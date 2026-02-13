import base64
import json
import os
import asyncio
import logging
import functions_framework
from cloudevents.http import CloudEvent
from shared.firestore.client import get_firestore_client
from shared.price_research.orchestrator import PriceResearchOrchestrator
from shared.apis.price_grounding import PriceGroundingClient

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize components once (outside the handler for warm starts)
db = get_firestore_client()

async def run_price_research(isbn: str, title: str, book_id: str, uid: str):
    """Async wrapper to ensure components are created in the correct loop."""
    grounding_client = PriceGroundingClient()
    price_orchestrator = PriceResearchOrchestrator(db, grounding_client)
    
    await price_orchestrator.research_price(
        isbn=isbn,
        title=title,
        book_id=book_id,
        uid=uid
    )

@functions_framework.cloud_event
def price_research_handler(cloud_event: CloudEvent) -> None:
    """
    Triggered by: projects/{project}/topics/price-research-requests
    """
    try:
        # Decode Pub/Sub message
        message_bytes = base64.b64decode(cloud_event.data["message"]["data"])
        message_data = json.loads(message_bytes.decode('utf-8'))
        
        book_id = message_data.get('bookId')
        uid = message_data.get('uid')
        isbn = message_data.get('isbn')
        title = message_data.get('title', '')
        
        if not all([book_id, uid, isbn]):
            logger.error(f"Missing required data in message: {message_data}")
            return

        logger.info(f"🚀 Starting background price research for ISBN {isbn} (Book: {book_id})")
        
        # Run async logic
        asyncio.run(run_price_research(
            isbn=isbn,
            title=title,
            book_id=book_id,
            uid=uid
        ))
        
        logger.info(f"✅ Background price research completed for ISBN {isbn}")
        
    except Exception as e:
        logger.error(f"❌ Error in price_research_handler: {str(e)}", exc_info=True)
