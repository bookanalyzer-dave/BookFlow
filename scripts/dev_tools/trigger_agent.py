from google.cloud import pubsub_v1
import json
import os

# WICHTIG: Quota-Projekt auf das aktuelle Projekt setzen, um "Project has been deleted" Fehler zu vermeiden
os.environ["GOOGLE_CLOUD_PROJECT"] = "project-52b2fab8-15a1-4b66-9f3"

project_id = "project-52b2fab8-15a1-4b66-9f3"
topic_id = "trigger-ingestion"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_id)

data = {
    "bookId": "test-repro-FINAL-2",
    "uid": "test-user",
    "imageUrls": ["gs://project-52b2fab8-15a1-4b66-9f3-book-images/test_upload_repro_2.jpg"]
}

message_json = json.dumps(data)
message_bytes = message_json.encode("utf-8")

print(f"Publishing to {topic_path}...")
future = publisher.publish(topic_path, data=message_bytes)
print(f"Published message ID: {future.result()}")
