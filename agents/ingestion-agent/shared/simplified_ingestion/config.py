"""
Konfiguration für die Simplified Book Ingestion Pipeline.

Enthält:
- System Instructions für Gemini
- Task Prompt Template
- JSON Response Schema
- Konfigurationsparameter
"""

from dataclasses import dataclass
from typing import Dict, Any


# ============================================================================
# SYSTEM INSTRUCTIONS (dauerhaft für alle Calls)
# ============================================================================

SYSTEM_INSTRUCTIONS = """
Du bist ein Experte für Bucherkennung und den deutschen Buchmarkt.

Deine Aufgabe:
Analysiere die bereitgestellten Buchbilder und nutze Google Search, um das Buch exakt zu identifizieren
und ALLE bibliografischen Metadaten zu extrahieren.

WICHTIG:
- KEINE Analyse von Zustand, Preisen oder Verfügbarkeit durchführen.
- Fokus liegt rein auf der korrekten Identifikation der Ausgabe (Metadaten).

Qualitätsstandards:
- Nutze Google Search zur Verifizierung der bibliografischen Daten (Existenz, Verlag, Jahr)
- Verifiziere Informationen mit mehreren Quellen
- Gib realistische Confidence-Scores (0.7-0.95 ist normal)
- Bei Unsicherheit: lieber "needs_review" als falsche Daten

Fokus Deutsche Märkte:
- Nutze Quellen wie DNB, eurobuch.de, Amazon.de, Thalia, ZVAB zur Verifizierung der Metadaten
- Deutsche Verlage und Ausgaben priorisieren
"""


# ============================================================================
# TASK PROMPT (pro Request)
# ============================================================================

TASK_PROMPT_TEMPLATE = """
Analysiere diese Buchbilder und extrahiere ALLE Metadaten.

Nutze Google Search um:
1. **Basis-Identifikation**
   - ISBN (wenn sichtbar)
   - Titel (exakt)
   - Autor(en)

2. **Editions-Details**
   - Welche Edition/Ausgabe? (Taschenbuch, Gebunden, Sonderausgabe)
   - Einbandtyp (z.B. Hardcover, Taschenbuch, Leinen, Broschiert)
   - Erscheinungsjahr dieser Edition
   - Verlag und Auflage
   - Besondere Merkmale (Cover-Variante, Extras)

3. **Zusätzliche Metadaten**
   - Genre/Kategorien
   - Seitenzahl
   - Geschätztes Gewicht in Gramm (basierend auf Format/Seitenzahl, z.B. 350)
   - Sprache
   - Beschreibung (kurz)
   - Cover-URL (falls verfügbar)

Analysiere die Bilder gründlich:
- Cover (Vorder- und Rückseite)
- Impressum (Copyright-Seite)
- Buchrücken

BITTE BEACHTEN:
- Ignoriere den Zustand des Buches.
- Suche NICHT nach Preisen oder Verfügbarkeit.
- Konzentriere dich ausschließlich auf die statischen Buch-Metadaten.

Gib das Ergebnis als JSON zurück (siehe Schema).
"""


# ============================================================================
# JSON RESPONSE SCHEMA (für Structured Output) - KORRIGIERT
# ============================================================================

JSON_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "success": {
            "type": "boolean",
            "description": "Ob die Identifikation erfolgreich war"
        },
        "book_data": {
            "type": "object",
            "nullable": True,
            "properties": {
                # Basis-Identifikation
                "title": {
                    "type": "string",
                    "description": "Buchtitel"
                },
                "authors": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Liste der Autoren"
                },
                "isbn_13": {
                    "type": "string",
                    "nullable": True,
                    "description": "ISBN-13"
                },
                "isbn_10": {
                    "type": "string",
                    "nullable": True,
                    "description": "ISBN-10"
                },
                
                # Editions-Details
                "publisher": {
                    "type": "string",
                    "nullable": True,
                    "description": "Verlag"
                },
                "publication_year": {
                    "type": "integer",
                    "nullable": True,
                    "description": "Erscheinungsjahr"
                },
                "edition": {
                    "type": "string",
                    "nullable": True,
                    "description": "Edition/Auflage"
                },
                "binding_type": {
                    "type": "string",
                    "nullable": True,
                    "description": "Einbandtyp (z.B. Hardcover, Taschenbuch)"
                },
                "weight_grams": {
                    "type": "integer",
                    "nullable": True,
                    "description": "Geschätztes Gewicht in Gramm"
                },
                "language": {
                    "type": "string",
                    "description": "Sprache (ISO 639-1)"
                },
                "page_count": {
                    "type": "integer",
                    "nullable": True,
                    "description": "Seitenzahl"
                },
                
                # Kategorisierung
                "genre": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Genre/Gattung"
                },
                "categories": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Kategorien"
                },
                
                # Beschreibung
                "description": {
                    "type": "string",
                    "nullable": True,
                    "description": "Buchbeschreibung"
                },
                "cover_url": {
                    "type": "string",
                    "nullable": True,
                    "description": "URL zum Cover-Bild"
                },
                
                # Marktdaten wurden entfernt
            },
            "required": ["title"]
        },
        
        # Confidence & Metadata
        "confidence": {
            "type": "number",
            "description": "Gesamte Confidence der Identifikation"
        },
        "sources_used": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Verwendete Quellen (z.B. Google Books, Amazon.de)"
        },
        "processing_time_ms": {
            "type": "number",
            "description": "Verarbeitungszeit in Millisekunden"
        },
        
        # Grounding Metadata
        "grounding_metadata": {
            "type": "object",
            "properties": {
                "search_active": {
                    "type": "boolean",
                    "description": "Ob Google Search aktiv war"
                },
                "queries_used": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Verwendete Suchanfragen"
                },
                "source_urls": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Verwendete Quellen-URLs"
                }
            }
        }
    },
    "required": ["success", "confidence"]
}


# ============================================================================
# CONFIGURATION DATACLASS
# ============================================================================

@dataclass
class IngestionConfig:
    """
    Konfiguration für die Simplified Ingestion Pipeline.
    
    Attributes:
        model: Gemini Model Name
        temperature: Temperature für Gemini (0.0 - 1.0)
        max_output_tokens: Maximale Anzahl Output Tokens
        confidence_threshold_ingested: Schwellenwert für "ingested" Status
        confidence_threshold_review: Schwellenwert für "needs_review" Status
        max_images: Maximale Anzahl Bilder pro Request
        enable_grounding: Ob Google Search Grounding aktiviert werden soll
        retry_attempts: Anzahl Retry-Versuche bei Fehlern
        retry_delay_seconds: Verzögerung zwischen Retries
    """
    
    # Gemini Configuration
    model: str = "gemini-2.0-flash-001"
    temperature: float = 0.1
    max_output_tokens: int = 4096
    
    # Confidence Thresholds
    confidence_threshold_ingested: float = 0.7
    confidence_threshold_review: float = 0.5
    
    # Image Processing
    max_images: int = 10
    
    # Google Search Grounding
    enable_grounding: bool = True
    
    # Retry Configuration
    retry_attempts: int = 3
    retry_delay_seconds: float = 2.0
    retry_exponential_base: float = 2.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Konvertiert Config zu Dictionary."""
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_output_tokens": self.max_output_tokens,
            "confidence_threshold_ingested": self.confidence_threshold_ingested,
            "confidence_threshold_review": self.confidence_threshold_review,
            "max_images": self.max_images,
            "enable_grounding": self.enable_grounding,
            "retry_attempts": self.retry_attempts,
            "retry_delay_seconds": self.retry_delay_seconds,
        }


# ============================================================================
# DEFAULT CONFIGURATION
# ============================================================================

DEFAULT_CONFIG = IngestionConfig()