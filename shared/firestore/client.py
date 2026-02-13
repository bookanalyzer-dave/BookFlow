from typing import Dict, Any, Optional
from google.cloud import firestore  # type: ignore

_db: Optional[firestore.Client] = None

def get_firestore_client() -> firestore.Client:
    """
    Lazily initializes and returns the Firestore client.
    """
    global _db
    if _db is None:
        _db = firestore.Client()
    return _db

def _get_user_books_collection(user_id: str):
    """
    Returns a reference to the user's specific 'books' subcollection.
    """
    db = get_firestore_client()
    return db.collection('users', user_id, 'books')

def add_book(user_id: str, book_data: Dict[str, Any]) -> str:
    """
    Adds a new book document to a user's subcollection in Firestore.
    """
    _, doc_ref = _get_user_books_collection(user_id).add(book_data)
    return doc_ref.id

def set_book(user_id: str, book_id: str, book_data: Dict[str, Any]):
    """
    Creates or overwrites a book document with a specific ID in a user's subcollection.
    """
    doc_ref = _get_user_books_collection(user_id).document(book_id)
    doc_ref.set(book_data)

# Define the valid status transitions for the book lifecycle
VALID_STATUS_TRANSITIONS = {
    "pending_analysis": ["ingesting", "failed", "condition_assessment_pending"],
    "uploaded": ["ingesting", "pending_analysis", "failed"],
    "ingesting": ["ingested", "needs_review", "analysis_failed"],
    "ingested": ["processing_condition", "condition_assessed", "condition_assessment_pending", "condition_failed", "failed"],
    "needs_review": ["ingesting", "failed"],
    "analysis_failed": ["ingesting", "failed", "condition_assessed"],
    "processing_condition": ["condition_assessed", "condition_failed", "ingested", "failed"],
    "condition_assessment_pending": ["processing_condition", "condition_assessed", "failed"],
    "condition_assessed": ["priced", "listed", "processing_condition", "failed", "pricing_failed"],
    "condition_failed": ["processing_condition", "ingested", "failed", "pricing_failed"],
    "pricing_failed": ["processing_condition", "ingested", "failed", "condition_failed", "condition_assessed"],
    "priced": ["listed", "condition_assessed", "failed", "pricing_failed"],
    "listed": ["sold", "delisted"],
    "failed": ["ingesting", "pending_analysis"]
}

def update_book(user_id: str, book_id: str, data: Dict[str, Any]):
    """
    Updates a book document with the provided data in a user's subcollection.
    Includes validation for status transitions.
    """
    doc_ref = _get_user_books_collection(user_id).document(book_id)

    if 'status' in data:
        current_doc = doc_ref.get()
        if current_doc.exists:
            current_status = current_doc.to_dict().get('status')
            new_status = data['status']
            
            if current_status and new_status != current_status:
                # Handle idempotency: if book is already 'priced', don't revert to 'condition_assessed'
                # but still allow updating other fields.
                if current_status == 'priced' and new_status == 'condition_assessed':
                    data['status'] = 'priced'
                    return doc_ref.update(data)

                # Relaxed validation: If status is unknown, allow any transition (fail open)
                # to prevent deadlocks during development/migrations.
                allowed_transitions = VALID_STATUS_TRANSITIONS.get(current_status)
                
                if allowed_transitions is not None and new_status not in allowed_transitions:
                    raise ValueError(
                        f"Invalid status transition from '{current_status}' to '{new_status}'. Allowed: {allowed_transitions}"
                    )
    
    doc_ref.update(data)

def get_book(user_id: str, book_id: str) -> Optional[Dict[str, Any]]:
    """
    Retrieves a book document by its ID from a user's subcollection.
    """
    doc_ref = _get_user_books_collection(user_id).document(book_id)
    doc = doc_ref.get()
    if doc.exists:
        return doc.to_dict()
    return None

def update_book_status(user_id: str, book_id: str, new_status: str):
    """
    Updates the status field of a specific book in a user's subcollection.
    """
    update_book(user_id, book_id, {'status': new_status})

def create_condition_assessment_request(user_id: str, book_id: str, payload: Dict[str, Any]):
    """
    Creates a new document in the condition_assessment_requests collection to trigger the agent.
    """
    db = get_firestore_client()
    request_ref = db.collection('users', user_id, 'condition_assessment_requests').document(book_id)
    request_ref.set(payload)

def delete_book(user_id: str, book_id: str):
    """
    Deletes a book document from a user's subcollection in Firestore.
    """
    doc_ref = _get_user_books_collection(user_id).document(book_id)
    doc_ref.delete()
