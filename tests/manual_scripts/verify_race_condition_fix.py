import os
import json
import time
import logging
from google.cloud import pubsub_v1
from google.cloud import firestore
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ID = "project-52b2fab8-15a1-4b66-9f3"
TOPIC_ID = "trigger-condition-assessment"
USER_ID = "race_condition_test_user"
BOOK_ID = f"test_book_{int(time.time())}"

def setup_test_data():
    """Creates a test book document in Firestore."""
    db = firestore.Client(project=PROJECT_ID)
    
    # Book data
    book_data = {
        "title": "Race Condition Test Book",
        "author": "Test Author",
        "status": "ingested",
        "imageUrls": [
            "gs://intelligent-research-pipeline-bucket/test_books/buch1_cover_1.jpg",
            "gs://intelligent-research-pipeline-bucket/test_books/buch1_back_1.jpg"
        ],
        "userId": USER_ID,
        "createdAt": datetime.utcnow().isoformat()
    }
    
    # Create document
    doc_ref = db.collection('users').document(USER_ID).collection('books').document(BOOK_ID)
    doc_ref.set(book_data)
    logger.info(f"✅ Created test book: users/{USER_ID}/books/{BOOK_ID}")
    return book_data

def trigger_workflow():
    """Publishes a message to start the workflow."""
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)
    
    message_data = {
        "book_id": BOOK_ID,
        "user_id": USER_ID,
        "image_urls": [
            "gs://intelligent-research-pipeline-bucket/test_books/buch1_cover_1.jpg",
            "gs://intelligent-research-pipeline-bucket/test_books/buch1_back_1.jpg"
        ]
    }
    
    data = json.dumps(message_data).encode("utf-8")
    
    future = publisher.publish(topic_path, data)
    message_id = future.result()
    
    logger.info(f"✅ Published message to {topic_path} (Message ID: {message_id})")
    logger.info(f"Payload: {json.dumps(message_data, indent=2)}")

def main():
    # Set credentials if available (assuming running in environment with key)
    if os.path.exists("service-account-key.json"):
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "service-account-key.json"
    
    logger.info("🚀 Starting Race Condition Fix Verification")
    
    try:
        setup_test_data()
        trigger_workflow()
        
        logger.info("\n⏳ Workflow triggered. Now wait for agents to process...")
        logger.info(f"Test Book ID: {BOOK_ID}")
        logger.info(f"Test User ID: {USER_ID}")
        
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")

if __name__ == "__main__":
    main()

