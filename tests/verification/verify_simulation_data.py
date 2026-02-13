import os
import sys
from google.cloud.firestore import Query
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))

from shared.firestore.client import get_firestore_client

def setup_credentials():
    """Sets up Google Application Credentials."""
    # Try to find service-account-key.json in various locations relative to this script
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    
    possible_paths = [
        os.path.join(base_dir, 'service-account-key.json'),
        os.path.join(base_dir, 'secrets', 'service-account-key.json'),
        os.path.join(base_dir, '..', 'service-account-key.json'),
    ]

    found = False
    for path in possible_paths:
        if os.path.exists(path):
            print(f"Setting GOOGLE_APPLICATION_CREDENTIALS to: {path}")
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = path
            found = True
            break
            
    if not found:
        print("Service account key not found in common locations, using default credentials")

def verify_data():
    setup_credentials()
    db = get_firestore_client()
    
    print("Searching for recent simulation users...")
    
    # 1. Find users with email ending in @simulation.com
    # Since we can't query auth users easily without the Auth SDK (and listing all),
    # we might check the 'users' collection if user profiles are stored there.
    # Alternatively, we can assume the user created a book, so we check users who have books.
    # But filtering collections by subcollection properties is hard.
    
    # Let's try to query the top-level collection 'users' if it exists.
    # The app seems to use 'users/{uid}/books'.
    
    # If we can't find the user easily, we can look for *any* book created recently across the system?
    # No, Firestore doesn't support collection group queries easily without indexes on specific fields across all.
    # But we can try a Collection Group Query on 'books'.
    
    print("Performing Collection Group Query on 'books' for recent entries...")
    
    # Look for books created in the last 1 hour
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    
    # Note: 'created_at' is a string ISO format in the code I saw: datetime.datetime.utcnow().isoformat()
    # String comparison works for ISO format.
    cutoff_iso = one_hour_ago.isoformat()
    
    books_query = db.collection_group('books').where('created_at', '>=', cutoff_iso).order_by('created_at', direction=Query.DESCENDING).limit(5)
    
    try:
        docs = list(books_query.stream())
    except Exception as e:
        print(f"Error querying books: {e}")
        print("Tip: You might need a composite index for this query. Check the error message.")
        return

    if not docs:
        print("No books found created in the last hour.")
        return

    print(f"Found {len(docs)} recent books.")
    
    target_book = None
    
    for doc in docs:
        data = doc.to_dict()
        user_id = data.get('userId')
        title = data.get('title', 'Unknown Title')
        print(f"Checking book {doc.id} (User: {user_id}, Title: {title})...")
        
        # We prefer a book from a simulation user if we can identify it.
        # But we don't have user email here usually.
        # However, the test uses a specific user email pattern.
        # If we can't verify email, we'll take the most recent one.
        target_book = (doc.id, data)
        break # Just take the first one (most recent)
        
    if not target_book:
        print("No suitable book found.")
        return

    book_id, book_data = target_book
    print(f"\n--- Verifying Data for Book: {book_id} ---")
    
    # Check Book Data (Title, Author, etc.)
    # In the code, 'title' is at top level.
    # The requirement says "book_data (Title, Author, etc.)".
    # The ingestion agent might structure it differently, or keep it top level.
    # Let's check for key fields.
    print("\n1. Book Data:")
    required_book_fields = ['title', 'author', 'isbn'] # Common fields
    found_book_data = {k: book_data.get(k) for k in required_book_fields if k in book_data}
    print(f"   Found: {found_book_data}")
    
    if found_book_data:
        print("   [PASS] Book data present.")
    else:
        print("   [FAIL] Book data missing or incomplete.")

    # Check Condition Data
    # Code uses 'ai_condition_grade' or 'grade' in condition assessment.
    # The verification requirement says: "condition_data (Defects, Grade)"
    # This might be in a separate collection 'condition_assessments' or merged?
    # The code update_book(..., {'ai_condition_grade': ...}) suggests it's merged or at least referenced.
    # But let's checks the subcollection 'condition_assessments' too if needed.
    
    print("\n2. Condition Data:")
    condition_grade = book_data.get('ai_condition_grade')
    print(f"   Top-level Grade: {condition_grade}")
    
    # Also check the condition assessment document
    user_id = book_data.get('userId')
    if user_id:
        condition_ref = db.collection('users').document(user_id).collection('condition_assessments').document(book_id)
        condition_doc = condition_ref.get()
        if condition_doc.exists:
            cond_data = condition_doc.to_dict()
            print(f"   Detailed Assessment: {cond_data}")
            if cond_data.get('grade') or cond_data.get('defects'):
                 print("   [PASS] Condition data present in subcollection.")
            else:
                 print("   [WARN] Condition document exists but might be empty.")
        else:
            print("   [FAIL] Condition assessment document not found.")
    else:
        print("   [FAIL] Cannot check detailed condition (no userId).")

    # Check Price Data
    # Requirement: "price_data (Market price, etc.)"
    # Usually 'price' or 'estimated_price' or 'price_range'.
    print("\n3. Price Data:")
    price = book_data.get('price')
    min_price = book_data.get('min_price')
    max_price = book_data.get('max_price')
    
    print(f"   Price: {price}, Min: {min_price}, Max: {max_price}")
    
    if price or (min_price and max_price):
        print("   [PASS] Price data present.")
    else:
        print("   [FAIL] Price data missing.")

if __name__ == "__main__":
    verify_data()
