import requests
import time
import json

API_KEY = "AIzaSyDzvdbml1lwiO2Bs0nqDSBF3VqjA4Ciimc"
PROJECT_ID = "project-52b2fab8-15a1-4b66-9f3"

def login(email, password):
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={API_KEY}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    resp = requests.post(url, json=payload)
    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return None
    return resp.json()['idToken']

def check_status(token, uid, book_id):
    url = f"https://firestore.googleapis.com/v1/projects/{PROJECT_ID}/databases/(default)/documents/users/{uid}/books/{book_id}"
    headers = {"Authorization": f"Bearer {token}"}
    
    print(f"Checking book {book_id} for user {uid}...")
    
    for i in range(20):
        resp = requests.get(url, headers=headers)
        if resp.status_code == 200:
            doc = resp.json()
            fields = doc.get("fields", {})
            status = fields.get("status", {}).get("stringValue", "unknown")
            print(f"Poll {i+1}: Status = {status}")
            
            if status == "ingested":
                title = fields.get("title", {}).get("stringValue", "N/A")
                authors_val = fields.get("authors", {})
                # Authors structure depends on array or string
                print(f"SUCCESS! Book ingested. Title: {title}")
                print(json.dumps(fields, indent=2))
                return
            elif status in ["failed", "analysis_failed"]:
                error = fields.get("error", {}).get("stringValue", "Unknown error")
                print(f"FAILURE! Analysis failed: {error}")
                return
        else:
            print(f"Poll {i+1}: Error {resp.status_code} - {resp.text}")
            
        time.sleep(3)

def main():
    email = "agent.harald.kdz47g@example.com" # User from previous run
    password = "HaraldsSuperSecretPassword123!"
    uid = "1cdYIFM7Sbh7BLqXuuB0FChoWgQ2"       # UID from previous run
    book_id = "Testbuch1_Foto1_1770586035"     # Book ID from previous run
    
    token = login(email, password)
    if token:
        check_status(token, uid, book_id)

if __name__ == "__main__":
    main()
