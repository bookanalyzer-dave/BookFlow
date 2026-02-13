"""
Price Research Orchestrator
Koordiniert Preis-Recherche über multiple Quellen und führt intelligente Fusion durch.
"""

import logging
import asyncio
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from google.cloud import firestore
from shared.apis.price_grounding import PriceGroundingClient, PriceData

logger = logging.getLogger(__name__)

class PriceResearchOrchestrator:
    """Orchestriert Multi-Source Price Research."""
    
    def __init__(self, db: firestore.Client, grounding_client: PriceGroundingClient):
        self.db = db
        self.grounding = grounding_client
    
    async def research_price(
        self, 
        isbn: str, 
        title: str, 
        book_id: str,
        uid: str
    ) -> Dict:
        """
        Hauptfunktion: Recherchiert Preise über alle Quellen.
        """
        # 1. Zusätzliche Metadaten aus Firestore abrufen für genaueres Grounding
        author = None
        publisher = None
        year = None
        edition = None
        
        try:
            # Nutze asyncio.to_thread für den synchronen Firestore-Aufruf
            book_doc = await asyncio.to_thread(
                lambda: self.db.collection('users').document(uid).collection('books').document(book_id).get()
            )
            
            if book_doc.exists:
                b_data = book_doc.to_dict()
                # Extrahiere Metadaten (Feldnamen basierend auf Ingestion Agent)
                authors_list = b_data.get('authors', [])
                if authors_list and isinstance(authors_list, list):
                    author = authors_list[0]
                elif b_data.get('author'):
                    author = b_data.get('author')
                
                publisher = b_data.get('publisher')
                year = b_data.get('publication_year')
                edition = b_data.get('edition')
                
                # Update isbn/title falls sie im PubSub fehlten aber im Doc sind
                if not isbn: isbn = b_data.get('isbn')
                if not title: title = b_data.get('title')
                
                logger.info(f"📖 Zusätzliche Metadaten für {book_id} geladen: Author={author}, Publisher={publisher}, Year={year}")
        except Exception as e:
            logger.warning(f"⚠️ Konnte Metadaten für Buch {book_id} nicht laden: {e}")

        # 2. Cache Check
        cached = await self._check_cache(isbn)
        if cached:
            logger.info(f"💾 Cache hit for ISBN {isbn}")
            return cached
        
        # 3. Query Gemini Grounding mit allen verfügbaren Metadaten
        result = await self.grounding.search_market_prices(
            isbn=isbn, 
            title=title,
            author=author,
            publisher=publisher,
            year=year,
            edition=edition
        )
        
        # 4. Simplify result for Orchestrator (Storage focus)
        # Orchestrator now only passes through raw data + Gemini analysis
        analyzed = {
            "offers_count": len(result.offers),
            "confidence_score": result.confidence_score,
            "ai_reasoning": result.reasoning,
            "sources": list(set(p.platform for p in result.offers)),
            "top_offers": [
                {
                    "seller": p.seller,
                    "price_eur": p.price_eur,
                    "condition": p.condition,
                    "platform": p.platform,
                    "url": p.url
                } for p in result.offers[:10]
            ]
        }
        
        # 5. Store in Firestore
        if result.offers:
            await self._store_results(isbn, book_id, uid, analyzed, result.offers)
        
        analyzed['cached'] = False
        return analyzed
    
    async def _check_cache(self, isbn: str, max_age_days: int = 7) -> Optional[Dict]:
        """Prüft Firestore Cache für market_data."""
        one_week_ago = datetime.utcnow() - timedelta(days=max_age_days)
        
        def _query_cache():
            return self.db.collection('market_data')\
                .where(filter=firestore.FieldFilter('isbn', '==', isbn))\
                .where(filter=firestore.FieldFilter('timestamp', '>', one_week_ago))\
                .order_by('timestamp', direction=firestore.Query.DESCENDING)\
                .limit(1)\
                .get()

        docs = await asyncio.to_thread(_query_cache)
            
        if docs:
            data = docs[0].to_dict()
            return {
                "offers_count": data.get("offers_count"),
                "confidence_score": data.get("confidence_score"),
                "ai_reasoning": data.get("ai_reasoning"),
                "sources": data.get("sources"),
                "top_offers": data.get("top_offers"),
                "cached": True
            }
        return None

    async def _store_results(self, isbn: str, book_id: str, uid: str, analyzed: Dict, all_offers: List[PriceData]):
        """Speichert die Ergebnisse in Firestore."""
        data = {
            "isbn": isbn,
            "bookId": book_id,
            "userId": uid,
            "offers_count": analyzed["offers_count"],
            "confidence_score": analyzed["confidence_score"],
            "ai_reasoning": analyzed.get("ai_reasoning"),
            "sources": analyzed["sources"],
            "top_offers": analyzed["top_offers"],
            "timestamp": firestore.SERVER_TIMESTAMP,
            "expires_at": datetime.utcnow() + timedelta(days=60) # TTL
        }
        
        await asyncio.to_thread(lambda: self.db.collection('market_data').add(data))
