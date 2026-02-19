"""
Core-Logik für die Simplified Book Ingestion Pipeline.

Hauptfunktionen:
- prepare_images(): Lädt und konvertiert Bilder für Gemini
- ingest_book_with_gemini(): Hauptfunktion für Gemini API Call
- extract_grounding_metadata(): Extrahiert Grounding-Daten
- Retry Logic mit exponential backoff
"""

import os
import json
import re
import time
import logging
import datetime
from pathlib import Path
from typing import List, Optional, Any
import asyncio
from urllib.parse import urlparse, unquote

try:
    from google.cloud import storage
except ImportError:
    storage = None

try:
    from google import genai
    from google.genai import types
except ImportError:
    raise ImportError(
        "google-genai is required. Install with: pip install 'google-genai>=0.3.0'"
    )

import requests
from io import BytesIO

from .models import (
    BookIngestionRequest,
    BookIngestionResult,
    BookData,
    GroundingMetadata,
    IngestionError,
)
from .config import (
    SYSTEM_INSTRUCTIONS,
    TASK_PROMPT_TEMPLATE,
    JSON_RESPONSE_SCHEMA,
    IngestionConfig,
    DEFAULT_CONFIG,
)

# Logging Setup
logger = logging.getLogger(__name__)

# ============================================================================
# GENAI INITIALIZATION (bei Modul-Import)
# ============================================================================

def get_required_env(key: str) -> str:
    """Holt eine Umgebungsvariable oder wirft einen Fehler, wenn sie fehlt."""
    value = os.environ.get(key)
    if not value:
        raise RuntimeError(f"CRITICAL: Environment variable '{key}' is not set.")
    return value

try:
    project_id = get_required_env("GCP_PROJECT")
    location = os.environ.get("GCP_REGION", "europe-west1") # Region kann optional bleiben mit Default
    
    # google-genai SDK für Vertex AI konfigurieren
    client = genai.Client(
        vertexai=True,
        project=project_id,
        location=location,
    )
    logger.info(f"Google GenAI SDK for Vertex AI initialized successfully (project={project_id}, location={location})")
except Exception as e:
    logger.critical(f"Failed to initialize Google GenAI SDK: {e}")
    # Fail fast: Ohne LLM läuft hier nichts
    raise


# ============================================================================
# CUSTOM EXCEPTION
# ============================================================================

class IngestionException(Exception):
    """Benutzerdefinierte Exception für Ingestion-Fehler."""
    def __init__(self, error: IngestionError):
        self.error = error
        super().__init__(f"{error.error_type}: {error.error_message}")


# ============================================================================
# IMAGE PREPARATION
# ============================================================================

def prepare_images(image_urls: List[str]) -> List[types.Part]:
    """
    Bereitet Bilder für Gemini vor.
    
    Unterstützt:
    - URLs (http://, https://)
    - Cloud Storage URLs (gs://)
    - Lokale Dateien (file://, oder direkter Pfad)
    
    Args:
        image_urls: Liste von Bild-URLs oder Pfaden
        
    Returns:
        Liste von genai Part-Objekten
        
    Raises:
        ValueError: Wenn keine gültigen Bilder geladen werden konnten
    """
    parts = []
    
    for url in image_urls:
        try:
            if url.startswith('gs://'):
                logger.debug(f"Loading Cloud Storage image: {url}")
                parts.append(types.Part.from_uri(file_uri=url, mime_type="image/jpeg"))
                logger.info(f"Successfully loaded image from GCS: {url}")
            
            elif url.startswith(('http://', 'https://')):
                logger.debug(f"Downloading image from URL: {url}")
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                parts.append(types.Part.from_bytes(data=response.content, mime_type="image/jpeg"))
                logger.info(f"Successfully loaded image from URL: {url}")
            
            elif url.startswith('file://'):
                # Extrahiere Pfad aus file:// URL
                path_str = url.replace('file://', '')
                # Behandle /D:/... Format auf Windows
                if os.name == 'nt' and path_str.startswith('/'):
                    path_str = path_str[1:]
                
                # Unquote URL-encoded spaces etc.
                path_str = unquote(path_str)
                
                path = Path(path_str)
                # Fallback: Wenn Pfad nicht existiert, versuche absolut im Workspace
                if not path.exists():
                    # Workspace Root ist d:/Neuer Ordner laut environment_details
                    workspace_root = Path('d:/Neuer Ordner')
                    # Wenn path_str mit / beginnt, entferne ihn für join
                    join_path = path_str[1:] if path_str.startswith('/') else path_str
                    path = workspace_root / join_path

                logger.debug(f"Loading local image: {path}")
                
                if not path.exists():
                    logger.warning(f"File not found: {path}")
                    continue
                
                with open(path, 'rb') as f:
                    image_bytes = f.read()
                parts.append(types.Part.from_bytes(data=image_bytes, mime_type="image/jpeg"))
                logger.info(f"Successfully loaded local image: {path}")
            
            else:
                logger.warning(f"Unbekanntes URL-Format: {url}")
        
        except requests.RequestException as e:
            logger.error(f"Fehler beim Download von {url}: {e}")
        except Exception as e:
            logger.error(f"Fehler beim Laden von {url}: {e}")
    
    if not parts:
        raise ValueError("Keine gültigen Bilder gefunden")
    
    logger.info(f"Successfully prepared {len(parts)} images")
    return parts


# ============================================================================
# GROUNDING METADATA EXTRACTION
# ============================================================================

def extract_grounding_metadata(response: Any) -> GroundingMetadata:
    """
    Extrahiert Grounding Metadata aus Gemini Response.
    
    Args:
        response: Gemini API Response Objekt
        
    Returns:
        GroundingMetadata mit Search-Informationen
    """
    metadata = GroundingMetadata()
    try:
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            
            # Prüfe auf 'grounding_metadata' im Candidate (neues SDK Verhalten)
            if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                 # Hier könnten wir noch mehr extrahieren, aber das Objekt ist komplex
                 pass
            
            # Das Attribut heißt oft 'grounding_attributions' oder 'citation_metadata'
            # Wir prüfen beides für Robustheit
            attributions = None
            if hasattr(candidate, 'grounding_attributions') and candidate.grounding_attributions:
                 attributions = candidate.grounding_attributions
            elif hasattr(candidate, 'citation_metadata') and candidate.citation_metadata:
                 if hasattr(candidate.citation_metadata, 'citation_sources'):
                     attributions = candidate.citation_metadata.citation_sources

            if attributions:
                metadata.search_active = True
                for attr in attributions:
                    uri = None
                    if hasattr(attr, 'web') and hasattr(attr.web, 'uri'):
                        uri = attr.web.uri
                    elif hasattr(attr, 'uri'):
                        uri = attr.uri
                    
                    if uri:
                        metadata.source_urls.append(uri)
                        
                if metadata.source_urls:
                    metadata.queries_used = ["Google Search was used (query not available)"]
                    
    except Exception as e:
        logger.error(f"Error extracting grounding metadata: {e}", exc_info=True)
    return metadata


# ============================================================================
# MAIN INGESTION FUNCTION
# ============================================================================

async def ingest_book_with_gemini(
    request: BookIngestionRequest,
    config: Optional[IngestionConfig] = None,
    system_instructions: Optional[str] = None,
    task_prompt: Optional[str] = None
) -> BookIngestionResult:
    """
    HAUPTFUNKTION: Führt die komplette Ingestion mit einem Gemini-Call durch.
    
    Pipeline:
    1. Initialisiere Gemini Client (falls noch nicht geschehen)
    2. Lade und bereite Bilder vor
    3. Führe EINEN Gemini API Call mit Google Search Grounding durch (wenn aktiviert)
    4. Parse JSON Response
    5. Extrahiere Grounding Metadata
    6. Konstruiere und validiere Result
    
    Args:
        request: BookIngestionRequest mit book_id, user_id, image_urls
        config: Optional IngestionConfig (nutzt DEFAULT_CONFIG wenn None)
        system_instructions: Optional System Instructions (nutzt SYSTEM_INSTRUCTIONS wenn None)
        task_prompt: Optional Task Prompt (nutzt TASK_PROMPT_TEMPLATE wenn None)
    
    Returns:
        BookIngestionResult mit allen Metadaten
        
    Raises:
        IngestionError: Bei Fehlern während der Verarbeitung
    """
    start_time = time.time()
    
    if config is None:
        config = DEFAULT_CONFIG
    if system_instructions is None:
        system_instructions = SYSTEM_INSTRUCTIONS
    if task_prompt is None:
        task_prompt = TASK_PROMPT_TEMPLATE
    
    # Force explicit JSON request in prompt if grounding is enabled
    # Since we can't use response_mime_type="application/json" with tools
    if config.enable_grounding:
        task_prompt += "\n\nWICHTIG: Antworte AUSSCHLIESSLICH mit einem validen JSON-Objekt. Kein Markdown, kein erklärender Text davor oder danach. Nur das rohe JSON."
    
    try:
        # 1. Bilder vorbereiten
        logger.info(
            f"Processing book {request.book_id}: Loading {len(request.image_urls)} images"
        )
        image_parts = prepare_images(request.image_urls)
        
        # 3. Model konfigurieren
        model_name = config.model
        grounding_enabled = config.enable_grounding
        logger.info(f"Generation Config: Model={model_name}, SearchGrounding={grounding_enabled}")
        
        # 4. Generation Config
        # WICHTIG: Controlled Generation (response_schema) und Google Search Grounding 
        # können momentan nicht gleichzeitig genutzt werden.
        if grounding_enabled:
            logger.info("⚠️ Grounding is enabled: Disabling response_schema/mime_type to avoid API conflict.")
            generate_content_config = types.GenerateContentConfig(
                temperature=config.temperature,
                max_output_tokens=config.max_output_tokens,
                tools=[types.Tool(google_search=types.GoogleSearch())],
                system_instruction=system_instructions,
                safety_settings=[
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                        threshold=types.HarmBlockThreshold.BLOCK_NONE,
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                        threshold=types.HarmBlockThreshold.BLOCK_NONE,
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                        threshold=types.HarmBlockThreshold.BLOCK_NONE,
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        threshold=types.HarmBlockThreshold.BLOCK_NONE,
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_CIVIC_INTEGRITY,
                        threshold=types.HarmBlockThreshold.BLOCK_NONE,
                    ),
                ]
            )
        else:
            generate_content_config = types.GenerateContentConfig(
                temperature=config.temperature,
                max_output_tokens=config.max_output_tokens,
                response_mime_type="application/json",
                response_schema=JSON_RESPONSE_SCHEMA,
                system_instruction=system_instructions,
                safety_settings=[
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH,
                        threshold=types.HarmBlockThreshold.BLOCK_NONE,
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                        threshold=types.HarmBlockThreshold.BLOCK_NONE,
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                        threshold=types.HarmBlockThreshold.BLOCK_NONE,
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                        threshold=types.HarmBlockThreshold.BLOCK_NONE,
                    ),
                    types.SafetySetting(
                        category=types.HarmCategory.HARM_CATEGORY_CIVIC_INTEGRITY,
                        threshold=types.HarmBlockThreshold.BLOCK_NONE,
                    ),
                ]
            )
        
        # 6. Content zusammenstellen (Bilder + Prompt)
        contents = image_parts + [task_prompt]
        
        # 7. API Call durchführen
        logger.debug(f"Making Google GenAI API call with {len(image_parts)} images")
        
        try:
            # Stellen Sie sicher, dass client initialisiert ist (Fallback)
            local_client = client
            if local_client is None:
                 raise ValueError("Google GenAI Client is not initialized.")

            response = local_client.models.generate_content(
                model=config.model,
                contents=contents,
                config=generate_content_config
            )
            logger.info(f"📥 FULL GEMINI RESPONSE TYPE: {type(response)}")
            
        except Exception as e:
            logger.error(f"❌ API CALL FEHLER: {e}", exc_info=True)
            raise e
        
        # 7. Response parsen (Logik aus main.py übernommen und verbessert)
        logger.info("🔍 Parsing: Extrahiere Text aus Response...")
        
        if hasattr(response, 'candidates') and response.candidates:
            cand = response.candidates[0]
            logger.info(f"📊 Candidate 0 Finish Reason: {getattr(cand, 'finish_reason', 'N/A')}")
            
            # Log Candidate-Struktur
            if hasattr(cand, 'content'):
                logger.info(f"📊 Candidate has content: {hasattr(cand.content, 'parts')}")
                if hasattr(cand.content, 'parts') and cand.content.parts:
                    logger.info(f"📊 Number of parts: {len(cand.content.parts)}")

        result_text = ""
        try:
            result_text = response.text
        except Exception as e:
            if hasattr(response, 'candidates') and response.candidates and \
               response.candidates[0].content and response.candidates[0].content.parts:
                for part in response.candidates[0].content.parts:
                    if hasattr(part, 'text') and part.text:
                        result_text = part.text
                        break
        
        if not result_text or not result_text.strip():
            logger.error("❌ Keine Text-Antwort von Gemini erhalten")
            # Fallback JSON um Crash zu verhindern
            raise json.JSONDecodeError("Leere Antwort von Gemini", "", 0)

        logger.info(f"📝 Result Text (first 500 chars): {result_text[:500]}")
        
        # JSON Parsing: Robustere Logik für "Chatty" Models
        try:
            result_json = None
            
            # Strategie 1: Suche nach Markdown Code-Blöcken (z.B. ```json ... ```)
            # Wir nehmen den LETZTEN Block, da Modelle oft erst ein Beispiel zeigen und dann das Ergebnis.
            # Regex verbessert: Erlaubt optional json Tag, ignoriert Whitespace, non-greedy match für Inhalt
            code_block_pattern = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL | re.IGNORECASE)
            matches = code_block_pattern.findall(result_text)
            
            if matches:
                logger.info(f"🔍 Found {len(matches)} JSON code blocks.")
                # Versuche Blocks von hinten nach vorne zu parsen
                for json_str in reversed(matches):
                    try:
                        result_json = json.loads(json_str)
                        logger.info("✅ Valid JSON found in markdown code block (using last valid block)")
                        break
                    except json.JSONDecodeError:
                        continue
            
            # Strategie 2: Fallback - Suche alle JSON-Objekte im Rohtext
            if result_json is None:
                logger.info("⚠️ No valid code blocks found, scanning raw text for JSON objects...")
                decoder = json.JSONDecoder()
                idx = 0
                candidates = []
                
                while idx < len(result_text):
                    # Finde nächstes '{'
                    start_idx = result_text.find('{', idx)
                    if start_idx == -1:
                        break
                        
                    try:
                        obj, end_idx = decoder.raw_decode(result_text, start_idx)
                        candidates.append(obj)
                        idx = end_idx
                    except json.JSONDecodeError:
                        idx = start_idx + 1
                
                if candidates:
                    logger.info(f"🔍 Found {len(candidates)} JSON candidates in raw text.")
                    # Wir nehmen das letzte Objekt, da dies am wahrscheinlichsten das finale Ergebnis ist
                    result_json = candidates[-1]
                    logger.info("✅ Selected last valid JSON candidate from raw text")

            if result_json is None:
                raise json.JSONDecodeError("No valid JSON object found in response", result_text, 0)
                
            logger.info(f"📋 JSON Top-level keys: {list(result_json.keys())}")

        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON DECODE ERROR: {e}")
            logger.error(f"❌ Problematischer Text: {result_text}")
            raise e
        
        # 8. Grounding Metadata extrahieren
        grounding_metadata = extract_grounding_metadata(response)
        
        # 9. Result konstruieren
        book_data = None
        # Flexibles Parsing: Suche nach verschiedenen möglichen Keys
        possible_keys = ["book_data", "book", "book_identification", "data"]
        book_data_dict = None
        
        if isinstance(result_json, dict):
            # 1. Check for nested keys
            for key in possible_keys:
                if key in result_json:
                    book_data_dict = result_json[key]
                    logger.info(f"✅ Found book data using key: '{key}'")
                    break
            
            # 2. Check root-level structure (flat JSON)
            if not book_data_dict:
                # Prüfe auf 'metadata' key, den Gemini oft bei grounding nutzt
                if "metadata" in result_json and isinstance(result_json["metadata"], dict):
                    # Flatten: Merge metadata into root or use as base
                    logger.info("✅ Found 'metadata' key - attempting to restructure for BookData")
                    book_data_dict = result_json["metadata"]
                    # Kopiere Top-Level Felder wie 'confidence_score' in das book_data_dict
                    for k, v in result_json.items():
                        if k != "metadata" and k not in book_data_dict:
                            book_data_dict[k] = v
                
                # Prüfe ob Root selbst schon BookData ist (title/authors/isbn)
                elif "title" in result_json or "isbn" in result_json or "authors" in result_json:
                     book_data_dict = result_json
                     logger.info("✅ Using root JSON as book data (structure matches)")
        
        logger.info(f"🔍 Extracted book_data from result_json: {book_data_dict is not None}")
        
        if book_data_dict and isinstance(book_data_dict, dict):
            logger.info(f"📚 book_data keys: {list(book_data_dict.keys())}")
            if "metadata" not in book_data_dict:
                book_data_dict["metadata"] = {}
            book_data_dict["metadata"]["raw_gemini_response"] = result_json
            try:
                book_data = BookData(**book_data_dict)
                logger.info(f"✅ BookData successfully created with title: {book_data.title}")
            except Exception as ve:
                logger.error(f"❌ BookData Validation Error: {ve}", exc_info=True)
        else:
            logger.warning(f"⚠️ No valid book_data in result_json!")
            if isinstance(result_json, dict):
                logger.warning(f"⚠️ result_json keys: {list(result_json.keys())}")
        
        processing_time = (time.time() - start_time) * 1000
        
        # Der Erfolg hängt davon ab, ob wir Buchdaten extrahieren konnten
        ingestion_success = book_data is not None

        # --- CONFIDENCE EXTRACTION FIX ---
        confidence = 0.0
        if isinstance(result_json, dict):
            # 1. Versuche Top-Level Keys
            if "confidence" in result_json:
                confidence = float(result_json["confidence"])
            elif "confidence_score" in result_json:
                confidence = float(result_json["confidence_score"])
            # 2. Versuche im book_data_dict
            elif book_data_dict and isinstance(book_data_dict, dict):
                if "confidence" in book_data_dict:
                    confidence = float(book_data_dict["confidence"])
                elif "confidence_score" in book_data_dict:
                    confidence = float(book_data_dict["confidence_score"])
            
            # Sanity Check
            if confidence > 1.0: # Manchmal kommt 95 statt 0.95
                 confidence = confidence / 100.0
        
        logger.info(f"📊 Extracted Confidence: {confidence}")
        # -------------------------------
        
        # Result erstellen
        # WICHTIG: Nutze model_construct oder stelle sicher, dass BookData erkannt wird
        result = BookIngestionResult(
            success=ingestion_success,
            book_data=book_data,
            confidence=confidence,
            sources_used=result_json.get("sources_used", []) if isinstance(result_json, dict) else [],
            processing_time_ms=processing_time,
            grounding_metadata=grounding_metadata,
            timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
        
        logger.info(f"🎯 BookIngestionResult created - success: {result.success}, has_book_data: {result.book_data is not None}")
        
        return result
    
    except IngestionException as e:
        raise e
        
    except Exception as e:
        logger.error(f"Book {request.book_id}: Ingestion failed - {e}", exc_info=True)
        
        error_str = str(e).lower()
        retry_possible = any(
            keyword in error_str
            for keyword in ["rate", "limit", "quota", "503", "429", "timeout", "unavailable", "exhausted"]
        )
        
        raise IngestionException(IngestionError(
            error_type=type(e).__name__,
            error_message=str(e),
            book_id=request.book_id,
            user_id=request.user_id,
            retry_possible=retry_possible,
            gemini_error_code=str(getattr(e, 'code', '')),
            image_count=len(request.image_urls),
        ))


# ============================================================================
# RETRY LOGIC
# ============================================================================

async def ingest_book_with_retry(
    request: BookIngestionRequest,
    config: Optional[IngestionConfig] = None,
    max_retries: Optional[int] = None,
) -> BookIngestionResult:
    """
    Wrapper mit automatischem Retry bei transienten Fehlern.
    
    Nutzt exponential backoff für Retries.
    
    Args:
        request: BookIngestionRequest
        config: Optional IngestionConfig
        max_retries: Optional maximale Anzahl Retries (überschreibt config)
        
    Returns:
        BookIngestionResult
        
    Raises:
        IngestionError: Nach allen Retry-Versuchen
    """
    if config is None:
        config = DEFAULT_CONFIG
    
    if max_retries is None:
        max_retries = config.retry_attempts
    
    last_error = None
    
    for attempt in range(max_retries + 1):
        try:
            result = await ingest_book_with_gemini(request, config)
            
            if attempt > 0:
                logger.info(
                    f"Book {request.book_id}: Succeeded on retry attempt {attempt}"
                )
            
            return result
        
        except IngestionException as e:
            last_error = e.error if hasattr(e, 'error') else IngestionError(
                error_type="UNKNOWN",
                error_message=str(e),
                book_id=request.book_id,
                user_id=request.user_id,
                retry_possible=False
            )
            
            if not last_error.retry_possible:
                logger.error(
                    f"Book {request.book_id}: Permanent error, no retry: {last_error.error_message}"
                )
                raise e
            
            if attempt >= max_retries:
                logger.error(
                    f"Book {request.book_id}: Max retries ({max_retries}) reached"
                )
                raise
            
            delay = config.retry_delay_seconds * (config.retry_exponential_base ** attempt)
            logger.warning(
                f"Book {request.book_id}: Transient error (attempt {attempt + 1}/{max_retries + 1}), "
                f"retrying in {delay:.1f}s: {last_error.error_message}"
            )
            
            await asyncio.sleep(delay)
    
    if last_error:
        raise IngestionException(last_error)
    else:
        raise IngestionException(IngestionError(
            error_type="UNKNOWN_ERROR",
            error_message="Max retries reached without clear error",
            book_id=request.book_id,
            user_id=request.user_id,
            retry_possible=False,
        ))
