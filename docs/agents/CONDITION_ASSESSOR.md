# Condition Assessor Agent - Technische Dokumentation

**Version:** 2.0.0 (GenAI Refactor)  
**Status:** ✅ DEPLOYED  
**Letztes Update:** 21. Dezember 2024  
**Agent-Datei:** [`agents/condition-assessor/main.py`](../../agents/condition-assessor/main.py)

---

## 📋 Übersicht & Zweck

Der **Condition Assessor Agent** ist ein spezialisierter KI-Agent zur professionellen Zustandsbewertung von Büchern nach internationalen ABAA/ILAB-Standards. Er analysiert Buchbilder holistisch unter Verwendung des **Google Generative AI SDK (GenAI)** mit **Gemini 1.5 Pro** und liefert strukturierte Bewertungen mit Zustandsgraden, Defekt-Beschreibungen und Preisfaktoren.

### Hauptfunktionen

- ✅ **Multi-Image Holistic Analysis:** Analysiert alle Bilder eines Buches gemeinsam für konsistente Bewertung
- ✅ **ABAA/ILAB Standard Grading:** Professionelle Grades von "Fine" bis "Poor"
- ✅ **Detaillierte Komponenten-Bewertung:** Cover, Spine, Pages, Binding einzeln bewertet
- ✅ **Defekt-Erkennung:** Automatische Identifizierung von Stains, Tears, Foxing, Sunning, etc.
- ✅ **Preisfaktor-Berechnung:** Condition-adjustierter Multiplikator (0.1-1.0) für Pricing
- ✅ **Strukturiertes JSON Output:** Frontend-kompatibles Format für nahtlose Integration

---

## 🏗️ Technische Architektur

### Deployment-Konfiguration

```yaml
Service Type: Cloud Function (2nd Gen)
Runtime: Python 3.11
Region: europe-west1
Memory: 2GB
Timeout: 540s (9 Minuten)
Min Instances: 0 (Cost-optimiert)
Max Instances: 10
Trigger: Pub/Sub Topic "trigger-condition-assessment"
```

### GenAI SDK Integration

**Entscheidung: System API Key statt User LLM Manager**

Der Condition Assessor nutzt bewusst **NICHT** den User LLM Manager, sondern einen **System-Level GEMINI_API_KEY**:

**Rationale:**

1. **Konsistenz:** Alle Nutzer erhalten gleich qualitative Assessments
2. **Reliability:** Keine Abhängigkeit von User-Credentials oder Budget-Limits
3. **Cost Transparency:** Systemkosten klar dem Condition Assessment-Feature zugeordnet
4. **Performance:** Keine zusätzliche Komplexität durch Provider-Switching

**Implementation:**

```python
# Zeile 46-54 in main.py
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables")
genai.configure(api_key=GEMINI_API_KEY)
```

### Modell-Wahl: Gemini 1.5 Pro

**Model:** `gemini-1.5-pro`  
**Temperatur:** 0.1 (Niedrig für analytische Konsistenz)

**Vorteile:**
- Exzellente Vision-Capabilities für Multi-Image-Analyse
- Balance zwischen Qualität, Speed und Kosten
- Native JSON-Mode Support (`response_mime_type: "application/json"`)
- Kontextfenster: 1M Tokens (wichtig für Multiple Images)

**Alternative evaluiert:**
- `gemini-1.5-flash`: Zu schnell, geringere Analyse-Tiefe
- `gemini-1.5-pro-002`: Neuere Version, aber noch nicht stabil genug für Production

---

## 🔄 Trigger-Mechanismus: Pub/Sub Pipeline

### Workflow-Übersicht

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. INGESTION AGENT                                               │
│    - Buch erfolgreich analysiert (Status: "analyzed")           │
│    - Pub/Sub Message publishen                                   │
└─────────────────────────────────────────────────────────────────┘
                             │
                             │ Pub/Sub Topic: "trigger-condition-assessment"
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ 2. CONDITION ASSESSOR AGENT (Cloud Function Trigger)            │
│    - @functions_framework.cloud_event                           │
│    - Empfängt CloudEvent von Pub/Sub                            │
└─────────────────────────────────────────────────────────────────┘
                             │
                             │ Async Processing
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ 3. ASSESSMENT PIPELINE                                           │
│    - Bilder von GCS laden                                        │
│    - GenAI Vision Analyse                                        │
│    - Komponenten-Scoring                                         │
│    - Grade & Price Factor berechnen                             │
└─────────────────────────────────────────────────────────────────┘
                             │
                             │ Firestore Update
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│ 4. RESULT STORAGE                                                │
│    - users/{userId}/condition_assessments/{bookId}              │
│    - users/{userId}/books/{bookId} (Status Update)              │
└─────────────────────────────────────────────────────────────────┘
```

### Pub/Sub Message Format

**Topic:** `trigger-condition-assessment`

**Message Payload:**
```json
{
  "book_id": "abc123",
  "user_id": "user456",
  "image_urls": [
    "gs://bucket-name/users/user456/books/abc123/image1.jpg",
    "gs://bucket-name/users/user456/books/abc123/image2.jpg"
  ],
  "metadata": {
    "title": "Book Title",
    "year": "1950",
    "publisher": "Publisher Name"
  }
}
```

**Trigger-Code im Ingestion Agent:**

```python
# agents/ingestion-agent/main.py:131-143
if publisher and topic_path:
    payload = {
        "book_id": book_id,
        "user_id": uid,
        "image_urls": image_urls,
    }
    data = json.dumps(payload).encode("utf-8")
    future = publisher.publish(topic_path, data)
    future.result()  # Wait for publish
    logger.info(f"Published condition assessment job for book {book_id}")
```

---

## 📊 Assessment Pipeline

### Pipeline-Stufen

#### 1. Image Preparation (`_prepare_images`)

```python
async def _prepare_images(images: List[Dict]) -> List[Image.Image]:
    """Fetch images from GCS and convert to PIL Images"""
```

**Prozess:**
- Unterstützt GCS URIs (`gs://...`) und Base64-Content
- Downloaded Bilder von Google Cloud Storage
- Konvertiert zu PIL Image Objects für GenAI SDK
- Error-Handling: Fehlerhafte Bilder werden übersprungen

**GCS Download:**
```python
# Zeile 189-208
bucket_name, blob_name = gcs_uri.replace("gs://", "").split("/", 1)
bucket = storage_client.bucket(bucket_name)
blob = bucket.blob(blob_name)
image_bytes = blob.download_as_bytes()
pil_image = Image.open(BytesIO(image_bytes))
```

#### 2. Prompt Construction (`_construct_prompt`)

**Persona:** "Expert antiquarian bookseller and professional book condition grader"

**Prompt-Struktur:**
```
1. System Role Definition
2. Book Context (Optional Metadata)
3. Analysis Tasks:
   - Analyze ALL images collectively
   - Identify components (Cover, Spine, Pages, Binding)
   - Detect specific defects
   - Determine ABAA grade
   - Assign numerical score
   - Estimate price factor
4. JSON Schema Definition (Strict)
```

**JSON Schema:**
```json
{
  "grade": "Fine|Very Fine|Good|Fair|Poor",
  "score": 0-100,
  "price_factor": 0.1-1.0,
  "confidence": 0.0-1.0,
  "summary": "concise professional summary",
  "defects": ["defect1", "defect2"],
  "components": {
    "cover": { "score": 0-100, "description": "..." },
    "spine": { "score": 0-100, "description": "..." },
    "pages": { "score": 0-100, "description": "..." },
    "binding": { "score": 0-100, "description": "..." }
  }
}
```

#### 3. LLM Inference

```python
# Zeile 133-146
model = genai.GenerativeModel(
    "gemini-1.5-pro",
    generation_config={
        "response_mime_type": "application/json",
        "temperature": 0.1,
    }
)
content = [prompt_text] + image_parts  # Text + Images
response = model.generate_content(content)
```

**Vorteile JSON Mode:**
- Garantiert valides JSON (kein Parsing-Fehler)
- Keine Markdown-Code-Blocks im Output
- Strukturierte Responses ohne Post-Processing

#### 4. Response Parsing (`_parse_llm_response`)

```python
def _parse_llm_response(response_text: str) -> ConditionScore
```

**Prozess:**
1. JSON dekodieren
2. Grade-String zu Enum mappen
3. Komponenten-Scores extrahieren
4. Details-Dictionary konstruieren
5. ConditionScore-Object zurückgeben

**Fallback bei Parsing-Fehler:**
```python
# Zeile 311-318
return ConditionScore(
    overall_score=0.0,
    grade=ConditionGrade.GOOD,  # Neutral default
    confidence=0.0,
    price_factor=0.5,
    details={'summary': 'Manual review required.'},
    component_scores={}
)
```

---

## 🗄️ Datenmodelle

### Condition Grades (Enum)

```python
class ConditionGrade(Enum):
    """ABAA/ILAB Standard Grades"""
    FINE = "Fine"              # 90-100% - Like new
    VERY_FINE = "Very Fine"    # 80-89%  - Light wear
    GOOD = "Good"              # 60-79%  - Moderate wear
    FAIR = "Fair"              # 40-59%  - Notable wear
    POOR = "Poor"              # 0-39%   - Significant damage
```

### Condition Score (Dataclass)

```python
@dataclass
class ConditionScore:
    overall_score: float          # 0-100 numerical score
    grade: ConditionGrade          # ABAA grade enum
    confidence: float              # 0.0-1.0 AI confidence
    details: Dict[str, Any]        # Flattened details für Frontend
    price_factor: float            # 0.1-1.0 pricing multiplier
    component_scores: Dict[str, float]  # Individual component scores
```

### Firestore Collections

#### Collection: `users/{userId}/condition_assessments/{bookId}`

**Dokument-Struktur:**
```json
{
  "book_id": "abc123",
  "uid": "user456",
  "overall_score": 75.0,
  "grade": "Good",
  "confidence": 0.85,
  "component_scores": {
    "cover": 80.0,
    "spine": 75.0,
    "pages": 70.0,
    "binding": 75.0
  },
  "details": {
    "summary": "Book shows moderate wear...",
    "defects_list": ["Minor yellowing", "Small spine crack"],
    "cover_defects": "Light scuffing on front cover",
    "spine_defects": "Small crack at bottom hinge",
    "pages_defects": "Slight yellowing throughout",
    "binding_defects": "Tight and secure"
  },
  "price_factor": 0.65,
  "timestamp": "2024-12-21T20:15:30.123Z",
  "agent_version": "2.0.0"
}
```

#### Collection: `users/{userId}/books/{bookId}` (Update)

**Felder hinzugefügt:**
```json
{
  "status": "condition_assessed",
  "ai_condition_grade": "Good",
  "ai_condition_score": 75.0,
  "condition_assessed_at": "2024-12-21T20:15:30.123Z",
  "price_factor": 0.65
}
```

#### Collection: `users/{userId}/condition_assessment_requests/{bookId}`

**Status-Tracking:**
```json
{
  "images": ["gs://..."],
  "status": "pending|processing|completed|failed",
  "timestamp": "...",
  "error": "..." // Falls failed
}
```

---

## ⚙️ Konfiguration

### Aktiv genutzte Environment Variables

```yaml
# Cloud Project (REQUIRED)
GOOGLE_CLOUD_PROJECT: "project-52b2fab8-15a1-4b66-9f3"

# GenAI API Key (REQUIRED)
GEMINI_API_KEY: "[System API Key from Secret Manager]"
```

### Legacy/Ungenutzte Variables (zu entfernen)

Die folgenden Variablen sind **NICHT mehr aktiv** und stammen aus der alten Vertex AI Vision API Implementation:

```yaml
# ❌ VERALTET - GenAI nutzt kein Location
VERTEX_AI_LOCATION: "europe-west1"

# ❌ VERALTET - GenAI nutzt gemini-1.5-pro (hardcoded)
CONDITION_MODEL_NAME: "imagetext@001"

# ❌ VERALTET - GenAI SDK verwendet keine Vision API Endpoints
VISION_API_ENDPOINT: "vision.googleapis.com"
VISION_API_VERSION: "v1"

# ❌ VERALTET - Agent-URLs sind durch Pub/Sub ersetzt
STRATEGIST_AGENT_URL: "https://..."
LIBRARIAN_AGENT_URL: "https://..."

# ❌ FALSCH - Richtiger Topic ist "trigger-condition-assessment"
PUBSUB_TOPIC: "condition-assessments"
```

### Konfigurierbare Thresholds (Optional, aktuell hardcoded)

Diese Werte sind aktuell im Code definiert, könnten aber als ENV Vars externalisiert werden:

```python
# Zeile 104
MODEL_NAME = "gemini-1.5-pro"
TEMPERATURE = 0.1

# Implizit im Prompt (Zeile 230-235)
GRADE_THRESHOLDS = {
    "FINE": (90, 100),
    "VERY_FINE": (80, 89),
    "GOOD": (60, 79),
    "FAIR": (40, 59),
    "POOR": (0, 39)
}
```

---

## 🚀 Deployment

### Build Configuration

**Datei:** [`cloudbuild.condition-assessor.yaml`](../../cloudbuild.condition-assessor.yaml)

```yaml
steps:
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
      - 'functions'
      - 'deploy'
      - 'condition-assessor'
      - '--gen2'
      - '--runtime=python311'
      - '--region=europe-west1'
      - '--source=agents/condition-assessor'
      - '--entry-point=assess_condition_handler'
      - '--trigger-topic=trigger-condition-assessment'
      - '--memory=2GB'
      - '--timeout=540s'
      - '--set-env-vars=GOOGLE_CLOUD_PROJECT=project-52b2fab8-15a1-4b66-9f3'
      - '--set-secrets=GEMINI_API_KEY=GEMINI_API_KEY:latest'
```

### Deployment-Befehle

**Via Cloud Build:**
```bash
gcloud builds submit --config=cloudbuild.condition-assessor.yaml
```

**Direkt (für Testing):**
```bash
cd agents/condition-assessor
gcloud functions deploy condition-assessor \
  --gen2 \
  --runtime=python311 \
  --region=europe-west1 \
  --source=. \
  --entry-point=assess_condition_handler \
  --trigger-topic=trigger-condition-assessment \
  --memory=2GB \
  --timeout=540s \
  --set-env-vars=GOOGLE_CLOUD_PROJECT=project-52b2fab8-15a1-4b66-9f3 \
  --set-secrets=GEMINI_API_KEY=GEMINI_API_KEY:latest
```

### Secret Management

**GEMINI_API_KEY Setup:**
```bash
# 1. Secret erstellen
echo -n "your-api-key-here" | gcloud secrets create GEMINI_API_KEY \
  --data-file=- \
  --replication-policy=automatic

# 2. Service Account Zugriff
gcloud secrets add-iam-policy-binding GEMINI_API_KEY \
  --member="serviceAccount:PROJECT_ID@appspot.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### Deployment-Verification

```bash
# 1. Function Status prüfen
gcloud functions describe condition-assessor --gen2 --region=europe-west1

# 2. Logs checken
gcloud functions logs read condition-assessor \
  --gen2 \
  --region=europe-west1 \
  --limit=50

# 3. Test-Message publishen
gcloud pubsub topics publish trigger-condition-assessment \
  --message='{"book_id":"test123","user_id":"testuser","image_urls":[]}'
```

---

## 🔍 Monitoring & Debugging

### Cloud Logging Queries

**Erfolgreiche Assessments:**
```
resource.type="cloud_function"
resource.labels.function_name="condition-assessor"
jsonPayload.message=~"Successfully assessed condition"
```

**Fehler:**
```
resource.type="cloud_function"
resource.labels.function_name="condition-assessor"
severity>=ERROR
```

**GenAI API Calls:**
```
resource.type="cloud_function"
resource.labels.function_name="condition-assessor"
jsonPayload.message=~"Sending request to gemini"
```

### Wichtige Log-Ausgaben

```python
# Zeile 122
logger.info(f"Starting GenAI condition assessment for {len(images)} images")

# Zeile 133
logger.info(f"Sending request to {self.model_name} with {len(image_parts)} images")

# Zeile 394
logger.info(f"Writing assessment to Firestore. User ID: {user_id}, Book ID: {book_id}")

# Zeile 410
logger.info(f"Successfully assessed condition for book {book_id}")
```

### Common Issues & Solutions

**1. "GEMINI_API_KEY not found"**
- **Ursache:** Secret nicht korrekt gemountet
- **Lösung:** Verify Secret Manager IAM permissions

**2. "Failed to process image"**
- **Ursache:** GCS URI invalid oder Blob nicht gefunden
- **Lösung:** Check image_urls in Pub/Sub Message

**3. "Failed to parse LLM JSON response"**
- **Ursache:** GenAI returnierte unexpected format (sehr selten mit JSON mode)
- **Lösung:** Fallback auf Manual Review triggern, Prompt überarbeiten

**4. "Pub/Sub message timeout"**
- **Ursache:** Verarbeitung dauert > 540s (z.B. 10+ hochauflösende Bilder)
- **Lösung:** Timeout erhöhen oder Image-Preprocessing implementieren

---

## 📈 Performance & Kosten

### Typische Processing-Zeiten

- **1 Bild:** ~3-5 Sekunden
- **3 Bilder:** ~8-12 Sekunden
- **5 Bilder:** ~15-20 Sekunden

### Kosten (Gemini 1.5 Pro)

**Pricing (Stand Dez 2024):**
- Input: $0.00125 / 1K tokens (Text) + $0.0025 / image
- Output: $0.005 / 1K tokens

**Beispiel-Kalkulation (3 Bilder):**
- Images: 3 × $0.0025 = $0.0075
- Input Text (Prompt): ~500 tokens = $0.0006
- Output Text (JSON): ~300 tokens = $0.0015
- **Total pro Assessment: ~$0.01**

### Optimierungsmöglichkeiten

1. **Image Preprocessing:** Resize zu max. 1024px für schnellere Verarbeitung
2. **Batch Processing:** Multiple Books parallel (aktuell nicht implementiert)
3. **Cache:** Condition Assessments für identische Image-Sets wiederverwenden
4. **Model Downgrade:** Gemini 1.5 Flash für unkritische Cases (3x günstiger)

---

## 🔗 Integration mit anderen Agents

### Upstream: Ingestion Agent

**Trigger:**
```python
# agents/ingestion-agent/main.py:131-143
publisher.publish(
    topic_path="trigger-condition-assessment",
    data=json.dumps({
        "book_id": book_id,
        "user_id": uid,
        "image_urls": image_urls
    })
)
```

### Downstream: Strategist Agent

**Verwendung der Condition Data:**
```python
# agents/strategist-agent/main.py (konzeptuell)
condition_data = get_condition_assessment(book_id)
base_price = calculate_base_price(book_data)
final_price = base_price * condition_data['price_factor']
```

**Beispiel:**
- Base Price: €50.00
- Condition Grade: "Good" → Price Factor: 0.65
- Final Price: €50.00 × 0.65 = €32.50

---

## 🧪 Testing

### Local Testing

```python
# agents/condition-assessor/main.py:419-447
if __name__ == "__main__":
    asyncio.run(test_condition_assessment())
```

**Setup für Local Testing:**
```bash
export GOOGLE_CLOUD_PROJECT="project-52b2fab8-15a1-4b66-9f3"
export GEMINI_API_KEY="your-test-key"
export GOOGLE_APPLICATION_CREDENTIALS="path/to/service-account.json"

python agents/condition-assessor/main.py
```

### Integration Test

**Test-Datei:** [`tests/test_condition_assessment_genai.py`](../../tests/test_condition_assessment_genai.py)

```bash
pytest tests/test_condition_assessment_genai.py -v
```

### Manual Pub/Sub Test

```bash
gcloud pubsub topics publish trigger-condition-assessment \
  --message='{
    "book_id": "test_book_123",
    "user_id": "test_user",
    "image_urls": [
      "gs://your-bucket/test-images/book1.jpg",
      "gs://your-bucket/test-images/book2.jpg"
    ],
    "metadata": {
      "title": "Test Book",
      "year": "1950"
    }
  }'
```

---

## 📚 Referenzen

### ABAA/ILAB Grading Standards

- [ABAA Book Condition Definitions](https://www.abaa.org/book-collecting/book-care/grading)
- [ILAB Standards and Practices](https://www.ilab.org/eng/documentation/32-condition_grades.html)

### Google GenAI SDK

- [Python SDK Documentation](https://ai.google.dev/api/python/google/generativeai)
- [Gemini Models Overview](https://ai.google.dev/models/gemini)
- [Vision Capabilities](https://ai.google.dev/gemini-api/docs/vision)

### Related Documentation

- [`AGENTS_DEEP_DIVE.md`](AGENTS_DEEP_DIVE.md) - Übersicht aller Agents
- [`TECHNICAL_ARCHITECTURE.md`](../current/TECHNICAL_ARCHITECTURE.md) - System-Architektur
- [`INGESTION_WORKFLOW_OVERVIEW.md`](../current/INGESTION_WORKFLOW_OVERVIEW.md) - Upstream Pipeline

---

**Dokumentation Version:** 1.0  
**Agent Version:** 2.0.0 (GenAI Refactor)  
**Deployment Status:** ✅ Production  
**Letzter Review:** 21. Dezember 2024

