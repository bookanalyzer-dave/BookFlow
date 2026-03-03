"""
Price Research Orchestrator
Koordiniert Preis-Recherche über multiple Quellen und führt intelligente Fusion durch.
"""

import logging
import asyncio
import json
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from google.cloud import firestore
from google import genai
from google.genai import types

# Lokale Module (Shared)
from shared.apis.price_grounding import PriceGroundingClient, PriceData, MarketQueryResult
from shared.price_research.models import MarketAnalysis, CompetitorOffer, MarketStrategy, PriceRange

logger = logging.getLogger(__name__)

class PriceResearchOrchestrator:
    """Orchestriert Multi-Source Price Research und KI-gestützte Preisfindung."""
    
    def __init__(self, db: firestore.Client, grounding_client: PriceGroundingClient, project_id: str = None, location: str = "europe-west1"):
        import os
        self.db = db
        self.grounding = grounding_client
        self.project_id = project_id or os.environ.get("GCP_PROJECT", "project-52b2fab8-15a1-4b66-9f3")
        self.location = location
        
        # Initialisierung Gemini Client für Analyse (nicht Suche)
        self.analysis_client = genai.Client(
            vertexai=True,
            project=self.project_id,
            location=self.location
        )

    async def research_and_price(
        self, 
        isbn: str, 
        title: str, 
        book_id: str, 
        uid: str,
        condition_report: Dict = None  # Das KI-Gutachten vom Condition Assessor
    ) -> MarketAnalysis:
        """
        Hauptfunktion:
        1. Recherchiert echte Marktpreise (Grounding).
        2. Analysiert die Situation (Konkurrenz vs. eigener Zustand).
        3. Gibt den optimalen Preis zurück.
        """
        
        # 1. Metadaten laden (Autor, Verlag etc.)
        metadata = await self._fetch_book_metadata(uid, book_id)
        # Update isbn/title falls nötig
        if not isbn and metadata.get('isbn'): isbn = metadata.get('isbn')
        if not title and metadata.get('title'): title = metadata.get('title')

        # SECURITY CHECK: Haben wir überhaupt eine ISBN oder einen Titel?
        if not isbn and not title:
            logger.warning(f"⚠️ Weder ISBN noch Titel für {book_id} gefunden. Abbruch des Groundings.")
            return MarketAnalysis(
                recommended_price=0.0,
                min_price_limit=0.0,
                strategy_used=MarketStrategy.BALANCED,
                confidence=0.0,
                competitor_count=0,
                market_price_range=PriceRange(min_price=0, max_price=0, avg_price=0),
                reasoning="Weder ISBN noch Titel vorhanden. Automatische Preisrecherche nicht möglich.",
                internal_notes="Missing ISBN and Title"
            )

        # 2. Marktdaten abrufen (Cache first, dann API)
        market_data = await self._get_market_data(isbn, title, metadata)
        
        if not market_data or not market_data.offers:
            logger.warning(f"⚠️ Keine Marktangebote gefunden. Nutze Fallback-Strategie.")
            # Fallback: Wenn wir GAR NICHTS finden -> Konservativer Startpreis oder Manuelle Prüfung?
            return MarketAnalysis(
                recommended_price=0.0,
                min_price_limit=0.0,
                strategy_used=MarketStrategy.BALANCED,
                confidence=0.0,
                competitor_count=0,
                market_price_range=PriceRange(min_price=0, max_price=0, avg_price=0),
                reasoning="Keine Marktdaten gefunden. Manuelle Prüfung empfohlen.",
                internal_notes="Grounding lieferte keine Ergebnisse."
            )

        # 3. KI-Analyse: Zustand vs. Markt -> Preis
        analysis = await self._analyze_market_situation(market_data, condition_report, title, metadata)
        
        # 4. Speichern (Historie)
        await self._store_analysis_result(uid, book_id, analysis, market_data)

        return analysis

    async def _analyze_market_situation(
        self, 
        market_data: MarketQueryResult, 
        condition_report: Dict, 
        title: str,
        metadata: Dict
    ) -> MarketAnalysis:
        """
        Nutzt Gemini 2.5 Flash, um die rohen Marktdaten zu interpretieren.
        Entscheidet: Sind wir besser als die Konkurrenz? Können wir mehr verlangen?
        """
        
        # Daten für Prompt aufbereiten
        offers_summary = [
            f"- {o.seller} ({o.platform}): {o.price_eur}€ (Zustand: {o.condition})" 
            for o in market_data.offers[:10] # Top 10 reichen
        ]
        
        my_condition = condition_report.get('grade', 'Unbekannt') if condition_report else "Gut (Standard)"
        my_defects = condition_report.get('defects', []) if condition_report else []
        
        prompt = f"""
        Du bist ein professioneller Buchhändler-Algorithmus. Deine Aufgabe: Den optimalen Verkaufspreis ermitteln.

        BUCH:
        Titel: {title}
        Autor: {metadata.get('author', 'Unbekannt')}
        Verlag: {metadata.get('publisher', 'Unbekannt')} (Jahr: {metadata.get('year', 'Unbekannt')})

        UNSER EXEMPLAR:
        Zustand: {my_condition}
        Mängel: {", ".join(my_defects) if my_defects else "Keine nennenswerten Mängel."}

        MARKTLAGE (Konkurrenz):
        {chr(10).join(offers_summary)}

        DYNAMIK:
        - Wenn unser Zustand BESSER ist als der billigste Konkurrent -> Preis höher ansetzen.
        - Wenn unser Zustand SCHLECHTER ist -> Preis niedriger (oder Liquidations-Strategie).
        - Floor Price: Niemals unter 2.50€ (wegen Gebühren/Versand), außer es ist Schrott.
        
        AUFGABE:
        Erstelle eine JSON-Analyse gemäß Schema `MarketAnalysis`.
        """

        # Gemini Config für Structured Output (Pydantic!)
        config = types.GenerateContentConfig(
            temperature=0.1,
            response_mime_type="application/json",
            response_schema=MarketAnalysis # Hier kommt Pydantic ins Spiel!
        )

        try:
            response = await self.analysis_client.aio.models.generate_content(
                model="gemini-2.5-flash", # Schnell & Smart
                contents=prompt,
                config=config
            )
            
            text_result = response.text
            if "```json" in text_result:
                text_result = text_result.split("```json")[1].split("```")[0].strip()
            elif "```" in text_result:
                text_result = text_result.split("```")[1].split("```")[0].strip()
                
            data = json.loads(text_result)
            return MarketAnalysis(**data)

        except Exception as e:
            logger.error(f"❌ Fehler bei der KI-Preisanalyse: {e}", exc_info=True)
            return MarketAnalysis(
                recommended_price=0.0,
                min_price_limit=0.0,
                strategy_used=MarketStrategy.BALANCED,
                confidence=0.0,
                competitor_count=len(market_data.offers),
                market_price_range=PriceRange(min_price=0, max_price=0, avg_price=0),
                reasoning=f"KI-Fehler: {str(e)}",
                internal_notes="Fehler im LLM Call."
            )

    async def _get_market_data(self, isbn, title, metadata) -> Optional[MarketQueryResult]:
        return await self.grounding.search_market_prices(
            isbn=isbn,
            title=title,
            author=metadata.get('author'),
            publisher=metadata.get('publisher'),
            year=metadata.get('year'),
            edition=metadata.get('edition')
        )

    async def _fetch_book_metadata(self, uid, book_id) -> Dict:
        try:
            doc = await asyncio.to_thread(
                lambda: self.db.collection('users').document(uid).collection('books').document(book_id).get()
            )
            if doc.exists:
                d = doc.to_dict()
                authors = d.get('authors', [])
                first_author = None
                if isinstance(authors, list) and len(authors) > 0:
                    first_author = authors[0]
                elif isinstance(d.get('author'), str):
                    first_author = d.get('author')
                
                return {
                    'isbn': d.get('isbn'),
                    'title': d.get('title'),
                    'author': first_author or 'Unknown Author',
                    'publisher': d.get('publisher'),
                    'year': d.get('publication_year'),
                    'edition': d.get('edition')
                }
        except Exception as e:
            logger.warning(f"Fehler beim Laden der Metadaten: {e}")
        return {}

    async def _store_analysis_result(self, uid, book_id, analysis: MarketAnalysis, market_data: MarketQueryResult):
        try:
            data = analysis.model_dump()
            data['timestamp'] = datetime.utcnow().isoformat()
            data['raw_offers_count'] = len(market_data.offers)
            
            await asyncio.to_thread(
                lambda: self.db.collection('users').document(uid).collection('books').document(book_id).collection('price_history').add(data)
            )
            
            # AUCH ins Hauptdokument schreiben, damit das Frontend es sofort sieht
            await asyncio.to_thread(
                lambda: self.db.collection('users').document(uid).collection('books').document(book_id).update({
                    'status': 'priced',
                    'estimated_price': analysis.recommended_price,
                    'price_confidence': analysis.confidence,
                    'competitor_count': analysis.competitor_count
                })
            )
            
            logger.info(f"💾 Preisanalyse für {book_id} gespeichert (History & Main Doc).")
        except Exception as e:
            logger.error(f"Fehler beim Speichern der Analyse: {e}")
