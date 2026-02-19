import requests
import json
import os
import time
import random
import string

# --- CONFIG ---
PROJECT_ID = "project-52b2fab8-15a1-4b66-9f3"
API_KEY = "AIzaSyDzvdbml1lwiO2Bs0nqDSBF3VqjA4Ciimc"  # Aus dem JS extrahiert
BACKEND_URL = "https://dashboard-backend-563616472394.europe-west1.run.app"
TEST_FILES = [
    "source/test_books/Testbuch1_Foto1.jpg",  # Cover
    "source/test_books/Testbuch1_Foto2.jpg",  # Back
    "source/test_books/Testbuch1_Foto3.jpg"   # Impressum
]

def log(msg):
    print(f"[HARALD] {msg}")

def generate_user():
    suffix = "".join(random.choices(string.ascii_lowercase + string.digits, k=6))
    email = f"agent.harald.{suffix}@example.com"
    password = "HaraldsSuperSecretPassword123!"
    return email, password

def register_user(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    resp = requests.post(url, json=payload)
    if resp.status_code != 200:
        log(f"Registration failed: {resp.text}")
        return None, None
    data = resp.json()
    log(f"Registered user: {email} (UID: {data['localId']})")
    return data['idToken'], data['localId']

def upload_file(token, filepath):
    filename = os.path.basename(filepath)
    content_type = "image/jpeg"
    
    # 1. Sign URL
    url = f"{BACKEND_URL}/api/books/upload"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"filename": filename, "contentType": content_type}
    
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code != 200:
        log(f"Failed to get signed URL for {filename}: {resp.text}")
        return None
    
    data = resp.json()
    signed_url = data['url']
    gcs_uri = data['gcs_uri']
    
    # 2. Upload to GCS
    with open(filepath, 'rb') as f:
        file_content = f.read()
    
    headers_put = {"Content-Type": content_type}
    resp_put = requests.put(signed_url, headers=headers_put, data=file_content)
    
    if resp_put.status_code != 200:
        log(f"Failed to upload {filename} to GCS: {resp_put.text}")
        return None
        
    log(f"Uploaded {filename} successfully -> {gcs_uri}")
    return gcs_uri

def start_processing(token, gcs_uris):
    url = f"{BACKEND_URL}/api/books/start-processing"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    payload = {"gcs_uris": gcs_uris}
    
    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code != 200:
        log(f"Failed to start processing: {resp.text}")
        return None
        
    data = resp.json()
    log(f"Processing started for Book ID: {data.get('bookId')}")
    return data.get('bookId')

def check_firestore_status(uid, book_id, token):
    # Using REST API for Firestore
    # Document path: projects/{projectId}/databases/(default)/documents/users/{uid}/books/{bookId}
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/users/{uid}/books/{book_id}"
    # Token auth works here too via Authorization header (Bear Token)
    headers = {"Authorization": f"Bearer {token}"}

    for i in range(30): # Wait up to 60 seconds
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            doc = resp.json()
            fields = doc.get("fields", {})
            status = fields.get("status", {}).get("stringValue", "unknown")
            log(f"Poll {i+1}: Status = {status}")
            
            if status == "ingested":
                title = fields.get("title", {}).get("stringValue", "N/A")
                log(f"SUCCESS! Book ingested. Title: {title}")
                return True
            if status in ["failed", "analysis_failed"]:
                error = fields.get("error", {}).get("stringValue", "Unknown error")
                log(f"FAILURE! Analysis failed: {error}")
                return False
        else:
            log(f"Poll {i+1}: Failed to fetch document: {resp.status_code}")
            
        time.sleep(2)
        
    log("Timeout waiting for result.")
    return False

def main():
    log("Starting simulation...")
    
    # 1. Register
    email, password = generate_user()
    token, uid = register_user(email, password)
    if not token: return
    
    # 2. Upload Files
    gcs_uris = []
    for f in TEST_FILES:
        if os.path.exists(f):
            uri = upload_file(token, f)
            if uri: gcs_uris.append(uri)
        else:
            log(f"File not found: {f}")
            
    if not gcs_uris:
        log("No files uploaded. Aborting.")
        return

    # 3. Start Processing
    book_id = start_processing(token, gcs_uris)
    if not book_id: return
    
    # 4. Wait for Result
    check_firestore_status(uid, book_id, token)

if __name__ == "__main__":
    main()
