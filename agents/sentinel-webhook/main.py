import os
import logging
import json
from typing import Dict, Any, Tuple
from flask import Flask, request, jsonify
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

app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return "Sentinel Webhook is running.", 200


@app.route('/health', methods=['GET'])
def health_check():
    return "OK", 200


@app.route('/webhook/ebay', methods=['POST'])
def ebay_webhook() -> Tuple[Dict[str, Any], int]:
    """
    Handles incoming webhook notifications from eBay.
    """
    # Simulate validation by checking for a specific header
    if 'X-Ebay-Signature' not in request.headers:
        return jsonify({"status": "error", "message": "Unauthorized"}), 401  # type: ignore

    # Get the raw request data
    data = request.get_json()

    # Extract bookId and uid from the webhook payload (assuming a structure)
    # This part needs to be adapted to the actual eBay webhook payload structure
    book_id = data.get("itemId")
    uid = data.get("userId") # This is a placeholder, you need to find the user identifier in the payload

    if not book_id or not uid:
        return jsonify({"status": "error", "message": "Missing itemId or userId in payload"}), 400

    # Publish a structured message
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(os.environ['GCP_PROJECT'], 'sale-notification-received')
    
    message_data = {
        "bookId": book_id,
        "uid": uid,
        "platform": "ebay"
    }
    message_bytes = json.dumps(message_data).encode('utf-8')
    
    future = publisher.publish(topic_path, message_bytes)
    logger.info(f"Published message ID: {future.result()} for book {book_id}")

    return jsonify({"status": "success", "message": "Webhook received"}), 200  # type: ignore

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))