"""
Simplified Book Ingestion Pipeline.

Eine radikal vereinfachte Buch-Ingestion Pipeline, die die komplexe
Multi-Step Pipeline durch EINEN einzigen Gemini 2.5 Pro Call ersetzt.

Features:
- Multimodal Image Analysis mit Gemini
- Google Search Grounding für aktuelle Marktdaten
- Structured Output mit JSON Schema
- Retry Logic mit exponential backoff
- Production-ready Error Handling

Main API:
    ingest_book_with_gemini(): Hauptfunktion für Gemini API Call
    ingest_book_with_retry(): Wrapper mit automatischem Retry
    BookIngestionRequest: Input Model
    BookIngestionResult: Output Model

Example:
    ```python
    from shared.simplified_ingestion import (
        ingest_book_with_gemini,
        BookIngestionRequest
    )
    
    # Create request
    request = BookIngestionRequest(
        book_id="abc123",
        user_id="user456",
        image_urls=["path/to/image1.jpg", "path/to/image2.jpg"]
    )
    
    # Run ingestion
    result = await ingest_book_with_gemini(request)
    
    # Check result
    if result.success and result.confidence >= 0.7:
        print(f"Book: {result.book_data.title}")
        print(f"Confidence: {result.confidence}")
    ```
"""

__version__ = "1.0.0"
__author__ = "BookScout Team"

# Core Functions
from .core import (
    ingest_book_with_gemini,
    ingest_book_with_retry,
    prepare_images,
    extract_grounding_metadata,
    IngestionException,
)

# Models
from .models import (
    BookIngestionRequest,
    BookIngestionResult,
    BookData,
    GroundingMetadata,
    IngestionError,
)

# Configuration
from .config import (
    IngestionConfig,
    DEFAULT_CONFIG,
    SYSTEM_INSTRUCTIONS,
    TASK_PROMPT_TEMPLATE,
    JSON_RESPONSE_SCHEMA,
)

# Public API
__all__ = [
    # Main functions
    "ingest_book_with_gemini",
    "ingest_book_with_retry",
    "prepare_images",
    "extract_grounding_metadata",
    
    "IngestionException",
    # Models
    "BookIngestionRequest",
    "BookIngestionResult",
    "BookData",
    "GroundingMetadata",
    "IngestionError",
    
    # Configuration
    "IngestionConfig",
    "DEFAULT_CONFIG",
    "SYSTEM_INSTRUCTIONS",
    "TASK_PROMPT_TEMPLATE",
    "JSON_RESPONSE_SCHEMA",
]