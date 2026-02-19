import base64
import json
import os
import sys
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional

import functions_framework
from cloudevents.http import CloudEvent
from google.cloud import pubsub_v1

# PATH HACK: Ensure local imports work in Cloud Functions
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from shared.firestore.client import get_firestore_client, update_book, get_book
from shared.price_research.orchestrator import PriceResearchOrchestrator
from shared.apis.price_grounding import PriceGroundingClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Feature Flag & Defaults
PRICE_RESEARCH_ENABLED = os.environ.get("PRICE_RESEARCH_ENABLED", "true").lower() == "true"

# Global Singletons
db = None
publisher = None
orchestrator = None
PROJECT_ID = None

def init_globals():
    global db, publisher, orchestrator, PROJECT_ID
    
    if PROJECT_ID is None:
        PROJECT_ID = os.environ.get("GCP_PROJECT")
        if not PROJECT_ID:
             raise RuntimeError("GCP_PROJECT environment variable not set")

    if db is None:
        db = get_firestore_client()
        logger.info(f"✅ Firestore initialized for {PROJECT_ID}")

    if publisher is None:
        publisher = pubsub_v1.PublisherClient()
        
    if orchestrator is None:
        # Wir nutzen Gemini 2.5 Flash für schnelle Analyse, aber Pro für Suche (via Grounding Client Default)
        # Der Orchestrator managed das intern.
        grounding_client = PriceGroundingClient(project_id=PROJECT_ID)
        orchestrator = PriceResearchOrchestrator(
            db=db, 
            grounding_client=grounding_client,
            project_id=PROJECT_ID
        )
        logger.info("✅ PriceResearchOrchestrator initialized")

@functions_framework.cloud_event
def strategist_agent(cloud_event: CloudEvent) -> Any:
    """Entry Point für Cloud Function."""
    try:
        init_globals()
        
        # Decode PubSub Message
        if 'data' not in cloud_event.data["message"]:
             logger.error("No data in message")
             return 'Bad Request', 400
             
        pubsub_message = base64.b64decode(cloud_event.data["message"]["data"]).decode('utf-8')
        event_data = json.loads(pubsub_message)
        
        # Async Loop starten
        asyncio.run(process_pricing_request(event_data))
        return 'OK', 200
        
    except Exception as e:
        logger.critical(f"🔥 Critical Error in Strategist Agent: {e}", exc_info=True)
        return 'Internal Server Error', 500

async def process_pricing_request(message_data: Dict[str, Any]):
    """Verarbeitet eine einzelne Pricing-Anfrage."""
    book_id = message_data.get('bookId') or message_data.get('book_id')
    uid = message_data.get('uid') or message_data.get('user_id')
    
    if not book_id or not uid:
        logger.error(f"❌ Missing required fields: {message_data}")
        return

    logger.info(f"🚀 Starting Pricing for Book {book_id} (User: {uid})")

    # 1. ATOMIC LOCKING (Verhindert Race Conditions)
    # Wir nutzen eine Transaktion, um sicherzustellen, dass nicht 2x gepriced wird.
    try:
        if not await _acquire_lock(uid, book_id):
            logger.info(f"🔒 Book {book_id} is locked or already finished. Skipping.")
            return
    except Exception as e:
        logger.error(f"❌ Locking failed: {e}")
        return

    try:
        # 2. Condition Report laden (wichtig für den Orchestrator)
        condition_report = await _get_condition_data(uid, book_id)
        
        # 3. Metadaten (ISBN, Titel) aus der Message oder DB holen
        # Der Orchestrator holt sich Details selbst, aber wir geben ihm was wir haben.
        # Wir übergeben hier leere Strings, wenn nichts da ist, der Orchestrator lädt nach.
        isbn = message_data.get('isbn', '') 
        title = message_data.get('title', '')

        # 4. ORCHESTRATOR AUFRUFEN (Die Magie passiert hier)
        analysis = await orchestrator.research_and_price(
            isbn=isbn,
            title=title,
            book_id=book_id,
            uid=uid,
            condition_report=condition_report
        )
        
        # 5. ERGEBNIS SPEICHERN
        # Wir mappen das komplexe Analysis-Objekt auf einfache Felder für die UI
        update_payload = {
            'status': 'priced',
            'calculatedPrice': analysis.recommended_price,
            'price_analysis': analysis.model_dump(), # Volles Detail-Objekt
            'priced_at': datetime.utcnow().isoformat()
        }
        
        if condition_report:
            update_payload['ai_condition_grade'] = condition_report.get('grade')
        
        update_book(uid, book_id, update_payload)
        logger.info(f"✅ Pricing complete: {analysis.recommended_price} EUR (Strategy: {analysis.strategy_used})")
        
        # 6. Listing Request triggern (wenn Preis > 0)
        if analysis.recommended_price > 0:
            await _publish_listing_request(uid, book_id)
            
    except Exception as e:
        logger.error(f"❌ Pricing process failed: {e}", exc_info=True)
        update_book(uid, book_id, {'status': 'pricing_failed', 'error': str(e)})

async def _acquire_lock(uid: str, book_id: str) -> bool:
    """Setzt atomar den Status auf 'pricing', wenn noch nicht geschehen."""
    # Firestore Client aus global scope nutzen, aber wir brauchen 'google.cloud.firestore' für Transaction
    from google.cloud import firestore
    
    transaction = db.transaction()
    book_ref = db.collection('users').document(uid).collection('books').document(book_id)

    @firestore.transactional
    def set_lock_in_transaction(transaction, ref):
        snapshot = ref.get(transaction=transaction)
        if not snapshot.exists:
            return False # Buch gelöscht?
        
        data = snapshot.to_dict()
        current_status = data.get('status')
        
        # Idempotency Check
        if current_status in ['pricing', 'priced', 'listed']:
            return False
            
        transaction.update(ref, {
            'status': 'pricing',
            'pricing_started_at': datetime.utcnow().isoformat()
        })
        return True

    return set_lock_in_transaction(transaction, book_ref)

async def _get_condition_data(uid: str, book_id: str) -> Optional[Dict[str, Any]]:
    try:
        # Asynchron wäre besser, aber Client ist sync. Wir wrappen es nicht extra, da Cloud Run schnell ist.
        # Oder doch? Firestore sync call blockiert Event Loop.
        # Aber hier ist es okay, da wir eh nur einen Request pro Instanz/Thread haben (Concurreny 1 default).
        doc_ref = db.collection('users').document(uid).collection('condition_assessments').document(book_id)
        doc = doc_ref.get()
        return doc.to_dict() if doc.exists else None
    except Exception as e:
        logger.error(f"Error fetching condition: {e}")
        return None

async def _publish_listing_request(uid: str, book_id: str) -> None:
    try:
        topic_path = publisher.topic_path(PROJECT_ID, 'book-listing-requests')
        message = {'bookId': book_id, 'uid': uid, 'platform': 'ebay', 'timestamp': datetime.utcnow().timestamp()}
        future = publisher.publish(topic_path, data=json.dumps(message).encode('utf-8'))
        future.result() # Wait for publish
        logger.info(f"📤 Published listing request for {book_id}")
    except Exception as e:
        logger.error(f"Failed to publish listing: {e}")
