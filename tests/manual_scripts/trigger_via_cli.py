import subprocess
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PROJECT_ID = "project-52b2fab8-15a1-4b66-9f3"
TOPIC_ID = "trigger-ingestion"

def trigger_workflow():
    message_data = {
        "bookId": "race-test-book-flow-1",
        "uid": "race-test-user-cli",
        "imageUrls": ["gs://intelligent-research-pipeline-bucket/test_books/buch1_cover_1.jpg"]
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
    trigger_workflow()
