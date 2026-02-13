import base64
import json
import os
import logging
from typing import Dict, Any

import functions_framework

from shared.firestore.client import get_firestore_client
from google.cloud import pubsub_v1

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_environment() -> Dict[str, str]:
    """Validate required environment variables are set."""
    required_vars = {
        "GCP_PROJECT": os.environ.get("GCP_PROJECT"),
    }
    
    missing = [key for key, value in required_vars.items() if not value]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    logger.info(f"Environment validation passed for: {', '.join(required_vars.keys())}")
    return required_vars


# Validate environment on module load
env_vars = validate_environment()


@functions_framework.cloud_event
def sentinel_agent(cloud_event: Any) -> None:
    """
    This function is triggered by a message on the 'sale-notification-received' Pub/Sub topic.
    It updates the book's status in Firestore and publishes a message to delist the book.
    """
    message_data = base64.b64decode(cloud_event.data["message"]["data"]).decode('utf-8')

    try:
        data = json.loads(message_data)
        book_id = data.get("bookId")
        uid = data.get("uid")
        platform = data.get("platform")
        if not book_id or not platform or not uid:
            return
    except json.JSONDecodeError:
        return

    # Update book status using Multi-Tenancy structure
    db = get_firestore_client()
    book_ref = db.collection('users').document(uid).collection('books').document(book_id)
    book_ref.update({"status": "sold"})

    # Publish delist message
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(os.environ['GCP_PROJECT'], 'delist-book-everywhere')
    new_message = json.dumps({"bookId": book_id, "uid": uid}).encode('utf-8')
    future = publisher.publish(topic_path, new_message)
    future.result()
