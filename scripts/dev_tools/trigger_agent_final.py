import os
from google.cloud import pubsub_v1
import json

# Nutze den vorhandenen Key
key_path = "service-account-key.json"
if os.path.exists(key_path):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = key_path
    print(f"Using service account key: {key_path}")
else:
    print(f"Warning: {key_path} not found. Falling back to default credentials.")

project_id = "project-52b2fab8-15a1-4b66-9f3"
topic_id = "trigger-ingestion"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_id)

data = {
    "bookId": "test-repro-FINAL-SUCCESS",
    "uid": "test-user",
    "imageUrls": ["gs://project-52b2fab8-15a1-4b66-9f3-book-images/test_upload_repro_2.jpg"]
}

message_json = json.dumps(data)
message_bytes = message_json.encode("utf-8")

print(f"Publishing to {topic_path}...")
try:
    future = publisher.publish(topic_path, data=message_bytes)
    print(f"Published message ID: {future.result()}")
except Exception as e:
    print(f"Error publishing message: {e}")
