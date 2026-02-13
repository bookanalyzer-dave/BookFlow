import base64
import json
import os
import sys

# PATH HACK: Ensure local imports work in Cloud Functions
# Add current directory to path so 'shared' module is found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import re
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from google.cloud import pubsub_v1
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

import functions_framework
from cloudevents.http import CloudEvent

from shared.firestore.client import get_firestore_client, get_book, update_book
#from shared.price_research.orchestrator import PriceOrchestrator # Coming in Phase 2

# Feature Flag
PRICE_RESEARCH_ENABLED = os.environ.get("PRICE_RESEARCH_ENABLED", "true").lower() == "true"
GEMINI_MODEL_PRICE = os.environ.get("GEMINI_MODEL", "gemini-1.5-flash-002")

# GenAI Import for Types and Client
try:
    from google import genai
    from google.genai import types
except ImportError:
    # Fail fast if dependency is missing
    raise ImportError("google-genai>=0.3.0 is required.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION & INITIALIZATION (HARDENED)
# ============================================================================

def get_required_env(key: str) -> str:
    """Holt eine Umgebungsvariable oder wirft einen Fehler, wenn sie fehlt."""
    value = os.environ.get(key)
    if not value:
        raise RuntimeError(f"CRITICAL: Environment variable '{key}' is not set.")
    return value

# Feature Flags
# LLM_MANAGER_REMOVAL: Direct Gemini Client initialization

# Initialize Shared Components
db = None
publisher = None
genai_client = None
PROJECT_ID = None

def init_globals():
    global db, publisher, genai_client, PROJECT_ID
    
    # 1. Project ID (Fail Fast)
    PROJECT_ID = get_required_env("GCP_PROJECT")
    
    # 2. Firestore
    if db is None:
        try:
            db = get_firestore_client() # from shared lib
            logger.info(f"Firestore client initialized for project {PROJECT_ID}")
        except Exception as e:
            logger.critical(f"Failed to initialize Firestore: {e}")
            raise # Crash -> Retry

    # 3. Pub/Sub
    if publisher is None:
        try:
            publisher = pubsub_v1.PublisherClient()
            logger.info("Pub/Sub publisher initialized")
        except Exception as e:
            logger.critical(f"Failed to initialize Pub/Sub publisher: {e}")
            raise # Crash -> Retry

    # 4. Gemini (Vertex AI)
    if genai_client is None:
        try:
            location = os.environ.get("GCP_REGION", "europe-west1")
            genai_client = genai.Client(
                vertexai=True,
                project=PROJECT_ID,
                location=location
            )
            logger.info(f"Gemini client initialized (Vertex AI, {PROJECT_ID}, {location})")
        except Exception as e:
            logger.critical(f"Failed to initialize Gemini client: {e}")
            raise # Crash -> Retry

# ============================================================================
# MAIN AGENT LOGIC
# ============================================================================

@functions_framework.cloud_event
def strategist_agent(cloud_event: CloudEvent) -> Any:
    """Triggered from a message on a Cloud Pub/Sub topic."""
    # Ensure globals are initialized
    try:
        init_globals()
    except Exception as e:
        logger.error(f"Initialization failed: {e}")
        return 'Internal Server Error', 500

    # Extract data from CloudEvent
    try:
        event_data = {
            "data": cloud_event.data["message"]["data"]
        }
        asyncio.run(strategist_agent_main(event_data, None))
        return 'OK', 200
    except Exception as e:
        logger.error(f"Error processing event: {e}")
        return 'Internal Server Error', 500

async def strategist_agent_main(event: Any, context: Any) -> None:
    """Main strategist agent logic: Condition Data + Images -> Gemini 2.5 Pro (w/ Search) -> Price."""
    
    try:
        pubsub_message = base64.b64decode(event['data']).decode('utf-8')
        message_data = json.loads(pubsub_message)
        
        # 1. Extract IDs
        book_id = message_data.get('bookId') or message_data.get('book_id')
        uid = message_data.get('uid') or message_data.get('user_id')
        event_image_urls = message_data.get('imageUrls') or message_data.get('image_urls', [])
        
        if not book_id or not uid:
            logger.error(f"❌ Missing required fields (bookId, uid) in message: {message_data}")
            return

        logger.info(f"🚀 Starting Strategist Agent for book {book_id} (User: {uid})")

        # 2. Fetch Book Metadata
        book_dict = get_book(uid, book_id)
        if not book_dict:
            logger.warning(f"Book {book_id} not found for user {uid}")
            return
            
        # Idempotency Check
        if book_dict.get('status') in ['priced', 'listed']:
            logger.info(f"ℹ️ Book {book_id} is already in state '{book_dict.get('status')}'. Skipping pricing.")
            return

        # 3. Fetch Condition Assessment Data
        condition_data = await _get_condition_data(uid, book_id)
        if not condition_data:
            logger.warning(f"⚠️ No condition data found for {book_id}. Proceeding with metadata only, but results may be suboptimal.")
        
        # 4. Prepare "Super Request" for Gemini
        try:
            if not genai_client:
                raise ValueError("Gemini client is not initialized")
                
            pricing_result = await _generate_price_suggestion(genai_client, uid, book_id, book_dict, condition_data, event_image_urls)
        except Exception as e:
            logger.error(f"❌ Pricing generation failed: {e}")
            # Optionally set status to 'pricing_failed'
            update_book(uid, book_id, {'status': 'pricing_failed', 'error': str(e)})
            return

        # 5. Save Result
        if pricing_result:
            # Update book with pricing data
            update_data = {
                'status': 'priced',
                'calculatedPrice': pricing_result.get('price', 0.0),
                'pricing': pricing_result,
                # 'priced_at' is updated below with correct format
            }
            # Merge AI condition data if we have it separately
            if condition_data:
                 update_data['ai_condition_grade'] = condition_data.get('grade')
                 update_data['ai_condition_score'] = condition_data.get('overall_score')
            
            # Update priced_at with ISO format
            update_data['priced_at'] = datetime.utcnow().isoformat()
            
            update_book(uid, book_id, update_data)
            logger.info(f"✅ Pricing complete for {book_id}: ${pricing_result.get('price')} (Conf: {pricing_result.get('confidence')})")
            
            # 6. Trigger Listing (Optional, or next step)
            await _publish_listing_request(uid, book_id)
            
    finally:
        pass

async def _get_condition_data(uid: str, book_id: str) -> Optional[Dict[str, Any]]:
    """Fetch condition assessment from Firestore."""
    try:
        doc_ref = db.collection('users').document(uid).collection('condition_assessments').document(book_id)
        doc = doc_ref.get()
        if doc.exists:
            return doc.to_dict()
        return None
    except Exception as e:
        logger.error(f"Error fetching condition data: {e}")
        return None

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(Exception)
)
async def _generate_price_suggestion(client: genai.Client, uid: str, book_id: str, book_data: Dict[str, Any], condition_data: Optional[Dict[str, Any]], image_urls: List[str]) -> Dict[str, Any]:
    """Call Gemini 2.5 Pro with Google Search to determine price."""
    
    # Construct Content
    title = book_data.get('title', 'Unknown Title')
    author = book_data.get('author', 'Unknown Author')
    if isinstance(author, list): author = ", ".join(author)
    isbn = book_data.get('isbn', 'N/A')
    publisher_name = book_data.get('publisher', 'Unknown Publisher')
    year = book_data.get('publication_year') or book_data.get('year', 'Unknown Year')
    
    # Format Condition Data for Prompt
    condition_text = "No detailed condition report available."
    if condition_data:
        condition_text = json.dumps(condition_data, indent=2)

    prompt = f"""
You are an expert antiquarian bookseller. Your task is to determine the optimal listing price for a book based on its details, condition, and your extensive internal knowledge of the book market.

**Book Details:**
Title: {title}
Author: {author}
Year: {year}
Publisher: {publisher_name}
ISBN: {isbn}

**Condition Report:**
{condition_text}

**Instructions:**
1. Analyze the book's details and condition report.
2. Estimate a competitive list price (in EUR) based on your knowledge of similar books, editions, and their market value.
3. Consider the condition heavily in your valuation.
4. Provide a confidence score (0.0 - 1.0) and a brief reasoning explaining how you arrived at this estimate (e.g., "First edition, good condition, highly collectible").

**Output Format:**
Return valid JSON only. Do not wrap the response in markdown code blocks. Do not include any text outside the JSON object.
{{
  "price": <float, e.g. 24.99>,
  "confidence": <float, 0.0-1.0>,
  "reasoning": "<concise explanation>",
  "sources": []
}}
"""

    contents = []
    
    # Add Text
    contents.append(prompt)
    
    # Add Images
    # SIMPLIFICATION (2025-02-13): Removing images from pricing request to avoid 400 Bad Request errors.
    # The condition assessor has already processed the images, and we have the text metadata.
    # Relying solely on text metadata + condition report for pricing search is more robust and cheaper.
    logger.info("Skipping image inclusion for pricing request to improve stability and avoid Vertex AI 400 errors.")
    # images_to_use = image_urls or book_data.get('imageUrls', [])
    # for img_url in images_to_use:
    #     if img_url and img_url.startswith('gs://'):
    #         contents.append(types.Part.from_uri(file_uri=img_url, mime_type="image/jpeg"))


    # Prepare Request config WITHOUT Google Search tool (Stability Fix)
    # We rely on internal knowledge to avoid Runtime/Retry errors with the Search tool.
    
    config = types.GenerateContentConfig(
        temperature=0.1,
        # tools=[types.Tool(google_search=types.GoogleSearch())], # DISABLED for stability
        response_mime_type="application/json"
    )
    
    logger.info(f"Sending pricing request to {GEMINI_MODEL_PRICE} for {book_id}")
    
    response = client.models.generate_content(
        model=GEMINI_MODEL_PRICE,
        contents=contents,
        config=config
    )
    
    # Parse Response
    try:
        # Check if response has text (it might be blocked or empty)
        if not response.text:
            logger.error(f"Empty response from LLM. Finish reason: {response.finish_reason}")
            raise ValueError("Empty response from LLM")

        data = _parse_json(response.text)
        
        # Validation
        if "price" not in data:
            raise ValueError("Missing 'price' field in LLM response")
            
        return data
    except Exception as e:
        logger.error(f"Failed to parse LLM pricing response: {response.text} - Error: {e}")
        raise Exception(f"Invalid JSON from LLM: {e}")

def _parse_json(content: str) -> Dict[str, Any]:
    """Parse JSON from LLM response with robust fallback."""
    # 1. Try direct parsing
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass
        
    # 2. Try regex extraction (greedy match for outermost braces)
    try:
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            return json.loads(json_match.group(0))
    except Exception:
        pass
        
    # 3. Try markdown cleanup as last resort
    try:
        clean_content = re.sub(r"^```json\s*", "", content, flags=re.MULTILINE)
        clean_content = re.sub(r"^```\s*", "", clean_content, flags=re.MULTILINE)
        clean_content = re.sub(r"```$", "", clean_content, flags=re.MULTILINE).strip()
        return json.loads(clean_content)
    except Exception:
        pass
        
    raise ValueError(f"Could not parse JSON from response. Content: {content[:200]}...")

async def _publish_listing_request(uid: str, book_id: str) -> None:
    """Publish message to trigger listing agent (or next step)."""
    try:
        topic_path = publisher.topic_path(PROJECT_ID, 'book-listing-requests')
        message_data = {
            'bookId': book_id, 
            'uid': uid, 
            'platform': 'ebay', # Default to ebay for now
            'timestamp': asyncio.get_event_loop().time()
        }
        message_bytes = json.dumps(message_data).encode('utf-8')
        publisher.publish(topic_path, data=message_bytes)
        logger.info(f"📤 Published listing request for {book_id}")
    except Exception as e:
        logger.error(f"Failed to publish listing request: {e}")
