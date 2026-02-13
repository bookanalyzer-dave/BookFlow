import base64
import json
import asyncio
import logging
import functions_framework
from typing import Dict, Any
from google.cloud import firestore
import os

from platforms.ebay import EbayPlatform
from shared.firestore.client import get_firestore_client

# New GenAI SDK
try:
    from google import genai
    from google.genai import types
except ImportError:
    raise ImportError("google-genai>=0.8.0 is required.")

# Konfiguriere Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def validate_environment() -> Dict[str, str]:
    """Validate required environment variables are set."""
    required_vars = {
        "GCP_PROJECT": os.environ.get("GCP_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT"),
    }
    
    missing = [key for key, value in required_vars.items() if not value]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    logger.info(f"Environment validation passed for: {', '.join(required_vars.keys())}")
    return required_vars


# --- Konfiguration ---
env_vars = validate_environment()
GCP_PROJECT = env_vars["GCP_PROJECT"]
DEFAULT_LLM_MODEL = os.getenv("DEFAULT_LLM_MODEL", "gemini-2.0-flash")

# GenAI Client Initialization
try:
    project_id = GCP_PROJECT
    location = os.environ.get("GCP_REGION", "us-central1")
    
    if project_id:
        genai_client = genai.Client(
            vertexai=True,
            project=project_id,
            location=location
        )
        logger.info(f"Gemini client configured for Vertex AI (project={project_id}, location={location})")
    else:
        # Fallback to API Key for local dev if set
        api_key = os.getenv("GEMINI_API_KEY")
        if api_key:
            genai_client = genai.Client(api_key=api_key)
            logger.info("Gemini client configured with API Key (Local Dev Mode)")
        else:
            logger.warning("No Project ID or API Key found. GenAI client might fail.")
            genai_client = None

except Exception as e:
    logger.error(f"Failed to configure Gemini client: {e}")
    genai_client = None

async def enhance_product_description_with_llm(user_id: str, book_data: Dict[str, Any]) -> str:
    """
    Enhance product description using Gemini API.
    Falls back to original description if LLM is unavailable.
    """
    if not genai_client:
        logger.info("Gemini client not available, using original description")
        return book_data.get("description", "")
    
    try:
        prompt = f"""
        Create a compelling marketplace listing description for this book:
        
        Title: {book_data.get('title', 'N/A')}
        Author: {book_data.get('author', 'N/A')}
        Condition: {book_data.get('condition', 'N/A')}
        Original Description: {book_data.get('description', 'N/A')}
        
        Requirements:
        - Professional and engaging tone
        - Highlight the book's condition honestly
        - Mention key selling points
        - Keep it concise (3-4 sentences max)
        - Make it suitable for marketplace platforms
        
        Return ONLY the description text, no additional formatting.
        """
        
        response = genai_client.models.generate_content(
            model=DEFAULT_LLM_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                max_output_tokens=300
            )
        )
        
        logger.info(f"Enhanced description via Gemini API")
        return response.text.strip()
        
    except Exception as e:
        logger.warning(f"Gemini API failed: {e}. Using original description.")
        return book_data.get("description", "")


PLATFORMS = {
    "ebay": EbayPlatform,
}

@functions_framework.cloud_event
def handle_listing_request(cloud_event: Any) -> None:
    """Triggered by a Pub/Sub message to create a listing on a marketplace."""
    return asyncio.run(_async_handle_listing_request(cloud_event))


async def _async_handle_listing_request(cloud_event: Any) -> None:
    """
    Async implementation of listing request handler with User LLM Manager integration.
    """
    message_data = base64.b64decode(cloud_event.data["message"]["data"]).decode("utf-8")
    message_payload = json.loads(message_data)

    book_id = message_payload.get("bookId")
    uid = message_payload.get("uid")
    platform_name = message_payload.get("platform")
    book_data = message_payload.get("book")

    if not all([book_id, uid, platform_name, book_data]):
        logger.warning("Missing required fields in listing request")
        return

    platform_class = PLATFORMS.get(platform_name)
    if not platform_class:
        logger.warning(f"Unknown platform: {platform_name}")
        return

    try:
        # Enhance product description using Gemini API
        if genai_client:
            enhanced_description = await enhance_product_description_with_llm(uid, book_data)
            if enhanced_description:
                book_data["description"] = enhanced_description
                logger.info(f"Enhanced description for book {book_id}")

        ebay_credentials = {
            "app_id": os.environ.get("EBAY_APP_ID"),
            "dev_id": os.environ.get("EBAY_DEV_ID"),
            "cert_id": os.environ.get("EBAY_CERT_ID"),
            "token": os.environ.get("EBAY_TOKEN"),
        }

        if not all(ebay_credentials.values()):
            logger.error("Missing eBay credentials")
            return

        platform_instance = platform_class(**ebay_credentials)
        listing_id = platform_instance.create_listing(book_data)

        # Update Firestore using Multi-Tenancy structure
        db = get_firestore_client()
        book_ref = db.collection("users").document(uid).collection("books").document(book_id)
        listing_ref = book_ref.collection("listings").document()

        listing_ref.set({
            "platform": platform_name,
            "listing_id": listing_id,
            "status": "active",
            "created_at": firestore.SERVER_TIMESTAMP,
        })
        
        logger.info(f"Successfully created listing {listing_id} for book {book_id} on {platform_name}")

    except Exception as e:
        logger.error(f"Failed to create listing for book {book_id}: {e}")
        db = get_firestore_client()
        book_ref = db.collection("users").document(uid).collection("books").document(book_id)
        listing_ref = book_ref.collection("listings").document()
        listing_ref.set({
            "platform": platform_name,
            "status": "error",
            "error_message": str(e),
            "created_at": firestore.SERVER_TIMESTAMP,
        })

@functions_framework.cloud_event
def delist_book_everywhere(cloud_event: Any) -> None:
    """Triggered by a Pub/Sub message to delist a book from all marketplaces."""
    message_data = base64.b64decode(cloud_event.data["message"]["data"]).decode("utf-8")
    message_payload = json.loads(message_data)

    book_id = message_payload.get("bookId")
    uid = message_payload.get("uid")

    if not book_id or not uid:
        return

    db = get_firestore_client()
    book_ref = db.collection("users").document(uid).collection("books").document(book_id)
    listings_ref = book_ref.collection("listings")

    try:
        active_listings = listings_ref.where("status", "==", "active").stream()

        for listing in active_listings:
            listing_data = listing.to_dict()
            platform_name = listing_data.get("platform")
            listing_id = listing_data.get("listing_id")

            platform_class = PLATFORMS.get(platform_name)
            if not platform_class:
                continue

            ebay_credentials = {
                "app_id": os.environ.get("EBAY_APP_ID"),
                "dev_id": os.environ.get("EBAY_DEV_ID"),
                "cert_id": os.environ.get("EBAY_CERT_ID"),
                "token": os.environ.get("EBAY_TOKEN"),
            }

            if not all(ebay_credentials.values()):
                continue
            
            platform_instance = platform_class(**ebay_credentials)
            platform_instance.delete_listing(listing_id)

            listing.reference.update({"status": "delisted"})

    except Exception as e:
        pass