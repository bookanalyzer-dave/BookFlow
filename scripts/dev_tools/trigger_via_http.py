import requests
import json
import base64

url = "https://ingestion-agent-53w2gh6mhq-ew.a.run.app"

data = {
    "bookId": "test-repro-HTTP-1",
    "uid": "test-user",
    "imageUrls": ["gs://project-52b2fab8-15a1-4b66-9f3-book-images/test_upload_repro_2.jpg"]
}

# Pub/Sub Envelope simulieren
envelope = {
    "message": {
        "data": base64.b64encode(json.dumps(data).encode("utf-8")).decode("utf-8")
    }
}

print(f"Sending POST request to {url}...")
try:
    response = requests.post(url, json=envelope, timeout=60)
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
except Exception as e:
    print(f"Error: {e}")
