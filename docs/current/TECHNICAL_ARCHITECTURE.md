# Technische Architektur: Intelligent Book Sales Pipeline

**Version:** 3.1 (Stability Fixes)
**Letztes Update:** 13.02.2026
**Basis:** Refactoring & System-Level LLM Integration

---

## 📐 System-Übersicht

Die Intelligent Book Sales Pipeline ist eine **event-driven, microservices-basierte Cloud-Native Plattform** auf Google Cloud Platform, die Bücher automatisch identifiziert, bewertet, preislich einordnet und auf Verkaufsplattformen listet.

### Kern-Prinzipien

1. **Multi-Tenancy:** Vollständige User-Isolation auf Firestore-Ebene
2. **Event-Driven:** Pub/Sub für lose Kopplung zwischen Services
3. **Serverless-First:** Cloud Run & Cloud Functions für Auto-Scaling
4. **AI-Native:** Gemini 2.0 Flash / Pro für Multimodal Analysis & Pricing
5. **System-Managed LLM:** Zentrale Integration via System-Level GEMINI_API_KEY

---

## 🏗️ Architektur-Komponenten

### 1. Agent Layer (Microservices)

Sechs spezialisierte Agents, die jeweils eine klar definierte Aufgabe haben:

#### 1.1 Ingestion Agent
**Datei:** [`agents/ingestion-agent/main.py`](agents/ingestion-agent/main.py:1)
**Status:** ✅ DEPLOYED (Cloud Run)
**Trigger:** Pub/Sub Topic `ingestion-requests` (via Eventarc Trigger `ingestion-agent-trigger`)

**Verantwortlichkeit:**
- End-to-End Bildanalyse und Metadaten-Extraktion via Gemini 2.5 Pro
- Live-Verifikation via Search Grounding
- KI-generierte Produktbeschreibungen (Teil des Extraktions-Prompts)

**Workflow:**
```
1. Empfängt CloudEvent von "ingestion-requests" Topic
2. Lädt Bilder von Cloud Storage (In-Memory)
3. Ruft shared library `simplified_ingestion` auf
4. Gemini Call (Multimodal + Search Grounding Tool)
5. Extraktion von JSON + Grounding Metadata (Robustes Parsing für Chatty Models)
6. Firestore Update → Status "analyzed"
7. Trigger Condition Assessment (Pub/Sub: condition-assessment-jobs)
8. Trigger Price Research (Pub/Sub: price-research-requests)
```

**Konfiguration:**
- `GEMINI_MODEL`: gemini-2.5-pro (via Config)
- `ENABLE_GROUNDING`: True
- `MAX_RETRIES`: 3
- `STRICT_ENV_CHECKS`: True (Fail Fast bei fehlender Project ID/PubSub)

**Dependencies:**
- System Gemini Integration (GEMINI_API_KEY)
- Shared Library (`shared.simplified_ingestion`)

#### 1.2 Condition Assessor Agent
**Datei:** [`agents/condition-assessor/main.py`](agents/condition-assessor/main.py:1)
**Status:** ✅ DEPLOYED (Cloud Run)
**Trigger:** Pub/Sub Topic `condition-assessment-jobs` (Push Endpoint)

**System-API-Key Architektur:**

Der Condition Assessor nutzt einen **System-Level GEMINI_API_KEY**:
- **Konsistenz:** Gleiche Qualität für alle Nutzer
- **Reliability:** Keine Abhängigkeit von User-Credentials/Budget
- **Cost Transparency:** Klare Kostenattribution zum System-Feature

**Technologie:**
- **Model:** Gemini 2.5 Flash (`gemini-2.5-flash`)
- **SDK:** Google Generative AI Python SDK (Vertex AI)
- **Response Format:** Strukturiertes JSON via `response_mime_type: "application/json"`
- **Temperature:** 0.1 (niedrig für analytische Konsistenz)

**Verantwortlichkeit:**
- Professionelle Zustandsbewertung nach ABAA/ILAB Standards
- Holistische Multi-Image Analyse (alle Bilder gemeinsam)
- Komponenten-Bewertung (Cover, Spine, Pages, Binding)
- Defekt-Erkennung (Stains, Tears, Foxing, Sunning, etc.)
- Grade-Berechnung (Fine → Poor)
- Preis-Faktor-Ermittlung (0.1 - 1.0)

**Bewertungs-Pipeline:**
```
1. Pub/Sub CloudEvent empfangen (von Ingestion Agent via HTTP Push)
2. Bilder von Cloud Storage laden (GCS URIs → PIL Images)
3. Prompt Construction: "Expert antiquarian bookseller" Persona
4. GenAI Inference: Multi-Image Holistic Analysis
5. Response Parsing: JSON → ConditionScore Dataclass
6. Firestore Update:
   - users/{userId}/condition_assessments/{bookId}
   - users/{userId}/books/{bookId} (Status: "condition_assessed")
```

**Condition Grades & Price Factors:**
- **Fine:** Score 90-100, Price Factor: ~1.0 (keine Abzüge)
- **Very Fine:** Score 80-89, Price Factor: ~0.85 (-15%)
- **Good:** Score 60-79, Price Factor: ~0.65 (-35%)
- **Fair:** Score 40-59, Price Factor: ~0.45 (-55%)
- **Poor:** Score 0-39, Price Factor: ~0.25 (-75%)

**Dependencies:**
- Google GenAI SDK (`google.genai`)
- Cloud Storage (Bild-Downloads)
- System API Key (GEMINI_API_KEY aus Secret Manager)

**Deployment:**
```yaml
Service Type: Cloud Run
Runtime: Python 3.11
Region: europe-west1
Memory: 2GB
Timeout: 540s (9 Minuten)
Trigger: Pub/Sub "condition-assessment-jobs" (HTTP Push)
```

**Detaillierte Dokumentation:** [`docs/agents/CONDITION_ASSESSOR.md`](../agents/CONDITION_ASSESSOR.md)

#### 1.3 Strategist Agent (Pricing Agent)
**Datei:** [`agents/strategist-agent/main.py`](agents/strategist-agent/main.py:1)
**Status:** ✅ IMPLEMENTED & DEPLOYED
**Trigger:** Pub/Sub `price-research-requests`

**Verantwortlichkeit:**
- **"Super Request" Pricing:** Konsolidierte Preisfindung
- **Analytic Approach:** Nutzt Condition Data + Metadaten (Text-only für Stabilität)
- **Decision Making:** Bestimmt Listenpreis, Konfidenz und Begründung

**Funktionsweise (Gemini 2.5 Pro):**
Der Agent führt keine komplexen State-Machines mehr aus, sondern nutzt die Fähigkeiten von **Gemini 2.5 Pro**:
1. Empfängt Buch-Metadaten.
2. Lädt Condition Report aus Firestore.
3. Konstruiert einen umfassenden Prompt ("Expert Antiquarian Bookseller").
4. Generiert JSON-Response mit Preis, Konfidenz und Begründung.
   - *Hinweis:* Google Search Tool temporär deaktiviert wg. Vertex AI 400 Errors bei Multimodal Requests.

**Configuration:**
- `MODEL`: `gemini-1.5-flash` (Fallback Mode)
- `TOOLS`: Disabled (Temporary Stability Fix - Uses Internal Knowledge)
- `TEMPERATURE`: 0.1

#### 1.4 Scout Agent
**Status:** 🗑️ DELETED / REMOVED
**Grund:** Funktionalität wurde vollständig durch das **Google Search Tool** im Strategist Agent ersetzt. Service wurde am 08.02.2026 aus dem Projekt entfernt.

#### 1.5 Sentinel Agent
**Datei:** [`agents/sentinel-agent/main.py`](agents/sentinel-agent/main.py:1)  
**Status:** ⚠️ Code fertig, Deployment pending  
**Trigger:** Pub/Sub Topic `sale-notification-received`

**Verantwortlichkeit:**
- Verkaufserkennung
- Delisting-Orchestrierung
- Status-Update auf "sold"

**Workflow:**
```
1. Sale Notification empfangen
2. Book Status → "sold"
3. Publish auf "delist-book-everywhere"
4. Ambassador Agent übernimmt Delisting
```

#### 1.6 Ambassador Agent
**Datei:** [`agents/ambassador-agent/main.py`](agents/ambassador-agent/main.py:1)  
**Status:** ⚠️ Code fertig, Deployment pending (eBay Credentials fehlen)  
**Trigger:** Pub/Sub Topic `book-listing-requests` & `delist-book-everywhere`

**Verantwortlichkeit:**
- Multi-Platform Listing Management
- eBay API Integration (aktuell einzige Plattform)
- Produktbeschreibung-Enhancement mit System LLM

**Plattformen:**
```python
PLATFORMS = {
    "ebay": EbayPlatform  # Implementiert
    # Erweiterbar via platforms/base.py
}
```

**Listing-Pipeline:**
```
1. Book Data von Firestore laden
2. Optional: LLM-Enhancement der Beschreibung
3. eBay SDK: Create Listing
4. Store listing_id in Firestore
```

**Delisting-Pipeline:**
```
1. Query active listings für book_id
2. Pro Plattform: API Call zum Delisting
3. Update listing status → "delisted"
```

---

### 2. Dashboard Layer

#### 2.1 Backend (Flask API)
**Datei:** [`dashboard/backend/main.py`](dashboard/backend/main.py:1)  
**Status:** ✅ Build erfolgreich, Deployment zu verifizieren  
**Deployment:** Cloud Run

**API-Endpunkte:**

**Buch-Management:**
- `POST /api/books/upload` - Signed URL für GCS Upload
- `POST /api/books/start-processing` - Triggert Ingestion Pipeline
- `POST /api/books/<id>/reprocess` - Korrektur-Workflow

**Condition Assessment:**
- `POST /api/books/assess-condition` - Triggert Assessment
- `GET /api/books/<id>/condition-assessment` - Assessment abrufen
- `POST /api/books/override-condition` - Manuelle Überschreibung
- `GET /api/books/<id>/condition-history` - Assessment-Historie

**Authentication:**
```python
def _get_uid_from_token(id_token):
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token['uid']
    except auth.ExpiredIdTokenError:
        # Clock skew retry logic
```

**Rate Limiting:**
```python
limiter = Limiter(
    storage_uri="memory://"  # ⚠️ Production: Use Redis!
)

@limiter.limit("100 per minute")  # Default
@limiter.limit("20 per minute")   # Uploads
```

#### 2.2 Frontend (React SPA)
**Verzeichnis:** [`dashboard/frontend/`](dashboard/frontend/)  
**Status:** ✅ Firebase Hosting konfiguriert  
**Framework:** React 18 + Vite + Tailwind CSS

**Komponenten:**
- [`App.jsx`](dashboard/frontend/src/App.jsx:1) - Routing & Auth
- [`ImageUpload.jsx`](dashboard/frontend/src/components/ImageUpload.jsx:1) - GCS Upload Flow
- [`BookList.jsx`](dashboard/frontend/src/components/BookList.jsx:1) - Realtime Firestore Listener
- [`ConditionAssessment.jsx`](dashboard/frontend/src/components/ConditionAssessment.jsx:1) - Assessment UI

**Routes:**
```
/ → BookList (Protected)
/upload → ImageUpload (Protected)
/condition → ConditionAssessment (Protected)
/login → Login (Public)
/register → Register (Public)
```

---

### 3. Shared Libraries Layer

#### 3.1 Firestore Client
**Datei:** [`shared/firestore/client.py`](shared/firestore/client.py:1)

**Multi-Tenancy Pattern:**
```
users/{userId}/books/{bookId}
users/{userId}/condition_assessments/{bookId}
users/{userId}/listings/{listingId}
market_data/{dataId}  # Shared
```

**Status Transitions:**
```python
VALID_STATUS_TRANSITIONS = {
    "ingested": ["condition_assessed", "failed"],
    "condition_assessed": ["priced", "failed"],
    "priced": ["described", "failed"],
    "described": ["listed", "failed"],
    "listed": ["sold", "delisted", "failed"],
    "sold": [],
    "delisted": ["listed"],
    "failed": ["ingested"]
}
```

**⚠️ KNOWN ISSUE:** Ingestion Agent setzt direkt "priced", überspringt Zwischenschritte!

#### 3.2 Simplified Ingestion Core
**Datei:** [`shared/simplified_ingestion/core.py`](shared/simplified_ingestion/core.py:1)

**Verantwortlichkeit:**
- Zentrale Logik für die Ingestion Pipeline
- Kapselung der Gemini API Interaktion
- Error Handling & Retry Logic
- Extraktion von Grounding Metadata

**Logik:**
- Nutzt `google-genai` SDK für Vertex AI Zugriff
- Konfiguriert das Model mit `GoogleSearchRetrieval` Tool
- **Parsing:** Robustes JSON-Parsing inkl. Markdown Code-Block Extraction
- Berechnet einfache Confidence-Metriken basierend auf Model-Feedback

---

## 🔄 Datenflüsse

### Workflow 1: Buch-Ingestion (End-to-End)

```
┌─────────────────────────────────────────────────────────────────────┐
│ USER                                                                  │
└─────────────────────────────────────────────────────────────────────┘
    │
    │ 1. Upload Images via Frontend
    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ DASHBOARD FRONTEND                                                    │
│ - ImageUpload.jsx: POST /api/books/upload                           │
└─────────────────────────────────────────────────────────────────────┘
    │
    │ 2. Request Signed URL
    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ DASHBOARD BACKEND (Cloud Run)                                        │
│ - Generate Signed URL for GCS                                       │
│ - Return to Frontend                                                 │
└─────────────────────────────────────────────────────────────────────┘
    │
    │ 3. Direct Upload to GCS
    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ CLOUD STORAGE                                                         │
│ - Store images in bucket                                             │
└─────────────────────────────────────────────────────────────────────┘
    │
    │ 4. POST /api/books/start-processing
    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ DASHBOARD BACKEND                                                     │
│ - Create book document in Firestore (status: "ingested")            │
│ - Publish message to Pub/Sub "ingestion-requests"                       │
└─────────────────────────────────────────────────────────────────────┘
    │
    │ 5. Pub/Sub Event (Eventarc Trigger)
    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ INGESTION AGENT (Cloud Run)                                          │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ 1. Load images from GCS (In-Memory)                             │ │
│ │ 2. Call Shared Library (simplified_ingestion)                   │ │
│ │ 3. Gemini 2.5 Pro Call:                                         │ │
│ │    - Multimodal Analysis (Bilder)                               │ │
│ │    - Google Search Grounding (Live-Recherche)                   │ │
│ │    - Structured Output Extraction (JSON)                        │ │
│ │ 4. Parallel Dispatch:                                           │ │
│ │    - Trigger Condition Assessment                               │ │
│ │    - Trigger Price Research                                     │ │
│ └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
    │
    │ 6. Update Firestore
    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ FIRESTORE                                                             │
│ users/{userId}/books/{bookId}                                        │
│ - status: "analyzed"                                                 │
│ - bookData: { title, author, isbn, ... }                            │
│ - confidence: 0.95                                                   │
│ - sources_used: ["google_search", "gemini_knowledge"]               │
└─────────────────────────────────────────────────────────────────────┘
    │
    │ 7. Trigger Condition Assessment & Pricing
    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ PUB/SUB (condition-assessment-jobs)                                 │
│ PUB/SUB (price-research-requests)                                   │
└─────────────────────────────────────────────────────────────────────┘
```

### Workflow 2: Condition Assessment

```
┌─────────────────────────────────────────────────────────────────────┐
│ USER: Clicks "Assess Condition" in Frontend                          │
└─────────────────────────────────────────────────────────────────────┘
    │
    │ POST /api/books/assess-condition
    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ DASHBOARD BACKEND                                                     │
│ - Create document in Firestore:                                     │
│   users/{userId}/condition_assessment_requests/{requestId}          │
└─────────────────────────────────────────────────────────────────────┘
    │
    │ Firestore onCreate Trigger ⚠️ (NOT Pub/Sub!)
    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ CONDITION ASSESSOR AGENT                                              │
│ ┌─────────────────────────────────────────────────────────────────┐ │
│ │ 1. Load images from GCS                                         │ │
│ │ 2. Per Image Analysis:                                          │ │
│ │    - Vision API: Detect objects, colors, text                  │ │
│ │    - Defect Detection: Stains, Tears, Yellowing, etc.         │ │
│ │ 3. Component Scoring:                                          │ │
│ │    - Cover: 30% weight                                          │ │
│ │    - Spine: 25% weight                                          │ │
│ │    - Pages: 25% weight                                          │ │
│ │    - Binding: 20% weight                                        │ │
│ │ 4. Calculate Final Grade (Fine → Poor)                         │ │
│ │ 5. Calculate Price Factor (1.0 → 0.25)                         │ │
│ └─────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
    │
    │ Update Firestore
    ↓
┌─────────────────────────────────────────────────────────────────────┐
│ FIRESTORE                                                             │
│ users/{userId}/condition_assessments/{bookId}                        │
│ - grade: "GOOD"                                                      │
│ - priceFactor: 0.65                                                  │
│ - componentScores: { cover: 75, spine: 80, ... }                    │
│ - detectedIssues: ["Minor yellowing on pages"]                      │
│ - assessedAt: timestamp                                              │
│                                                                       │
│ users/{userId}/books/{bookId}                                        │
│ - status: "condition_assessed"                                       │
│ - conditionGrade: "GOOD"                                             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 🔐 Security-Architektur

### Multi-Tenancy Isolation

**Firestore Security Rules:**
```javascript
match /users/{userId}/books/{bookId} {
  allow read: if isAuthenticated() && isOwner(userId);
  allow write: if isAuthenticated() && isOwner(userId);
  allow read: if isServiceAccount();  // Agents können lesen
}
```

**Helper Functions:**
```javascript
function isAuthenticated() {
  return request.auth != null;
}

function isOwner(userId) {
  return request.auth.uid == userId;
}

function isServiceAccount() {
  return request.auth.token.email.matches(".*@.*\\.iam\\.gserviceaccount\\.com$");
}
```

### Authentication Flow

```
1. User → Firebase Auth (Email/Password)
2. Firebase → ID Token
3. Frontend → Backend API (ID Token in Authorization header)
4. Backend → Verify ID Token with Firebase Admin SDK
5. Backend → Extract user_id from token
6. Backend → Use user_id for Firestore paths
```

---

## 📊 Monitoring & Observability

### Logging

**Aktuell:**
- Agents: `logging.basicConfig(level=logging.INFO)` → stdout
- Cloud Run erfasst stdout automatisch → Cloud Logging

**⚠️ Verbesserung empfohlen:**
- Strukturiertes Logging (JSON)
- Explizite Cloud Logging Integration
- Request Tracing mit Correlation IDs

### Metrics

**Aktuell:**
- Monitoring von API-Quotas in Google Cloud Console
- Cloud Run Basic Metrics (CPU, Memory, Requests)

**Fehlend:**
- Custom Metrics für Business Logic
- Ingestion Success Rate
- Average Confidence Scores
- Condition Assessment Accuracy

### Alerting

**Fehlend (zu implementieren):**
- Error Rate > Threshold
- Budget Exceeded Alerts
- API Quota Warnings
- Cold Start Latency Alerts

---

## 🚀 Deployment-Architektur

### Cloud Run Services

```
Service: ingestion-agent
├── Image: gcr.io/project-52b2fab8-15a1-4b66-9f3/ingestion-agent
├── Region: europe-west1
├── Min Instances: 0 (Cold Start)
├── Max Instances: 100 (Auto-scale)
├── Memory: 2GB
├── CPU: 2
├── Timeout: 540s (9 min)
└── Trigger: Pub/Sub "ingestion-requests" (Eventarc)

Service: dashboard-backend
├── Image: gcr.io/project-52b2fab8-15a1-4b66-9f3/dashboard-backend
├── Region: europe-west1
├── Min Instances: 1 (⚠️ Empfehlung für Production)
├── Memory: 1GB
├── CPU: 1
├── Timeout: 300s
└── Trigger: HTTP (Public + Auth Check)
```

### Firebase Hosting

```
Project: project-52b2fab8-15a1-4b66-9f3
├── Public Dir: dashboard/frontend/dist
├── Rewrites: /** → /index.html (SPA)
└── Deploy: firebase deploy --only hosting
```

### Pub/Sub Topics

```
ingestion-requests (ehemals trigger-ingestion)
├── Publisher: Dashboard Backend
└── Subscriber: Ingestion Agent

condition-assessment-jobs (ehemals trigger-condition-assessment)
├── Publisher: Ingestion Agent
└── Subscriber: Condition Assessor Agent

price-research-requests
├── Publisher: Ingestion Agent / Condition Assessor Agent
└── Subscriber: Strategist Agent

sale-notification-received
├── Publisher: External (eBay Webhook)
└── Subscriber: Sentinel Agent

delist-book-everywhere
├── Publisher: Sentinel Agent
└── Subscriber: Ambassador Agent

book-listing-requests
├── Publisher: Strategist Agent
└── Subscriber: Ambassador Agent
```

### Cloud Storage

```
Bucket: {project-id}-book-images
├── Location: europe-west1
├── Storage Class: Standard
└── Lifecycle: 90 days then Archive
```

---

## 🎯 Performance-Überlegungen

### Bottlenecks

1. **Cold Starts:** Cloud Run Services können 5-10s Latenz haben
   - **Lösung:** Minimum Instances für kritische Services

2. **Gemini Vision API:** ~2-3s pro Bild
   - **Lösung:** Parallel Processing von Multiple Images

3. **Multi-Source API Calls:** ~1-2s pro externe API
   - **Lösung:** Async/Await + Parallel Execution

4. **Firestore Queries:** Multi-Tenant Queries könnten langsam werden
   - **Lösung:** Composite Indexes für häufige Queries

### Optimierungen

✅ **Implementiert:**
- Data Fusion Cache (1h TTL)
- Parallel API Calls in Data Fusion
- Async Processing in Ingestion Agent

⚠️ **Empfohlen:**
- Redis für Rate Limiting (statt Memory)
- Cloud CDN für Frontend
- Firestore Connection Pooling

---

## 📝 Bekannte Limitierungen

1. **Status Transitions Inkonsistenz**
   - Ingestion Agent überspringt States
   - Muss mit VALID_STATUS_TRANSITIONS synchronisiert werden

2. **Scout Agent TTL-Policy**
   - Dokumentiert als 60 Tage
   - Aber nicht in Firestore konfiguriert

3. **Rate Limiting**
   - Memory-Backend nicht Production-Ready
   - Redis erforderlich für Multi-Instance Setups

4. **eBay Credentials**
   - Fehlen für Ambassador Agent Deployment
   - Sandbox-Test erforderlich vor Production

5. **Monitoring Lücken**
   - Keine Custom Business Metrics
   - Keine Alerting-Strategie

---

## 🔄 Nächste Architektur-Verbesserungen

### Phase 2 (Q1 2025)

1. **Service Mesh** (Istio/Cloud Service Mesh)
   - Traffic Management
   - Circuit Breaking
   - Distributed Tracing

2. **Event Sourcing**
   - Audit Trail für alle Book State Changes
   - Replay-Fähigkeit

3. **ML-Pipeline Integration**
   - Vertex AI Training für Custom Models
   - Automated Pricing Model Updates

4. **Multi-Region Deployment**
   - Disaster Recovery
   - Geo-Redundanz

---

**Dokument-Version:** 3.1 (Stability Fixes)
**Basis:** Refactoring 13.02.2026
**Validiert:** Gegen tatsächliche Implementierung  
**Nächste Review:** Nach Stability Monitoring
