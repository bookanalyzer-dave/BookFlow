import os
import json
import base64
import asyncio
import logging
import functions_framework
from typing import Any
from google.cloud import pubsub_v1
from google.cloud import firestore

# Imports aus der Shared Library
from shared.simplified_ingestion.models import BookIngestionRequest
from shared.simplified_ingestion.core import ingest_book_with_retry, IngestionException
from shared.simplified_ingestion.config import IngestionConfig

# Konfiguriere Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# VERSION MARKER
logger.info("**************************************************")
logger.info("VERSION MARKER: v3.1.0-ROBUSTNESS-FIXES")
logger.info("**************************************************")

def get_required_env(key: str) -> str:
    """Holt eine Umgebungsvariable oder wirft einen Fehler, wenn sie fehlt."""
    value = os.environ.get(key)
    if not value:
        raise RuntimeError(f"CRITICAL: Environment variable '{key}' is not set.")
    return value

# Function to get Project ID from environment (Strict Mode)
def get_project_id():
    """Returns the Project ID from environment variables."""
    return get_required_env("GCP_PROJECT")

# Konfiguration mit aktiviertem Grounding
# Nutze Env Var GEMINI_MODEL falls vorhanden, sonst Default aus Config (gemini-2.5-pro)
model_env = os.environ.get("GEMINI_MODEL")
if model_env:
    INGESTION_CONFIG = IngestionConfig(enable_grounding=True, model=model_env)
else:
    INGESTION_CONFIG = IngestionConfig(enable_grounding=True)

# Firestore Client Initialisierung (dynamisch)
try:
    project_id = get_project_id()
    db = firestore.Client(project=project_id)
except Exception as e:
    logger.critical(f"Failed to initialize Firestore client: {e}")
    raise

def get_firestore_client():
    return db

# Initialize Pub/Sub client
try:
    project_id = get_project_id()
    publisher = pubsub_v1.PublisherClient()
    # FIX: Korrektes Topic für Condition Assessor (gemäß Eventarc Trigger)
    condition_topic_path = publisher.topic_path(project_id, "condition-assessment-jobs")
    # NEU: Topic für Price Research
    price_topic_path = publisher.topic_path(project_id, "price-research-requests")
    logger.info(f"Pub/Sub publisher initialized.")
    logger.info(f"Condition Topic: {condition_topic_path}")
    logger.info(f"Price Topic: {price_topic_path}")
except Exception as e:
    logger.critical(f"Failed to initialize Pub/Sub publisher: {e}", exc_info=True)
    # Fail fast: Ohne Pub/Sub können wir nicht arbeiten
    raise

@functions_framework.cloud_event
def ingestion_analysis_agent(cloud_event: Any):
    """Wrapper für die Cloud Function."""
    try:
        asyncio.run(_async_ingestion_analysis_agent(cloud_event))
        return "OK", 200
    except (json.JSONDecodeError, ValueError, KeyError) as e:
        # Permanente Fehler (Datenformat falsch, Felder fehlen) -> Kein Retry
        logger.error(f"Permanent Error (No Retry): {e}", exc_info=True)
        return "Bad Request", 200
    except Exception as e:
        # Transiente Fehler (DB Timeout, API Fehler) -> Retry (500)
        logger.critical(f"Transient Error (Will Retry): {e}", exc_info=True)
        # Exception werfen, damit Cloud Functions 500 sendet und Pub/Sub retried
        raise e


async def _async_ingestion_analysis_agent(cloud_event: Any) -> None:
    try:
        message_data = base64.b64decode(cloud_event.data["message"]["data"]).decode('utf-8')
        message_json = json.loads(message_data)
    except Exception as e:
        logger.error(f"Invalid message format: {e}")
        # Wirft Fehler weiter an Wrapper für Entscheidung
        raise ValueError(f"Invalid message format: {e}")

    book_id = message_json.get('bookId')
    image_urls = message_json.get('imageUrls')
    uid = message_json.get('uid')

    if not all([book_id, image_urls, uid]) or not isinstance(image_urls, list) or len(image_urls) == 0:
        logger.error(f"Missing required fields or empty imageUrls in message: {message_json}")
        raise ValueError("Missing required fields or empty imageUrls")

    logger.info(f"📨 Received Pub/Sub message - bookId: {book_id}, uid: {uid}, images: {len(image_urls)}")
    logger.info(f"Processing book {book_id} for user {uid} with {len(image_urls)} images")
    book_ref = db.collection('users').document(uid).collection('books').document(book_id)

    @firestore.transactional
    def check_and_update_status(transaction):
        snapshot = book_ref.get(transaction=transaction)
        if snapshot.exists:
            status = snapshot.to_dict().get('status')
            logger.info(f"📄 Found existing document for {book_id} with status: {status}")
            # Nur bei finalen States überspringen - erlaubt Retry bei pending_analysis
            if status in ['ingested', 'needs_review', 'analysis_failed', 'condition_assessed']:
                logger.warning(f"Book {book_id} already finished ({status}). Skipping.")
                return False
            # Erlaubt Retry bei 'pending_analysis' oder 'ingesting'
        else:
            logger.warning(f"⚠️ Document {book_id} does NOT exist in Firestore! This should not happen.")
        
        transaction.set(book_ref, {'status': 'ingesting'}, merge=True)
        logger.info(f"✅ Updated status to 'ingesting' for {book_id}")
        return True

    transaction = db.transaction()
    should_process = check_and_update_status(transaction)

    if not should_process:
        return


    try:
        request = BookIngestionRequest(
            book_id=book_id,
            user_id=uid,
            image_urls=image_urls
        )
        
        # Aufruf der Shared Library Logik
        # Hier wird jetzt Search Grounding aktiv genutzt (via INGESTION_CONFIG)
        result = await ingest_book_with_retry(request, config=INGESTION_CONFIG)
        
        if result.book_data:
            final_data = {
                "status": result.get_firestore_status(),
                "title": result.book_data.title,
                "authors": result.book_data.authors,
                "isbn": result.book_data.isbn_13 or result.book_data.isbn_10,
                "publisher": result.book_data.publisher,
                "publication_year": result.book_data.publication_year,
                "edition": result.book_data.edition,
                "language": result.book_data.language,
                "page_count": result.book_data.page_count,
                "genre": result.book_data.genre,
                "categories": result.book_data.categories,
                "cover_url": result.book_data.cover_url,
                "description": result.book_data.description,
                "confidence_score": result.confidence,
                "sources_used": result.sources_used,
                "_metadata": {
                    "processing_time_ms": result.processing_time_ms,
                    "simplified_ingestion": True,
                    "grounding_metadata": result.grounding_metadata.model_dump() if result.grounding_metadata else None,
                    "library_version": "v3.0.0" 
                }
            }
            book_ref.update(final_data)
            logger.info(f"Simplified ingestion processed for book {book_id} with status {final_data['status']}")

            if publisher:
                # 1. Trigger Condition Assessment
                if condition_topic_path:
                    try:
                        payload = {"book_id": book_id, "user_id": uid, "image_urls": image_urls, "metadata": final_data}
                        data = json.dumps(payload).encode("utf-8")
                        publisher.publish(condition_topic_path, data)
                        logger.info(f"✅ Successfully published condition assessment job for book {book_id}")
                    except Exception as e:
                        logger.error(f"❌ Failed to trigger condition assessment for book {book_id}: {e}")
                
                # 2. Trigger Price Research (wenn ISBN vorhanden)
                isbn = final_data.get('isbn')
                if price_topic_path and isbn:
                    try:
                        payload = {"bookId": book_id, "uid": uid, "isbn": isbn, "title": final_data.get('title', '')}
                        data = json.dumps(payload).encode("utf-8")
                        publisher.publish(price_topic_path, data)
                        logger.info(f"✅ Successfully published price research job for book {book_id}")
                    except Exception as e:
                        logger.error(f"❌ Failed to trigger price research for book {book_id}: {e}")
            else:
                logger.error("❌ Pub/Sub publisher not initialized.")

        else:
            logger.warning(f"Ingestion for book {book_id} failed: Gemini returned no book data.")
            book_ref.update({
                'status': 'analysis_failed',
                'error_message': 'Gemini returned no book data.',
                'error_type': 'INGESTION_NO_DATA',
            })

    except IngestionException as e:
        logger.error(f"Simplified ingestion failed for book {book_id}: {e.error.error_message}")
        book_ref.update({
            'status': 'analysis_failed',
            'error_message': e.error.error_message,
            'error_type': e.error.error_type,
        })
    except Exception as e:
        logger.error(f"Unexpected error for book {book_id}: {e}", exc_info=True)
        book_ref.update({'status': 'analysis_failed', 'error_message': str(e)})
