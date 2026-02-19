"""
Pydantic Models für die Simplified Book Ingestion Pipeline.

Diese Models definieren die Datenstrukturen für:
- Input: BookIngestionRequest
- Output: BookIngestionResult mit BookData
- Error: IngestionError
- Grounding: GroundingMetadata
"""

from pydantic import BaseModel, Field, field_validator, model_validator, BeforeValidator
from typing import List, Optional, Dict, Any, Union, Annotated
from datetime import datetime
import logging
import re
import json

logger = logging.getLogger(__name__)

# --- Validator Functions ---

def robust_int_validator(v: Any) -> Optional[int]:
    """Konvertiert Strings wie '1700-1899' oder 'Unbekannt' in Integer oder None."""
    if v is None:
        return None
    if isinstance(v, int):
        return v
    if isinstance(v, str):
        # Versuche "Unbekannt" etc. abzufangen
        if any(x in v.lower() for x in ['unbekannt', 'unknown', 'geschätzt', 'ca.', 'n.a']):
            # Suche trotzdem nach Zahlen, falls "ca. 1700"
            pass
        
        # Extrahiere erste Zahl
        match = re.search(r'\d+', v)
        if match:
            try:
                return int(match.group())
            except ValueError:
                return None
    return None

def robust_list_validator(v: Any) -> List[str]:
    """Konvertiert einzelne Strings in Listen und filtert 'Unbekannt'."""
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x) for x in v if x]
    if isinstance(v, str):
        if any(x in v.lower() for x in ['unbekannt', 'unknown', 'keine', 'none']):
            return []
        # Trenne Komma-Listen wie "History, Religion"
        if ',' in v:
            return [s.strip() for s in v.split(',')]
        return [v]
    return []

class BookIngestionRequest(BaseModel):
    """
    Input für die vereinfachte Ingestion.
    
    Attributes:
        book_id: Firestore Document ID
        user_id: User ID für Multi-Tenancy
        image_urls: Liste von Bild-URLs (max 10)
        session_id: Optional Session ID für Tracking
    """
    
    book_id: str = Field(..., description="Firestore Document ID")
    user_id: str = Field(..., description="User ID für Multi-Tenancy")
    image_urls: List[str] = Field(
        ..., 
        min_length=1, 
        max_length=10,
        description="Liste von Bild-URLs (max 10)"
    )
    session_id: Optional[str] = Field(None, description="Optional Session ID für Tracking")
    
    @field_validator('image_urls')
    @classmethod
    def validate_image_urls(cls, v: List[str]) -> List[str]:
        """Validiere dass alle URLs gültig sind."""
        if not v:
            raise ValueError("image_urls darf nicht leer sein")
        for url in v:
            if not url.startswith(('http://', 'https://', 'gs://', 'file://')):
                raise ValueError(f"Ungültige URL: {url}")
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "book_id": "abc123xyz",
                "user_id": "user_12345",
                "image_urls": [
                    "https://storage.googleapis.com/bucket/image1.jpg",
                    "https://storage.googleapis.com/bucket/image2.jpg"
                ],
                "session_id": "session_789"
            }
        }
    }


class BookData(BaseModel):
    """
    Komplette Buchdaten.
    
    Enthält alle Metadaten die aus den Buchbildern und Google Search extrahiert werden:
    - Basis-Identifikation (Titel, Autoren, ISBN)
    - Editions-Details (Verlag, Jahr, Auflage)
    - Kategorisierung (Genre, Kategorien)
    - Beschreibung und Cover
    - Marktdaten
    """
    
    # Basis-Identifikation
    title: Optional[str] = Field(None, description="Buchtitel")
    authors: List[str] = Field(default_factory=list, description="Liste der Autoren")
    isbn_13: Optional[str] = Field(None, description="ISBN-13")
    isbn_10: Optional[str] = Field(None, description="ISBN-10")
    
    # Editions-Details
    publisher: Optional[str] = Field(None, description="Verlag")
    
    publication_year: Annotated[Optional[int], BeforeValidator(robust_int_validator)] = Field(
        None, ge=1000, le=2100, description="Erscheinungsjahr"
    )
    
    edition: Optional[str] = Field(None, description="Edition/Auflage")
    binding_type: Optional[str] = Field(None, description="Einbandtyp (z.B. Hardcover, Taschenbuch, Leinen)")
    weight_grams: Optional[int] = Field(None, ge=0, description="Geschätztes Gewicht in Gramm")
    language: str = Field("de", description="Sprache (ISO 639-1 Code)")
    
    page_count: Annotated[Optional[int], BeforeValidator(robust_int_validator)] = Field(
        None, ge=1, description="Seitenzahl"
    )
    
    # Kategorisierung
    genre: Annotated[List[str], BeforeValidator(robust_list_validator)] = Field(
        default_factory=list, description="Genre/Gattung"
    )
    
    categories: Annotated[List[str], BeforeValidator(robust_list_validator)] = Field(
        default_factory=list, description="Kategorien"
    )
    
    # Beschreibung
    description: Optional[str] = Field(None, description="Buchbeschreibung")
    cover_url: Optional[str] = Field(None, description="URL zum Cover-Bild")
    
    # Debug / Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Zusätzliche Metadaten und Debug-Infos")
    
    @field_validator('publisher', 'edition', 'binding_type', mode='before')
    @classmethod
    def robust_string_conversion(cls, v: Any) -> Optional[str]:
        """
        Konvertiert komplexe Inputs (Dicts, Listen) robust in Strings.
        Gemini gibt manchmal Objekte zurück, wo Strings erwartet werden.
        """
        if v is None:
            return None
        if isinstance(v, str):
            return v
        if isinstance(v, (int, float)):
            return str(v)
        if isinstance(v, list):
            # Nimm das erste Element oder joine
            filtered = [str(x) for x in v if x]
            return ", ".join(filtered) if filtered else None
        if isinstance(v, dict):
            # Versuche typische Keys zu finden
            for key in ['name', 'value', 'text', 'content', 'label']:
                if key in v and v[key]:
                    return str(v[key])
            # Fallback: JSON String
            try:
                return json.dumps(v, ensure_ascii=False)
            except:
                return str(v)
        return str(v)

    @field_validator('isbn_13')
    @classmethod
    def validate_isbn_13(cls, v: Optional[str]) -> Optional[str]:
        """Validiere ISBN-13 Format."""
        if v is None:
            return v
        cleaned = v.replace('-', '').replace(' ', '')
        # Robustheit: Extrahiere nur Ziffern falls "ISBN: 978..." kommt
        cleaned = re.sub(r'\D', '', cleaned)
        
        if len(cleaned) != 13:
            logger.warning(f"Invalid ISBN-13 format: {v}")
            return None
        return cleaned
    
    @field_validator('isbn_10')
    @classmethod
    def validate_isbn_10(cls, v: Optional[str]) -> Optional[str]:
        """Validiere ISBN-10 Format."""
        if v is None:
            return v
        cleaned = v.replace('-', '').replace(' ', '')
        # Robustheit: Extrahiere nur Ziffern falls "ISBN: 3..." kommt
        # Achtung: ISBN-10 kann 'X' am Ende haben
        if cleaned.endswith('X') or cleaned.endswith('x'):
            digits = re.sub(r'\D', '', cleaned[:-1])
            cleaned = digits + 'X'
        else:
             cleaned = re.sub(r'\D', '', cleaned)

        if len(cleaned) != 10:
            logger.warning(f"Invalid ISBN-10 format: {v}")
            return None
        return cleaned


class GroundingMetadata(BaseModel):
    """
    Metadata über Google Search Grounding.
    """
    search_active: bool = Field(False, description="Ob Google Search aktiv war")
    queries_used: List[str] = Field(default_factory=list, description="Verwendete Suchanfragen")
    source_urls: List[str] = Field(default_factory=list, description="Verwendete Quellen-URLs")


def find_and_extract_book_data(data: Union[Dict, Any]) -> Optional[Dict]:
    """
    Sucht rekursiv nach 'book_identification' oder 'book_data' in einem Dict.
    """
    if not isinstance(data, dict):
        return None

    for key, value in data.items():
        if key in ("book_identification", "book_data"):
            if isinstance(value, dict):
                return value
        
        if isinstance(value, dict):
            result = find_and_extract_book_data(value)
            if result:
                return result
    return None

class BookIngestionResult(BaseModel):
    """
    Output der vereinfachten Ingestion.
    """
    success: bool = Field(..., description="Ob die Identifikation erfolgreich war")
    book_data: Optional[BookData] = Field(None, description="Extrahierte Buchdaten")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence Score")
    sources_used: List[str] = Field(default_factory=list, description="Verwendete Quellen")
    processing_time_ms: float = Field(..., ge=0, description="Verarbeitungszeit in ms")
    grounding_metadata: GroundingMetadata = Field(
        default_factory=GroundingMetadata,
        description="Google Search Grounding Metadata"
    )
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Zeitstempel")

    @model_validator(mode='before')
    @classmethod
    def flatten_gemini_response(cls, data: Any) -> Any:
        """
        Versucht, die verschachtelte Gemini-Antwort zu normalisieren,
        bevor die eigentliche Validierung stattfindet.
        """
        if not isinstance(data, dict):
            return data

        # WICHTIG: Wenn book_data bereits ein BookData Objekt ist (von model_construct oder manueller Instanziierung),
        # dann NICHT überschreiben oder neu parsen!
        if 'book_data' in data and isinstance(data['book_data'], BookData):
            # logger.info("✅ book_data ist bereits ein BookData Objekt - überspringe Validierung")
            return data

        logger.debug(f"BookIngestionResult Rohdaten: {data}")

        # Wenn book_data bereits existiert, aber nicht das richtige Format hat
        if 'book_data' in data and not isinstance(data['book_data'], dict):
             if data['book_data'] is not None:
                logger.warning(f"⚠️ book_data hat unerwarteten Typ: {type(data['book_data'])}")
             # Setze es auf None, damit es später evtl. gefunden wird
             data['book_data'] = None

        # Wenn book_data nicht existiert oder None ist, suche danach
        if not data.get('book_data'):
            extracted_data = find_and_extract_book_data(data)
            if extracted_data:
                logger.info(f"Buchdaten extrahiert aus verschachtelter Antwort: {extracted_data}")
                data['book_data'] = extracted_data
            else:
                logger.warning("Konnte 'book_data' oder 'book_identification' nicht in der Antwort finden.")
        
        return data

    @field_validator('confidence')
    @classmethod
    def validate_confidence(cls, v: float, info) -> float:
        """Warnung bei unrealistischen Confidence-Werten."""
        if v > 0.98:
            logger.warning(f"Ungewöhnlich hohe Confidence: {v:.3f}")
        elif v < 0.3 and info.data.get('success', False):
            logger.warning(f"Erfolg mit niedriger Confidence: {v:.3f}")
        return v
    
    def needs_review(self, threshold: float = 0.7) -> bool:
        """
        Prüft ob manuelle Review nötig ist.
        """
        return self.confidence < threshold
    
    def get_firestore_status(self, threshold: float = 0.7) -> str:
        """
        Gibt den Firestore Status zurück.
        """
        return "ingested" if self.confidence >= threshold else "needs_review"


class IngestionError(BaseModel):
    """
    Fehler während der Ingestion.
    """
    error_type: str = Field(..., description="Fehler-Typ (z.B. API_ERROR, VALIDATION_ERROR)")
    error_message: str = Field(..., description="Detaillierte Fehlermeldung")
    book_id: str = Field(..., description="Betroffene Buch-ID")
    user_id: str = Field(..., description="Betroffene User-ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Zeitstempel")
    retry_possible: bool = Field(True, description="Ob ein Retry sinnvoll ist")
    
    gemini_error_code: Optional[str] = Field(None, description="Gemini API Error Code")
    grounding_failed: bool = Field(False, description="Ob Grounding fehlgeschlagen ist")
    image_count: int = Field(0, ge=0, description="Anzahl der verarbeiteten Bilder")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "error_type": "API_RATE_LIMIT",
                "error_message": "Gemini API rate limit exceeded",
                "book_id": "abc123",
                "user_id": "user_456",
                "retry_possible": True,
                "gemini_error_code": "429",
                "grounding_failed": False,
                "image_count": 3
            }
        }
    }
