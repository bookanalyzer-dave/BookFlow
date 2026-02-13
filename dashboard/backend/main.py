import os
import datetime
from flask import Flask, jsonify, request, make_response
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
import firebase_admin
from firebase_admin import credentials, auth
from google.cloud import storage, pubsub_v1
import json
import requests
import google.auth
from google.auth.transport import requests as google_requests
import asyncio
import logging
import traceback

# Load environment variables
load_dotenv()

# --- CRITICAL BOOTSTRAP REPAIR ---
def bootstrap_env():
    """
    Repairs environment variables globally in os.environ before any clients are initialized.
    This fixes the persistent Pub/Sub topic path error caused by concatenated env vars.
    """
    critical_vars = ["GCP_PROJECT", "GCS_BUCKET_NAME", "VERTEX_AI_LOCATION", "GOOGLE_CLOUD_PROJECT", "GCP_PROJECT_ID"]
    for var in critical_vars:
        val = os.environ.get(var)
        if val:
            original = val
            # 1. Take first token if spaces are present
            # 2. Globally remove all quotes (handles '"proj" GCS=...' cases)
            # 3. Strip any remaining whitespace
            val = val.split()[0].replace('"', '').replace("'", "").strip()
            
            # Special case for doubled project IDs: "proj-123proj-123"
            if len(val) > 10 and len(val) % 2 == 0:
                half = len(val) // 2
                if val[:half] == val[half:]:
                    val = val[:half]

            if val != original:
                # Use print because logger might not be configured yet or using broken env vars
                print(f"🔧 BOOTSTRAP REPAIR: {var}='{original}' -> '{val}'")
                os.environ[var] = val
            
            # Ensure synchronization across common GCP env var names
            if var == "GCP_PROJECT":
                os.environ["GOOGLE_CLOUD_PROJECT"] = val
                os.environ["GCP_PROJECT_ID"] = val

# Execute repair immediately
bootstrap_env()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from shared.firestore.client import update_book, get_book, set_book, create_condition_assessment_request, delete_book

app = Flask(__name__)

# Configure CORS
# Configure CORS globally with explicit origins for the frontend
CORS(app, resources={
    r"/*": {
        "origins": [
            "https://project-52b2fab8-15a1-4b66-9f3.web.app",
            "https://project-52b2fab8-15a1-4b66-9f3.firebaseapp.com",
            "http://localhost:5173"
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Requested-With", "Accept"],
        "supports_credentials": True
    }
})

# CORS handles everything automatically if configured correctly.
# Remove manual header injection that causes duplicates.

# @app.before_request
# def handle_preflight():
#     if request.method == "OPTIONS":
#         response = jsonify({'status': 'ok'})
#         response.headers.add('Access-Control-Allow-Origin', '*')
#         response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
#         response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
#         return response, 200

# Initialize Rate Limiter for Alpha Launch
# 100 requests per minute per user (as per requirements)
# OPTIONS requests are exempted to prevent CORS preflight failures
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["100 per minute"],
    default_limits_exempt_when=lambda: request.method == "OPTIONS",
    storage_uri="memory://",  # Use Redis in production
    strategy="fixed-window"
)

# Configure rate limit exceeded handler
@app.errorhandler(429)
def ratelimit_handler(e):
    """Handle rate limit exceeded errors"""
    logger.warning(f"Rate limit exceeded: {request.remote_addr} - {request.path}")
    return jsonify({
        "error": "Too Many Requests",
        "message": "Rate limit exceeded. Please try again later.",
        "retry_after": e.description
    }), 429

# Initialize Credentials Logic
# Supports Service Account Key file (legacy/local) AND Application Default Credentials (ADC)
service_account_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'service-account-key.json')

# Check if GOOGLE_APPLICATION_CREDENTIALS is explicitly set
if os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
    print(f"✅ GOOGLE_APPLICATION_CREDENTIALS explicitly set to: {os.environ['GOOGLE_APPLICATION_CREDENTIALS']}")
# Fallback: If not set, but local key file exists, inject it (Backward Compatibility)
elif os.path.exists(service_account_path):
    print(f"ℹ️  Injecting local service account key into environment: {service_account_path}")
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = service_account_path
else:
    print("ℹ️  No explicit key file found. Relying on Standard ADC (gcloud auth application-default login) or Metadata Server.")

# Initialize Firebase Admin SDK
try:
    # ApplicationDefault automatically picks up GOOGLE_APPLICATION_CREDENTIALS or ADC
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred)
    print("✅ Firebase Admin SDK initialized with ApplicationDefault credentials")
except Exception as e:
    print(f"❌ Error initializing Firebase Admin SDK: {e}")

# Initialize Google Cloud clients
try:
    # Client() automatically picks up GOOGLE_APPLICATION_CREDENTIALS or ADC
    storage_client = storage.Client()
    publisher = pubsub_v1.PublisherClient()
    print("✅ Google Cloud Clients (Storage, PubSub) initialized")
except Exception as e:
    print(f"❌ Error initializing Google Cloud clients: {e}")

# Get critical variables (already sanitized by bootstrap_env)
project_id = os.environ.get("GCP_PROJECT")
bucket_name = os.environ.get("GCS_BUCKET_NAME")
vertex_location = os.environ.get("VERTEX_AI_LOCATION")

logger.info(f"✅ Loaded GCP_PROJECT: '{project_id}'")
logger.info(f"✅ Loaded GCS_BUCKET_NAME: '{bucket_name}'")
logger.info(f"✅ Loaded VERTEX_AI_LOCATION: '{vertex_location}'")

if not project_id:
    raise ValueError("GCP_PROJECT environment variable not set or invalid.")
if not bucket_name:
    raise ValueError("GCS_BUCKET_NAME environment variable not set or invalid.")

topic_name = "ingestion-requests"
topic_path = publisher.topic_path(project_id, topic_name)

logger.info(f"🔧 Generated topic_path: '{topic_path}'")

# Condition Assessment Topic
condition_assessment_topic = "trigger-condition-assessment"
condition_assessment_topic_path = publisher.topic_path(project_id, condition_assessment_topic)

bucket = storage_client.bucket(bucket_name)

# LLM Manager Removal: No longer initializing UserLLMManager

def _get_uid_from_token():
    """Helper to extract UID from Authorization header."""
    id_token = request.headers.get('Authorization')
    if not id_token or 'Bearer ' not in id_token:
        return None, (jsonify({"error": "Authorization token is required"}), 401)
    try:
        token_value = id_token.split('Bearer ')[1]
        
        # Try token verification with retry for clock skew issues
        max_retries = 3
        for attempt in range(max_retries):
            try:
                decoded_token = auth.verify_id_token(token_value)
                return decoded_token['uid'], None
            except Exception as verify_error:
                if "used too early" in str(verify_error) and attempt < max_retries - 1:
                    import time
                    time.sleep(1)
                    continue
                else:
                    raise verify_error
                    
    except Exception as e:
        return None, (jsonify({"error": "Invalid or expired token", "details": str(e)}), 401)

@app.route('/api/books/upload', methods=['POST', 'OPTIONS'])
@limiter.limit("20 per minute")  # Stricter limit for uploads
def upload_book():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "https://project-52b2fab8-15a1-4b66-9f3.web.app")
        response.headers.add('Access-Control-Allow-Headers', "Content-Type, Authorization")
        response.headers.add('Access-Control-Allow-Methods', "GET, POST, PUT, DELETE, OPTIONS")
        response.headers.add('Access-Control-Allow-Credentials', 'true')
        return response

    uid, error_response = _get_uid_from_token()
    if error_response:
        return error_response

    file_name = request.json.get('filename')
    if not file_name:
        return jsonify({"error": "filename is required"}), 400

    blob_path = f"uploads/{uid}/{secure_filename(file_name)}"
    blob = bucket.blob(blob_path)

    # LOGGING: Diagnose Content-Type issues
    client_content_type = request.json.get('contentType')
    final_content_type = client_content_type if client_content_type is not None else 'application/octet-stream'
    logger.info(f"Upload request for {file_name}: client_content_type='{client_content_type}', final_content_type='{final_content_type}'")

    try:
        # Get credentials for signing (works in Cloud Run/GKE/Local)
        credentials, _ = google.auth.default()
        
        # Ensure we have a token if we need to delegate to IAM
        if hasattr(credentials, "refresh") and not credentials.token:
             request_auth = google_requests.Request()
             credentials.refresh(request_auth)

        if hasattr(credentials, "service_account_email") and credentials.service_account_email:
             # Cloud Environment (Cloud Run, etc.) - Delegate to IAM
             # Requires role: roles/iam.serviceAccountTokenCreator
             logger.info(f"Generating signed URL using service account: {credentials.service_account_email}")
             signed_url = blob.generate_signed_url(
                version="v4",
                expiration=datetime.timedelta(minutes=15),
                method="PUT",
                content_type=request.json.get('contentType', 'application/octet-stream'),
                service_account_email=credentials.service_account_email,
                access_token=credentials.token
            )
        else:
             # Local/Key-based Environment - Sign locally
             logger.info("Generating signed URL using local/default credentials")
             signed_url = blob.generate_signed_url(
                version="v4",
                expiration=datetime.timedelta(minutes=15),
                method="PUT",
                content_type=request.json.get('contentType', 'application/octet-stream'),
            )
    except Exception as e:
        logger.error(f"Error generating signed URL with specific credentials: {str(e)}")
        # Fallback: Try generating without explicit credentials (relies on client defaults)
        try:
            signed_url = blob.generate_signed_url(
                version="v4",
                expiration=datetime.timedelta(minutes=15),
                method="PUT",
                content_type=request.json.get('contentType', 'application/octet-stream'),
            )
        except Exception as e2:
             logger.error(f"Fatal error generating signed URL: {str(e2)}")
             return jsonify({"error": "Failed to generate upload URL"}), 500

    return jsonify({"url": signed_url, "gcs_uri": f"gs://{bucket_name}/{blob_path}"})

@app.route('/api/test-log', methods=['GET', 'POST'])
def test_log():
    logger.info("Test Log Route called!")
    return jsonify({"message": "Log written"}), 200

@app.route('/api/books/start-processing', methods=['POST'])
# @limiter.limit("50 per minute")  # Temporarily disabled for debugging
def start_processing():
    print("PRINT: Start processing called!") # Direct print to stdout
    logger.info(f"Start processing called. Headers: {dict(request.headers)}")
    
    uid, error_response = _get_uid_from_token()
    if error_response:
        logger.error(f"Auth failed: {error_response}")
        return error_response

    try:
        data = request.get_json(force=True, silent=True)
        logger.info(f"Request payload: {data}")
        
        if not data:
            logger.error("No JSON data received")
            return jsonify({"error": "No JSON data provided"}), 400
            
        gcs_uris = data.get('gcs_uris')
    except Exception as e:
        logger.error(f"Error parsing JSON: {e}")
        return jsonify({"error": "Invalid JSON format"}), 400

    if not gcs_uris or not isinstance(gcs_uris, list) or len(gcs_uris) == 0:
        logger.error(f"Invalid gcs_uris: {gcs_uris}")
        return jsonify({"error": "gcs_uris must be a non-empty list of strings"}), 400

    # Use the filename from the first URI and a timestamp to create a unique book ID
    first_gcs_uri = gcs_uris[0]
    filename = first_gcs_uri.split('/')[-1]
    base_book_id, _ = os.path.splitext(filename)
    # Add timestamp to ensure uniqueness for each upload session
    book_id = f"{base_book_id}_{int(datetime.datetime.utcnow().timestamp())}"
    
    logger.info(f"🆔 Created unique book_id: {book_id} (base: {base_book_id})")

    new_book = {
        "status": "pending_analysis",
        "imageUrls": gcs_uris,
        "userId": uid,
        "title": filename,
        "created_at": datetime.datetime.utcnow().isoformat()
    }
    set_book(uid, book_id, new_book)
    logger.info(f"✅ Created Firestore document for book_id: {book_id} with status: pending_analysis")

    # Send all fields required by the ingestion agent (uid, bookId, imageUrls)
    message_data = json.dumps({
        "bookId": book_id,
        "uid": uid,
        "imageUrls": gcs_uris
    }).encode('utf-8')
    logger.info(f"📤 Publishing to Pub/Sub with bookId: {book_id}")
    logger.info(f"📍 Topic path: {topic_path}")
    logger.info(f"📦 Message size: {len(message_data)} bytes")
    try:
        future = publisher.publish(topic_path, data=message_data)
        logger.info(f"⏳ Waiting for Pub/Sub confirmation...")
        message_id = future.result(timeout=10.0)  # 10 second timeout
        logger.info(f"✅ Published message with ID: {message_id}")
    except Exception as e:
        logger.error(f"❌ Pub/Sub publish failed: {type(e).__name__}: {str(e)}")
        logger.error(f"📋 Full traceback:\n{traceback.format_exc()}")
        logger.error(f"🔍 Topic path was: {topic_path}")
        logger.error(f"🔍 Project ID: {project_id}")
        return jsonify({"error": "Failed to publish message", "details": str(e)}), 500

    return jsonify({"message": "Processing started", "bookId": book_id}), 202

@app.route('/api/books/<book_id>', methods=['DELETE'], strict_slashes=False)
def delete_book_endpoint(book_id):
    uid, error_response = _get_uid_from_token()
    if error_response:
        return error_response

    try:
        delete_book(uid, book_id)
        return jsonify({"message": "Book deleted successfully"}), 200
    except Exception as e:
        logger.error(f"Error deleting book {book_id}: {str(e)}")
        return jsonify({"error": "Failed to delete book"}), 500

@app.route('/api/books/<book_id>/reprocess', methods=['POST'])
def reprocess_book(book_id):
    uid, error_response = _get_uid_from_token()
    if error_response:
        return error_response

    book_doc = get_book(uid, book_id)
    if not book_doc:
        return jsonify({"error": "Book not found or not authorized"}), 404

    corrected_data = request.json
    update_payload = {"status": "reprocessing"}
    if 'title' in corrected_data:
        update_payload['title'] = corrected_data['title']
    if 'author' in corrected_data:
        update_payload['author'] = corrected_data['author']
    if 'isbn' in corrected_data:
        update_payload['isbn'] = corrected_data['isbn']
        
    update_book(uid, book_id, update_payload)

    message_data = json.dumps({
        "bookId": book_id,
        "userId": uid,
        "corrected_data": corrected_data
    }).encode('utf-8')
    try:
        publisher.publish(topic_path, data=message_data).result()
    except Exception as e:
        return jsonify({"error": "Failed to publish reprocessing message"}), 500

    return jsonify({"message": "Book is being reprocessed."}), 200

@app.route('/api/books/assess-condition', methods=['POST'])
@limiter.limit("30 per minute")  # LLM-heavy operation
def assess_condition():
    """Trigger condition assessment for a book using Vertex AI."""
    uid, error_response = _get_uid_from_token()
    if error_response:
        return error_response

    try:
        request_data = request.json
        book_id = request_data.get('bookId')
        images = request_data.get('images', []) # Optional: images can be passed explicitly
        metadata = request_data.get('metadata', {})

        if not book_id:
            return jsonify({"error": "bookId is required"}), 400

        # Check if book exists and user has access
        book_doc = get_book(uid, book_id)
        if not book_doc:
            return jsonify({"error": "Book not found or not authorized"}), 404
            
        # If no images provided, use existing images from book document
        if not images:
            image_urls = book_doc.get('imageUrls', [])
            if not image_urls:
                return jsonify({"error": "No images found for this book"}), 400
            
            # Convert simple URLs to image objects for the assessor
            # Assume unknown type since we don't have classification yet
            images = [{'gcs_uri': url, 'type': 'unknown'} for url in image_urls]

        # Enhance metadata with book details
        enhanced_metadata = {
            **metadata,
            'book_id': book_id,
            'uid': uid,
            'title': book_doc.get('title', ''),
            'authors': book_doc.get('authors', []),
            'publication_year': book_doc.get('publication_year'),
            'publisher': book_doc.get('publisher'),
            'edition': book_doc.get('edition'),
            'isbn': book_doc.get('isbn', '') or book_doc.get('isbn_13') or book_doc.get('isbn_10')
        }

        # Create a request for the Condition Assessment Agent in Firestore
        assessment_payload = {
            'images': images,
            'metadata': enhanced_metadata,
            'status': 'pending',
            'created_at': datetime.datetime.utcnow().isoformat()
        }
        
        create_condition_assessment_request(uid, book_id, assessment_payload)
        
        # Update book status to indicate assessment is in progress
        update_book(uid, book_id, {'status': 'condition_assessment_pending'})

        # Publish message to Pub/Sub for Condition Assessment Agent
        message_data = json.dumps({
            "book_id": book_id,
            "user_id": uid,
            "image_urls": [img['gcs_uri'] for img in images],
            "metadata": enhanced_metadata
        }).encode('utf-8')
        
        try:
            publisher.publish(condition_assessment_topic_path, data=message_data).result()
            logger.info(f"Published condition assessment job for book {book_id}")
        except Exception as pub_error:
            logger.error(f"Failed to publish condition assessment message: {str(pub_error)}")
            # Continue even if Pub/Sub fails - the Firestore trigger should still work
        
        return jsonify({
            "message": "Condition assessment request created successfully.",
            "bookId": book_id
        }), 202

    except Exception as e:
        print(f"Condition assessment error: {str(e)}")
        return jsonify({"error": "Assessment failed", "details": str(e)}), 500

@app.route('/api/books/<book_id>/condition-assessment', methods=['GET'])
def get_condition_assessment(book_id):
    """Get existing condition assessment for a book."""
    uid, error_response = _get_uid_from_token()
    if error_response:
        return error_response

    try:
        # Check if book exists and user has access
        book_doc = get_book(uid, book_id)
        if not book_doc:
            return jsonify({"error": "Book not found or not authorized"}), 404

        # Get condition assessment from Firestore
        from shared.firestore.client import get_firestore_client
        db = get_firestore_client()
        
        condition_ref = db.collection('users').document(uid).collection('condition_assessments').document(book_id)
        condition_doc = condition_ref.get()
        
        if not condition_doc.exists:
            return jsonify({"error": "No condition assessment found"}), 404
            
        return jsonify(condition_doc.to_dict()), 200

    except Exception as e:
        print(f"Get condition assessment error: {str(e)}")
        return jsonify({"error": "Failed to get assessment", "details": str(e)}), 500

@app.route('/api/books/override-condition', methods=['POST'])
def override_condition():
    """Override AI condition assessment with manual assessment."""
    uid, error_response = _get_uid_from_token()
    if error_response:
        return error_response

    try:
        request_data = request.json
        book_id = request_data.get('bookId')
        override_grade = request_data.get('overrideGrade')
        reason = request_data.get('reason')

        if not all([book_id, override_grade, reason]):
            return jsonify({"error": "bookId, overrideGrade, and reason are required"}), 400

        # Check if book exists and user has access
        book_doc = get_book(uid, book_id)
        if not book_doc:
            return jsonify({"error": "Book not found or not authorized"}), 404

        # Calculate price factor for override grade
        grade_factors = {
            'Fine': 1.0,
            'Very Fine': 0.85,
            'Good': 0.65,
            'Fair': 0.45,
            'Poor': 0.25
        }
        
        price_factor = grade_factors.get(override_grade, 0.7)

        # Update condition assessment with override
        from shared.firestore.client import get_firestore_client
        db = get_firestore_client()
        
        condition_ref = db.collection('users').document(uid).collection('condition_assessments').document(book_id)
        condition_doc = condition_ref.get()
        
        if condition_doc.exists:
            # Update existing assessment
            assessment_data = condition_doc.to_dict()
            assessment_data.update({
                'grade': override_grade,
                'price_factor': price_factor,
                'manual_override': True,
                'override_reason': reason,
                'override_timestamp': datetime.datetime.utcnow().isoformat(),
                'overridden_by': uid
            })
            condition_ref.set(assessment_data)
        else:
            # Create new assessment with override
            assessment_data = {
                'book_id': book_id,
                'uid': uid,
                'grade': override_grade,
                'price_factor': price_factor,
                'manual_override': True,
                'override_reason': reason,
                'timestamp': datetime.datetime.utcnow().isoformat(),
                'override_timestamp': datetime.datetime.utcnow().isoformat(),
                'overridden_by': uid
            }
            condition_ref.set(assessment_data)
        
        # Update book document
        update_book(uid, book_id, {
            'ai_condition_grade': override_grade,
            'condition_assessed_at': datetime.datetime.utcnow().isoformat(),
            'price_factor': price_factor,
            'manual_override': True
        })

        # Create response
        result = {
            'condition_assessment': {
                'grade': override_grade,
                'price_factor': price_factor,
                'manual_override': True,
                'override_reason': reason
            }
        }

        return jsonify(result), 200

    except Exception as e:
        print(f"Override condition error: {str(e)}")
        return jsonify({"error": "Override failed", "details": str(e)}), 500

@app.route('/api/books/<book_id>/condition-history', methods=['GET'])
def get_condition_history(book_id):
    """Get condition assessment history for a book."""
    uid, error_response = _get_uid_from_token()
    if error_response:
        return error_response

    try:
        # Check if book exists and user has access
        book_doc = get_book(uid, book_id)
        if not book_doc:
            return jsonify({"error": "Book not found or not authorized"}), 404

        # Get condition history from Firestore
        from shared.firestore.client import get_firestore_client
        db = get_firestore_client()
        
        history_ref = db.collection('users').document(uid).collection('condition_history').where('book_id', '==', book_id).order_by('timestamp', direction='DESCENDING')
        history_docs = history_ref.stream()
        
        history = [doc.to_dict() for doc in history_docs]
        
        return jsonify({'history': history}), 200

    except Exception as e:
        print(f"Get condition history error: {str(e)}")
        return jsonify({"error": "Failed to get history", "details": str(e)}), 500

# LLM Manager Removal: Endpoints removed

@app.route('/api/health', methods=['GET'])
@limiter.exempt  # No rate limit on health checks
def health_check():
    """Health check endpoint to verify backend is running."""
    return jsonify({
        "status": "healthy",
        "message": "Backend is running",
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "version": "1.0.0-alpha"
    }), 200

@app.route('/api/rate-limit-status', methods=['GET'])
@limiter.exempt
def rate_limit_status():
    """Check rate limit status for current client"""
    return jsonify({
        "limits": {
            "default": "100 per minute",
            "uploads": "20 per minute",
            "processing": "50 per minute",
            "llm_operations": "30 per minute",
            "credentials": "10 per minute"
        },
        "client": request.remote_addr,
        "user_agent": request.headers.get('User-Agent', 'Unknown')
    }), 200

if __name__ == '__main__':
    print("=== BACKEND STARTUP ===")
    print(f"GCP_PROJECT_ID: {project_id}")
    print(f"GCS_BUCKET_NAME: {bucket_name}")
    print("Starting Flask app on http://0.0.0.0:8080")
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))