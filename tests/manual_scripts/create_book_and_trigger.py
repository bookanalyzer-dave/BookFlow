import os
import time
import json
import logging
import subprocess
import requests
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = "project-52b2fab8-15a1-4b66-9f3"
TOPIC_ID = "trigger-condition-assessment"
USER_ID = "race-test-user-cli"
BOOK_ID = f"race-test-book-flow-{int(time.time())}"
TEST_IMAGE = f"gs://{PROJECT_ID}-book-images/test_upload_repro_1.jpg"

def get_access_token():
    try:
        token = subprocess.check_output(["gcloud", "auth", "print-access-token"], text=True, shell=True).strip()
        return token
    except Exception as e:
        logger.error(f"Failed to get access token: {e}")
        return None

def create_book_rest():
    token = get_access_token()
    if not token:
        return False
    
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/users/{USER_ID}/books?documentId={BOOK_ID}"
    
    payload = {
        "fields": {
            "title": {"stringValue": "Race Condition Test Book"},
            "status": {"stringValue": "ingested"},
            "userId": {"stringValue": USER_ID},
            "imageUrls": {
                "arrayValue": {
                    "values": [
                        {"stringValue": TEST_IMAGE}
                    ]
                }
            }
        }
    }
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            logger.info(f"✅ Created test book via REST: {BOOK_ID}")
            return True
        else:
            logger.error(f"❌ Failed to create book: {response.status_code} {response.text}")
            return False
    except Exception as e:
        logger.error(f"❌ REST API call failed: {e}")
        return False

def trigger_workflow():
    message_data = {
        "book_id": BOOK_ID,
        "user_id": USER_ID,
        "image_urls": [TEST_IMAGE]
    }
    
    json_str = json.dumps(message_data)
    
    cmd = [
        "gcloud", "pubsub", "topics", "publish", TOPIC_ID,
        f"--message={json_str}",
        f"--project={PROJECT_ID}"
    ]
    
    logger.info(f"Executing: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, shell=True)
        logger.info(f"Success: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error: {e.stderr}")

if __name__ == "__main__":
    if create_book_rest():
        time.sleep(2)
        trigger_workflow()
    else:
        logger.error("Skipping trigger due to setup failure.")
