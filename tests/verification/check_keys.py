import os
from google.cloud import firestore
from google.oauth2 import service_account

def check_key(key_path):
    print(f"Testing key: {key_path}")
    if not os.path.exists(key_path):
        print(f"  -> FAILURE: File not found at {key_path}")
        return False

    try:
        # Attempt to create credentials and client
        credentials = service_account.Credentials.from_service_account_file(key_path)
        db = firestore.Client(credentials=credentials)
        
        # Attempt a simple operation
        # Listing collections is a good read operation to test permissions
        collections = list(db.collections())
        print(f"  -> SUCCESS: Connected and listed {len(collections)} collections.")
        return True
    except Exception as e:
        print(f"  -> FAILURE: {str(e)}")
        return False

def main():
    keys_to_test = [
        "secrets/service-account-key.json",
        "secrets/sa-key-new.json",
        "secrets/project-key.json"
    ]
    
    working_keys = []
    
    print("--- Starting Credential Verification ---")
    for key in keys_to_test:
        if check_key(key):
            working_keys.append(key)
    
    print("\n--- Verification Summary ---")
    if working_keys:
        print(f"Working keys found: {working_keys}")
    else:
        print("No working keys found.")

if __name__ == "__main__":
    main()
