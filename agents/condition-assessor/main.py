"""
Vertex AI Condition Assessment Agent (GenAI Refactor)
===================================================

Professional book condition assessment using the Google Generative AI SDK
for accurate grading according to ABAA/ILAB standards.

Features:
- Holistic multi-image analysis using Generative AI
- "Book Condition Specialist" persona
- Standard ABAA grading (Fine/Very Fine/Good/Fair/Poor)
- Structured JSON output for frontend compatibility
"""

import os
import sys

# PATH HACK: Ensure local imports work in Cloud Functions
# Add current directory to path so 'shared' module is found
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
import asyncio
import json
import base64
import time
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
from io import BytesIO
from PIL import Image

from google.cloud import storage, pubsub_v1
import functions_framework

# New GenAI SDK
try:
    from google import genai
    from google.genai import types
except ImportError:
    raise ImportError("google-genai>=0.8.0 is required.")

from shared.firestore.client import get_firestore_client, update_book

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Pub/Sub Publisher
publisher = pubsub_v1.PublisherClient()
PROJECT_ID = os.environ.get("GCP_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT")

# ============================================================================
# CLIENT INITIALIZATION
# ============================================================================
# IMPORTANT: Initialize storage client before any other Google library
# that might be affected by genai.configure() which sets a global API key.
# This ensures the storage client uses Application Default Credentials (ADC).
storage_client = storage.Client()
logger.info("Storage client initialized successfully.")

# GenAI Client Initialization
try:
    # Use Vertex AI by default in production
    project_id = os.environ.get("GCP_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT")
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
    # Don't exit yet, allow function to start but fail on request if needed
    genai_client = None


def validate_environment() -> Dict[str, str]:
    """Validate required environment variables are set."""
    # Check either GCP_PROJECT or GOOGLE_CLOUD_PROJECT
    project = os.environ.get("GCP_PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT")
    
    required_vars = {
        "GCP_PROJECT": project,
    }
    
    missing = [key for key, value in required_vars.items() if not value]
    if missing:
        # Log warning instead of crashing, as local testing might use different vars
        logger.warning(f"Missing environment variables: {', '.join(missing)}")
    
    return required_vars


class ConditionGrade(Enum):
    """Standardized condition grades based on ABAA/ILAB standards"""
    FINE = "Fine"                    # 90-100% - Like new, minimal wear
    VERY_FINE = "Very Fine"          # 80-89% - Light wear, structurally sound
    GOOD = "Good"                    # 60-79% - Moderate wear, complete
    FAIR = "Fair"                    # 40-59% - Notable wear, minor defects
    POOR = "Poor"                    # 0-39% - Significant damage, readable

@dataclass
class ConditionScore:
    """Standardized condition score output"""
    overall_score: float
    grade: ConditionGrade
    confidence: float
    details: Dict[str, Any]
    price_factor: float
    component_scores: Dict[str, float]

class VertexAIConditionAssessor:
    """Main condition assessment agent using Gemini Pro Vision"""
    
    def __init__(self, user_id: Optional[str] = None):
        """Initialize the Condition Assessor"""
        # Validate environment
        validate_environment()
        
        self.project_id = os.getenv('GOOGLE_CLOUD_PROJECT')
        self.user_id = user_id
        
        # Initialize clients
        self.storage_client = storage_client
        self.client = genai_client
        
        # Configuration
        self.model_name = "gemini-2.0-flash-001"  # Use stable flash model for cost/speed efficiency
        self.temperature = 0.1  # Low temperature for analytical consistency

    async def assess_book_condition(
        self, 
        images: List[Dict[str, any]], 
        book_metadata: Optional[Dict] = None
    ) -> ConditionScore:
        """
        Perform comprehensive book condition assessment using GenAI.
        """
        try:
            logger.info(f"Starting GenAI condition assessment for {len(images)} images")
            
            if not self.client:
                raise ValueError("GenAI client is not initialized.")

            # 1. Fetch and Prepare Images
            image_parts = await self._prepare_images(images)
            if not image_parts:
                raise ValueError("No valid images provided for assessment")
            
            # 2. Construct Prompt
            prompt_text = self._construct_prompt(book_metadata)
            
            # 3. Call LLM
            logger.info(f"Sending request to {self.model_name} with {len(image_parts)} images")
            
            safety_settings = [
                types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
                types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=types.HarmBlockThreshold.BLOCK_NONE),
            ]

            generation_config = types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=self.temperature,
                safety_settings=safety_settings
            )
            
            contents = image_parts + [prompt_text]
            
            # Retry logic for 429 Resource Exhausted
            max_retries = 3
            base_delay = 2
            
            for attempt in range(max_retries):
                try:
                    response = self.client.models.generate_content(
                        model=self.model_name,
                        contents=contents,
                        config=generation_config
                    )
                    return self._parse_llm_response(response.text)
                
                except Exception as e:
                    error_str = str(e)
                    if "429" in error_str or "Resource has been exhausted" in error_str:
                        if attempt < max_retries - 1:
                            sleep_time = base_delay * (2 ** attempt)
                            logger.warning(f"⚠️ Quota exceeded (429). Retrying in {sleep_time}s... (Attempt {attempt + 1}/{max_retries})")
                            time.sleep(sleep_time)
                            continue
                    
                    logger.error(f"Error during GenAI condition assessment: {error_str}")
                    raise
            
        except Exception as e:
            logger.error(f"Error during GenAI condition assessment: {str(e)}")
            raise

    async def _prepare_images(self, images: List[Dict[str, any]]) -> List[types.Part]:
        image_parts = []
        for idx, img in enumerate(images):
            try:
                gcs_uri = img.get('gcs_uri') or img.get('imageUrl')
                if gcs_uri and gcs_uri.startswith('gs://'):
                    image_bytes = await self._fetch_gcs_image(gcs_uri)
                    if image_bytes:
                         image_parts.append(types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"))
                elif img.get('content'):
                    b64_content = img.get('content')
                    if "," in b64_content: b64_content = b64_content.split(",")[1]
                    image_bytes = base64.b64decode(b64_content)
                    image_parts.append(types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"))
            except Exception as e:
                logger.error(f"Failed to process image {idx+1}: {e}")
                continue
        return image_parts

    async def _fetch_gcs_image(self, gcs_uri: str) -> Optional[bytes]:
        try:
            parts = gcs_uri.replace("gs://", "").split("/", 1)
            if len(parts) != 2: return None
            bucket_name, blob_name = parts
            bucket = self.storage_client.bucket(bucket_name)
            blob = bucket.blob(blob_name)
            return blob.download_as_bytes()
        except Exception as e:
            logger.error(f"GCS download error for {gcs_uri}: {e}")
            return None

    def _construct_prompt(self, metadata: Optional[Dict] = None) -> str:
        meta_context = ""
        if metadata:
            title = metadata.get('title', 'Unknown')
            year = metadata.get('year') or metadata.get('publication_year') or 'Unknown'
            publisher = metadata.get('publisher', 'Unknown')
            meta_context = f"\nBOOK CONTEXT:\nTitle: {title}\nYear: {year}\nPublisher: {publisher}\n"

        return f"""
You are an expert antiquarian bookseller and professional book condition grader.
You have been provided with a set of images of a single book.

{meta_context}

Your task is to analyze the book's condition and output strictly valid JSON matching this schema:
{{
  "grade": "Fine|Very Fine|Good|Fair|Poor",
  "score": <number 0-100>,
  "price_factor": <number 0.1-1.0>,
  "confidence": <number 0.0-1.0>,
  "summary": "<concise professional summary of condition>",
  "defects": ["<defect 1>", "<defect 2>"],
  "components": {{
    "cover": {{ "score": <0-100>, "description": "..." }},
    "spine": {{ "score": <0-100>, "description": "..." }},
    "pages": {{ "score": <0-100>, "description": "..." }},
    "binding": {{ "score": <0-100>, "description": "..." }}
  }}
}}
"""

    def _parse_llm_response(self, response_text: str) -> ConditionScore:
        try:
            clean_text = response_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean_text)
            grade_str = data.get('grade', 'Good').strip().upper().replace(" ", "_")
            grade_map = {"FINE": ConditionGrade.FINE, "VERY_FINE": ConditionGrade.VERY_FINE, "GOOD": ConditionGrade.GOOD, "FAIR": ConditionGrade.FAIR, "POOR": ConditionGrade.POOR}
            grade = grade_map.get(grade_str, ConditionGrade.GOOD)
            components = data.get('components', {})
            component_scores = {k: float(components.get(k, {}).get('score', 0)) for k in ['cover', 'spine', 'pages', 'binding']}
            details = {'summary': data.get('summary', ''), 'defects_list': data.get('defects', []), 'cover_defects': components.get('cover', {}).get('description', ''), 'spine_defects': components.get('spine', {}).get('description', ''), 'pages_defects': components.get('pages', {}).get('description', ''), 'binding_defects': components.get('binding', {}).get('description', '')}
            return ConditionScore(overall_score=float(data.get('score', 0)), grade=grade, confidence=float(data.get('confidence', 0.5)), price_factor=float(data.get('price_factor', 0.5)), details=details, component_scores=component_scores)
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return ConditionScore(overall_score=0.0, grade=ConditionGrade.GOOD, confidence=0.0, price_factor=0.5, details={'summary': 'Assessment failed.'}, component_scores={})

@functions_framework.cloud_event
def assess_condition_handler(cloud_event: Any):
    try:
        message_data = base64.b64decode(cloud_event.data["message"]["data"]).decode('utf-8')
        message_json = json.loads(message_data)
        book_id = message_json.get('book_id')
        user_id = message_json.get('user_id')
        if not book_id or not user_id: return 'Bad Request', 400
        raw_images = message_json.get('image_urls', [])
        images_list = [{"gcs_uri": img} for img in raw_images if isinstance(img, str)]
        metadata = message_json.get('metadata', {})
        asyncio.run(process_assessment(user_id, book_id, images_list, metadata))
        return 'OK', 200
    except Exception as e:
        logger.error(f"Error: {e}")
        return 'Error', 500

async def process_assessment(user_id: str, book_id: str, images: List[Dict], metadata: Dict) -> None:
    db = get_firestore_client()
    book_ref = db.collection('users').document(user_id).collection('books').document(book_id)
    
    # Check if book exists and status before processing (with retry)
    book_snap = None
    book_data = {}
    
    for attempt in range(3):
        try:
            book_snap = book_ref.get()
            if book_snap.exists:
                book_data = book_snap.to_dict()
                break
        except Exception as e:
            logger.warning(f"Attempt {attempt+1} to fetch book {book_id} failed: {e}")
        
        if attempt < 2:
            await asyncio.sleep(1 * (2 ** attempt))

    if not book_snap or not book_snap.exists:
        logger.warning(f"⚠️ Book {book_id} not found for user {user_id} after retries. Proceeding with assessment using available message data.")
    else:
        current_status = book_data.get('status')
        
        # IDEMPOTENCY CHECK: If already assessed or priced, skip and just publish completion event
        if current_status in ['condition_assessed', 'priced', 'listed']:
            logger.info(f"ℹ️ Book {book_id} already in state '{current_status}'. Skipping GenAI analysis.")
            # Still publish completion event just in case downstream agents missed it
            image_urls = [img.get('gcs_uri') or img.get('imageUrl') for img in images]
            await publish_completion_event(user_id, book_id, image_urls)
            return

    request_ref = db.collection('users', user_id, 'condition_assessment_requests').document(book_id)
    try:
        assessor = VertexAIConditionAssessor(user_id=user_id)
        condition_score = await assessor.assess_book_condition(images, metadata)
        assessment_data = {'book_id': book_id, 'uid': user_id, 'overall_score': condition_score.overall_score, 'grade': condition_score.grade.value, 'confidence': condition_score.confidence, 'component_scores': condition_score.component_scores, 'details': condition_score.details, 'price_factor': condition_score.price_factor, 'timestamp': datetime.utcnow().isoformat(), 'agent_version': '2.0.0'}
        db.collection('users', user_id, 'condition_assessments').document(book_id).set(assessment_data)
        update_book(user_id, book_id, {'status': 'condition_assessed', 'ai_condition_grade': condition_score.grade.value, 'ai_condition_score': condition_score.overall_score, 'condition_assessed_at': datetime.utcnow().isoformat(), 'price_factor': condition_score.price_factor})
        
        # Robust update of request status
        try:
            if request_ref.get().exists:
                request_ref.update({'status': 'completed'})
                logger.info(f"✅ Request status updated to 'completed'")
            else:
                logger.warning(f"⚠️ Request document not found, skipping status update: {book_id}")
        except Exception as e:
            logger.error(f"Error updating request status: {e}")

        # Extract image URLs for the completion event
        image_urls = [img.get('gcs_uri') or img.get('imageUrl') for img in images]
        await publish_completion_event(user_id, book_id, image_urls)
    except Exception as e:
        logger.error(f"Error: {e}")
        try:
            if request_ref.get().exists:
                request_ref.update({'status': 'failed', 'error': str(e)})
        except: pass
        update_book(user_id, book_id, {'status': 'condition_failed', 'error_message': str(e)})

async def publish_completion_event(user_id: str, book_id: str, image_urls: List[str] = None) -> None:
    if not PROJECT_ID:
        logger.error("❌ No PROJECT_ID found, cannot publish completion event!")
        return
    # Updated topic to trigger Strategist Agent explicitly
    topic_path = publisher.topic_path(PROJECT_ID, 'condition-assessment-completed')
    message = {
        'bookId': book_id,
        'uid': user_id,
        'status': 'condition_assessed',
        'imageUrls': image_urls or [],
        'timestamp': datetime.utcnow().isoformat()
    }
    try:
        publisher.publish(topic_path, data=json.dumps(message).encode('utf-8')).result()
        logger.info(f"📤 Published completion event for {book_id} to topic 'condition-assessment-completed'")
    except Exception as e:
        logger.error(f"❌ Failed to publish: {e}")
