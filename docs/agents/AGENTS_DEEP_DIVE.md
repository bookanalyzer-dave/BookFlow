# Agenten Deep Dive Dokumentation

Dieses Dokument bietet eine detaillierte technische Beschreibung der einzelnen Agenten und ihrer Interaktionen im System.

## Code-Qualität Standards

Alle Agenten folgen konsistenten Best Practices:

### Environment Variables Validation
Jeder Agent implementiert eine `validate_environment()` Funktion:
```python
def validate_environment() -> Dict[str, str]:
    """Validate required environment variables are set."""
    required_vars = {
        "GCP_PROJECT": os.environ.get("GCP_PROJECT"),
        # weitere kritische Variablen
    }
    
    missing = [key for key, value in required_vars.items() if not value]
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    logger.info(f"Environment validation passed for: {', '.join(required_vars.keys())}")
    return required_vars
```

### Type Hints
Alle Funktionen nutzen Python Type Hints:
```python
from typing import Dict, Any, Optional, List

async def process_data(data: Dict[str, Any], user_id: Optional[str] = None) -> Dict[str, Any]:
    """Process data with clear type signatures."""
    pass
```

### Imports & Code-Organisation
- Ungenutzte Imports wurden entfernt
- Konsistente Logging-Konfiguration in allen Agenten
- Klare Modularität und Trennung von Verantwortlichkeiten

---

## Gesamt-Workflow

Der Prozess von der Bilderfassung bis zum Verkauf ist eine hochautomatisierte Pipeline, die wie folgt abläuft:

1.  **Erfassung & Analyse (`ingestion-agent`):** Ein Benutzer lädt Bilder hoch. Der `ingestion-agent` startet seine "Intelligente Forschungs-Pipeline" unter Verwendung des System-Level Gemini API-Keys, um das Buch zu identifizieren, Metadaten anzureichern und eine Beschreibung zu generieren.
2.  **Qualitätssicherung (Human-in-the-Loop):** Basierend auf einem internen Konfidenz-Score wird das Buch entweder als `ingested` (bereit für den nächsten Schritt) oder `needs_review` markiert. Bücher, die eine Überprüfung benötigen, können vom Benutzer im Dashboard korrigiert und erneut durch die Pipeline geschickt werden.
3.  **Preisstrategie (`strategist-agent`):** Sobald ein Buch den Status `ingested` hat, berechnet der `strategist-agent` (unter Nutzung von Gemini Grounding) den optimalen Verkaufspreis.
4.  **Listing (`ambassador-agent`):** Nach erfolgreicher Preisberechnung sendet der `strategist-agent` automatisch eine Nachricht, die den `ambassador-agent` anstößt, das Buch auf den Zielplattformen (z.B. eBay) zu listen.
5.  **Verkaufsabwicklung (`sentinel`-System):** Bei einem Verkauf fängt das `sentinel`-System die Benachrichtigung ab, markiert das Buch als `sold` und sorgt dafür, dass es von allen anderen Plattformen entfernt wird.

---

## 1. Ingestion Agent (`ingestion-agent`)

-   **Zweck:** Identifiziert Bücher und reichert Metadaten an, indem Bilder analysiert und Fakten live recherchiert werden.
-   **Status:** ✅ DEPLOYED
-   **Technologie:** Gemini 2.5 Pro mit Search Grounding (via Shared Library).

> **Detaillierte Dokumentation:**
> Siehe [`INGESTION_AGENT.md`](INGESTION_AGENT.md) für die vollständige Referenz, Architektur und Konfiguration.

---


## 2. Strategist Agent (`strategist-agent`)

-   **Zweck:** Bestimmt eine dynamische Preisstrategie und **stößt den Listing-Prozess an**.
-   **Auslöser:** Pub/Sub-Nachricht `condition-assessment-completed`.
-   **Interaktionen:**
    -   **Gemini 2.0 Flash / Pro:** Nutzt Multimodal-Input (Bilder, Condition) und Google Search Tool für Live-Pricing.
    -   **Firestore:** Speichert `pricing` Objekt und `calculatedPrice`.
    -   **Pub/Sub:** **Nach erfolgreicher Preisberechnung** veröffentlicht der Agent eine Nachricht an das Thema `book-listing-requests`, um den `ambassador-agent` auszulösen.

---

## 3. Ambassador Agent (`ambassador-agent`)

-   **Zweck:** Fungiert als Schnittstelle zu externen Marktplätzen (z.B. eBay). Erstellt und löscht Produktangebote.
-   **Auslöser:** Pub/Sub-Nachricht im Thema `book-listing-requests` (gesendet vom `strategist-agent`) oder `delist-book-everywhere` (gesendet vom `sentinel-agent`). Alle Nachrichten verwenden `bookId` und `uid` als Identifier.
-   **Interaktionen:** Pub/Sub, Firestore, Externe Marktplatz-APIs.
-   **Architektur:** Nutzt eine `MarketplacePlatform`-Basisklasse für einfache Erweiterbarkeit.

---

## 4. Sentinel System (`sentinel-agent` & `sentinel-webhook`)

### 5.1. Sentinel Webhook (`sentinel-webhook`)

-   **Zweck:** Dient als sicherer Endpunkt für eingehende Verkaufsbenachrichtigungen von externen Plattformen.
-   **Auslöser:** HTTP `POST`-Request von einer externen Plattform.
-   **Funktionsweise:** Validiert die Anfrage und leitet sie zur asynchronen Verarbeitung an Pub/Sub weiter.

### 5.2. Sentinel Agent (`sentinel-agent`)

-   **Zweck:** Verarbeitet Verkaufsbenachrichtigungen, aktualisiert den Buchstatus und stößt das Delisting an.
-   **Auslöser:** Pub/Sub-Nachricht aus dem Thema `sale-notification-received`.
-   **Interaktionen:** Firestore, Pub/Sub.

---

## 5. Condition Assessor Agent (`condition-assessor`)

-   **Zweck:** Professionelle Zustandsbewertung von Büchern nach ABAA/ILAB-Standards mittels KI-gestützter Bildanalyse.
-   **Status:** ✅ DEPLOYED (Cloud Function Gen2)
-   **Auslöser:** Pub/Sub-Nachricht auf Topic `trigger-condition-assessment` (gesendet vom Ingestion Agent nach erfolgreicher Analyse).

### System-API-Key Architektur

**Design-Entscheidung:** Der Condition Assessor nutzt bewusst **NICHT** den User LLM Manager, sondern einen **System-Level GEMINI_API_KEY**.

**Rationale:**
1. **Konsistenz:** Alle Nutzer erhalten gleich qualitative Condition Assessments unabhängig von ihren eigenen API-Keys
2. **Reliability:** Keine Abhängigkeit von User-Credentials, Budget-Limits oder Provider-Verfügbarkeit
3. **Cost Transparency:** System-Kosten für Condition Assessment sind klar vom User-LLM-Verbrauch getrennt
4. **Simplified Architecture:** Keine zusätzliche Komplexität durch Provider-Switching-Logik

**Implementation:**
```python
# agents/condition-assessor/main.py:46-54
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)  # Google GenAI SDK
```

### Technische Details

-   **Model:** Gemini 1.5 Pro (`gemini-1.5-pro`)
-   **SDK:** Google Generative AI Python SDK (nicht Vertex AI!)
-   **Temperatur:** 0.1 (niedrig für analytische Konsistenz)
-   **Response Format:** Strukturiertes JSON via `response_mime_type: "application/json"`

### Pub/Sub Workflow

```
┌─────────────────────────────────────────────────────────────┐
│ 1. INGESTION AGENT                                          │
│    - Buch erfolgreich analysiert (Status: "analyzed")      │
│    - Publish auf Topic "trigger-condition-assessment"          │
└─────────────────────────────────────────────────────────────┘
                          │
                          ↓ Pub/Sub Message
┌─────────────────────────────────────────────────────────────┐
│ 2. CONDITION ASSESSOR AGENT                                 │
│    - @functions_framework.cloud_event Trigger              │
│    - Multi-Image Holistic Analysis mit Gemini 1.5 Pro     │
│    - ABAA/ILAB Grade Berechnung (Fine → Poor)             │
│    - Komponenten-Bewertung (Cover, Spine, Pages, Binding) │
│    - Preis-Faktor Ermittlung (0.1 - 1.0)                  │
└─────────────────────────────────────────────────────────────┘
                          │
                          ↓ Firestore Update
┌─────────────────────────────────────────────────────────────┐
│ 3. RESULT STORAGE                                           │
│    - users/{userId}/condition_assessments/{bookId}         │
│    - users/{userId}/books/{bookId} (Status Update)         │
└─────────────────────────────────────────────────────────────┘
```

### Assessment-Pipeline

1. **Image Preparation:** Lädt Bilder von GCS (`gs://...` URIs) und konvertiert zu PIL Images
2. **Prompt Construction:** "Expert antiquarian bookseller" Persona mit strukturiertem JSON-Schema
3. **GenAI Inference:** Multi-Image-Input an Gemini 1.5 Pro mit JSON-Mode
4. **Response Parsing:** Mapping zu `ConditionScore` Dataclass mit Grade-Enum

### Datenmodelle

**Condition Grades:**
```python
class ConditionGrade(Enum):
    FINE = "Fine"              # 90-100% - Like new
    VERY_FINE = "Very Fine"    # 80-89%  - Light wear
    GOOD = "Good"              # 60-79%  - Moderate wear
    FAIR = "Fair"              # 40-59%  - Notable wear
    POOR = "Poor"              # 0-39%   - Significant damage
```

**Firestore Output:**
```json
{
  "overall_score": 75.0,
  "grade": "Good",
  "confidence": 0.85,
  "component_scores": {
    "cover": 80.0,
    "spine": 75.0,
    "pages": 70.0,
    "binding": 75.0
  },
  "price_factor": 0.65,
  "details": {
    "summary": "Book shows moderate wear...",
    "defects_list": ["Minor yellowing", "Small spine crack"],
    "cover_defects": "...",
    "spine_defects": "...",
    "pages_defects": "...",
    "binding_defects": "..."
  }
}
```

### Interaktionen

-   **Upstream:** Ingestion Agent publisht Pub/Sub Message nach erfolgreicher Analyse
-   **Downstream:** Strategist Agent nutzt `price_factor` für Preisberechnung
-   **Storage:** Cloud Storage (Bilder), Firestore (Assessments)

### Detaillierte Dokumentation

Siehe [`CONDITION_ASSESSOR.md`](CONDITION_ASSESSOR.md) für:
- Vollständige Architektur-Details
- Deployment-Anleitung
- Konfiguration & Environment Variables
- Monitoring & Debugging
- Performance & Kosten-Analyse

---

## Entfernte Agenten

### Scribe Agent (Entfernt)
-   **Status:** ✅ Vollständig entfernt und in `ingestion-agent` integriert
-   **Grund:** Die Beschreibungserstellung ist jetzt Teil der Ingestion-Pipeline für bessere Kohärenz
-   **Migration:** Alle Funktionalität wurde in [`ingestion-agent/main.py`](agents/ingestion-agent/main.py) verschoben

### Scout Agent (Entfernt)
-   **Status:** ✅ Vollständig entfernt
-   **Grund:** Ersetzt durch Gemini 2.0 Flash mit Google Search Tool im Strategist Agent (Simplification).
-   **Migration:** Funktionalität ist nun Teil von [`agents/strategist-agent/main.py`](agents/strategist-agent/main.py).
