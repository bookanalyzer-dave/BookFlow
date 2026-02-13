# Konfigurations-Referenz: Intelligent Book Sales Pipeline

**Version:** 2.1 (OCR Removal & DLQ)
**Letztes Update:** 05.02.2026
**Zweck:** Zentrale Dokumentation aller Environment Variables und Konfigurationsoptionen

---

## 📋 Übersicht

Dieses Dokument konsolidiert alle Konfigurationsoptionen aus:
- Agent `.env.yaml` Files
- Dashboard `.env` Files
- Code-Default-Werte
- Deployment-Konfigurationen

---

## 🌍 GCP-Kern-Konfiguration

### Erforderliche Basis-Variablen

Diese Variablen sind für **ALLE** Komponenten erforderlich:

```bash
# GCP Projekt Identifikation
GCP_PROJECT=project-52b2fab8-15a1-4b66-9f3
# ⚠️ Alternative Namen im Code: GOOGLE_CLOUD_PROJECT, GCP_PROJECT_ID
# EMPFEHLUNG: Standardisieren auf GCP_PROJECT

# GCP Region
GCP_LOCATION=europe-west1
# Alternative: REGION (einige Agents)

# Google Books API Key
GOOGLE_BOOKS_API_KEY=your-api-key-here
# Erforderlich für: Ingestion Agent, Data Fusion Engine

# System Gemini API Key
GEMINI_API_KEY=your-gemini-key-here
# Erforderlich für: Alle Agents (System-Level Integration)
```

---

## 🤖 Ingestion Agent

**Datei:** [`agents/ingestion-agent/.env.yaml`](agents/ingestion-agent/.env.yaml)  
**Deployment:** Cloud Run Function

### Vision & AI Models

```yaml
# Gemini Vision Model für Bildanalyse
GEMINI_MODEL: "gemini-2.5-pro"
# Alternativen: gemini-1.5-flash, gemini-1.5-pro
# Default im Code: "gemini-2.5-pro"

# Gemini Model für Text-Generation
GEMINI_RESEARCH_MODEL: "gemini-1.5-pro"
# Verwendet für: AI Description Generation
```

### Feature Flags (Legacy - Deprecated)

*Die folgenden Flags sind in der neuen `simplified_ingestion` Architektur nicht mehr aktiv, da Gemini + Grounding die Recherche übernimmt.*

```yaml
USE_ENHANCED_RESEARCH: "true" # Deprecated
ENABLE_PARALLEL_APIS: "true"  # Deprecated
ENABLE_OPENLIBRARY: "true"    # Deprecated
```

### Qualitäts-Parameter

```yaml
# Minimale Konfidenz für Auto-Accept
MIN_CONFIDENCE_THRESHOLD: "0.6"
# Default: 0.6 (60%)
# Bücher unter diesem Wert → Status "needs_review"
# Über diesem Wert → Status "priced"

# Maximale Bilder pro Buch
MAX_IMAGES_PER_BOOK: "10"
# Default: 10
# Limit für Vision API Calls
```

### API Timeouts

```yaml
# Timeout für Gemini API Calls (Sekunden)
GEMINI_TIMEOUT: "60"
# Default: 60 (Multimodal + Search kann dauern)
```

### Python Path

```yaml
# Python Module Path
PYTHONPATH: "../.."
# Erforderlich für: Import von shared libraries
# WICHTIG: Nicht ändern!
```

---

## 🔍 Condition Assessor Agent

**Datei:** [`agents/condition-assessor/.env.yaml`](agents/condition-assessor/.env.yaml)  
**Deployment:** Cloud Run Function (Firestore Trigger)

### Vision API Konfiguration

```yaml
# Gemini Model für Condition Assessment
GEMINI_MODEL: "gemini-1.5-pro"
# Alternative: gemini-1.5-flash (schneller)

# Cloud Vision API Features
VISION_FEATURES: "OBJECT_LOCALIZATION,TEXT_DETECTION,LABEL_DETECTION"
# Default: Wie oben
# Verwendet für: Defekt-Erkennung
```

### Assessment-Parameter

```yaml
# Schwellenwerte für Condition Grades
CONDITION_THRESHOLD_FINE: "0.95"
CONDITION_THRESHOLD_VERY_FINE: "0.85"
CONDITION_THRESHOLD_GOOD: "0.70"
CONDITION_THRESHOLD_FAIR: "0.50"
# Default: Wie oben
# Alles darunter: POOR

# Maximale Bilder für Assessment
MAX_ASSESSMENT_IMAGES: "10"
# Default: 10
```

### Komponenten-Gewichtung

```yaml
# Gewichtung der Buchkomponenten (muss Summe 1.0 ergeben)
WEIGHT_COVER: "0.30"    # 30%
WEIGHT_SPINE: "0.25"    # 25%
WEIGHT_PAGES: "0.25"    # 25%
WEIGHT_BINDING: "0.20"  # 20%
# Default: Wie oben
```

### Defekt-Severity

```yaml
# Severity-Multiplikatoren für Defekte
DEFECT_SEVERITY_MINOR: "0.95"   # -5%
DEFECT_SEVERITY_MODERATE: "0.85" # -15%
DEFECT_SEVERITY_MAJOR: "0.70"   # -30%
DEFECT_SEVERITY_SEVERE: "0.50"  # -50%
# Default: Wie oben
```

---

## 💡 Strategist Agent

**Datei:** [`agents/strategist-agent/.env.yaml`](agents/strategist-agent/.env.yaml)  
**Deployment:** Cloud Run Function (Pub/Sub Trigger)

### Pricing-Strategie

```yaml
# ML-basierte Preisfindung aktivieren
ML_PRICING_ENABLED: "false"
# Default: false (traditioneller Algorithmus aktiv)

# Minimale ML Confidence für ML-Preis
ML_CONFIDENCE_THRESHOLD: "0.7"
# Default: 0.7 (70%)
# Nur bei höherer Confidence wird ML-Preis akzeptiert
```

### Wettbewerbs-Parameter

```yaml
# Unterbietungs-Faktor (Wettbewerbsvorteil)
COMPETITIVE_UNDERCUT_FACTOR: "0.92"
# Default: 0.92 (8% unter Durchschnitt)
# Range: 0.80 - 1.00

# Minimaler Preis (Euro)
MIN_PRICE: "5.0"
# Default: 5.0
# Niemals unter diesem Wert preisen

# Maximaler Preis (Euro)
MAX_PRICE: "500.0"
# Default: 500.0
# Cap für unrealistische Preise
```

### Market Data

```yaml
# Maximale Anzahl Market Data Points
MAX_MARKET_DATA_POINTS: "50"
# Default: 50
# Verwendet für: Preisberechnung

# Market Data TTL (Tage)
MARKET_DATA_TTL_DAYS: "60"
# Default: 60
# ⚠️ Nur dokumentiert, nicht im Code konfiguriert!
```

---

## 🕵️ Scout Agent

**Datei:** [`agents/scout-agent/.env.yaml`](agents/scout-agent/.env.yaml)  
**Status:** Optional für Alpha

### Scraping-Konfiguration

```yaml
# Headless Browser aktivieren
PUPPETEER_HEADLESS: "true"
# Default: true
# Wenn false: Browser-Fenster sichtbar (für Debugging)

# Browser Timeout (ms)
BROWSER_TIMEOUT: "30000"
# Default: 30000 (30 Sekunden)
```

### Scraping-Targets

```yaml
# Target URLs (Beispiel)
SCRAPING_TARGETS: "https://www.abebooks.com,https://www.zvab.com"
# Komma-separierte Liste
# ⚠️ Rechtliche Prüfung erforderlich!
```

---

## 🛡️ Sentinel Agent

**Datei:** [`agents/sentinel-agent/.env.yaml`](agents/sentinel-agent/.env.yaml)

### Minimal Config

```yaml
# Keine speziellen Config-Optionen
# Nutzt nur GCP_PROJECT und Standard-Config
```

---

## 📢 Ambassador Agent

**Datei:** [`agents/ambassador-agent/.env.yaml`](agents/ambassador-agent/.env.yaml)  
**Status:** eBay Credentials fehlen!

### eBay API Konfiguration

```yaml
# eBay App ID (Sandbox)
EBAY_APP_ID: "your-sandbox-app-id"
# Erforderlich für: eBay SDK

# eBay Cert ID (Sandbox)
EBAY_CERT_ID: "your-sandbox-cert-id"

# eBay Dev ID (Sandbox)
EBAY_DEV_ID: "your-sandbox-dev-id"

# eBay Environment
EBAY_ENVIRONMENT: "sandbox"
# Production: "production"
# ⚠️ WICHTIG: Niemals Production ohne extensive Tests!
```

### Listing-Defaults

```yaml
# Standard Listing-Dauer (Tage)
DEFAULT_LISTING_DURATION: "30"
# Default: 30
# eBay Maximum: 30 Tage für Good-Til-Cancelled

# Standard Kategorie (eBay)
DEFAULT_EBAY_CATEGORY: "267"
# 267 = Books > Nonfiction Books
# Oder dynamisch aus Buch-Daten ermitteln
```

### LLM Enhancement

```yaml
# AI Description Enhancement aktivieren
ENABLE_LLM_ENHANCEMENT: "true"
# Default: true
# Verwendet System LLM für bessere Beschreibungen

# Max Tokens für Enhancement
ENHANCEMENT_MAX_TOKENS: "500"
# Default: 500
```

---

## 🎛️ Dashboard Backend

**Datei:** [`dashboard/backend/.env`](dashboard/backend/.env)

### Firebase Configuration

```bash
# Firebase Service Account
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
# Erforderlich für: Firebase Admin SDK
# ⚠️ In Cloud Run via Service Account, nicht via File!

# Firebase Database URL
FIREBASE_DATABASE_URL=https://project-52b2fab8-15a1-4b66-9f3.firebaseio.com
# Optional (Firestore nutzt Standard)
```

### API Configuration

```bash
# Backend Port
PORT=8080
# Default: 8080
# Cloud Run setzt automatisch $PORT

# Flask Environment
FLASK_ENV=production
# Development: "development"
# Production: "production"

# Debug Mode
DEBUG=false
# Default: false in production
# WICHTIG: Niemals true in Production!
```

### Rate Limiting

```bash
# Rate Limiter Storage
RATE_LIMITER_STORAGE_URI=memory://
# Production: redis://redis-host:6379
# ⚠️ Memory-Backend NICHT für Multi-Instance!

# Default Rate Limit
DEFAULT_RATE_LIMIT=100 per minute
# Kann auch: "100/minute", "100 per hour"

# Upload Rate Limit
UPLOAD_RATE_LIMIT=20 per minute
```

### CORS Configuration

```bash
# Allowed Origins
CORS_ORIGINS=https://project-52b2fab8-15a1-4b66-9f3.web.app,http://localhost:5173
# Komma-separiert
# Lokale Development + Firebase Hosting
```

### Cloud Storage

```bash
# Storage Bucket
STORAGE_BUCKET=project-52b2fab8-15a1-4b66-9f3-book-images
# Default: {project-id}-book-images

# Signed URL Expiration (Sekunden)
SIGNED_URL_EXPIRATION=3600
# Default: 3600 (1 Stunde)
```

### Pub/Sub Topics

```bash
# Book Analysis Topic
BOOK_ANALYSIS_TOPIC=trigger-ingestion
# ⚠️ Dokumentation sagt oft "image-uploads", aber Code nutzt "trigger-ingestion"

# Sale Notification Topic
SALE_NOTIFICATION_TOPIC=sale-notification-received

# Delist Topic
DELIST_TOPIC=delist-book-everywhere

# Listing Request Topic
LIST_REQUEST_TOPIC=list-book-request
```

---

## 🎨 Dashboard Frontend

**Datei:** [`dashboard/frontend/.env.production`](dashboard/frontend/.env.production)

### Firebase Configuration

```bash
# Firebase Config (aus Firebase Console)
VITE_FIREBASE_API_KEY=your-api-key
VITE_FIREBASE_AUTH_DOMAIN=project-52b2fab8-15a1-4b66-9f3.firebaseapp.com
VITE_FIREBASE_PROJECT_ID=project-52b2fab8-15a1-4b66-9f3
VITE_FIREBASE_STORAGE_BUCKET=project-52b2fab8-15a1-4b66-9f3.appspot.com
VITE_FIREBASE_MESSAGING_SENDER_ID=your-sender-id
VITE_FIREBASE_APP_ID=your-app-id
```

### Backend API

```bash
# Backend API URL
VITE_API_URL=https://backend-[hash]-ew.a.run.app
# Production: Cloud Run URL
# Development: http://localhost:8080

# API Timeout (ms)
VITE_API_TIMEOUT=30000
# Default: 30000 (30 Sekunden)
```

### Feature Flags

```bash
# Debug Logging aktivieren
VITE_ENABLE_DEBUG_LOGS=false
# Default: false in production
```

---

## 🗄️ Firestore Configuration

### Collections-Schema

```
users/
├── {userId}/
│   ├── books/
│   │   └── {bookId}
│   │       ├── status: string
│   │       ├── bookData: object
│   │       ├── images: array
│   │       ├── confidence: number
│   │       ├── sources: array
│   │       └── timestamps: object
│   │
│   ├── condition_assessments/
│   │   └── {assessmentId}
│   │       ├── bookId: string
│   │       ├── grade: string
│   │       ├── priceFactor: number
│   │       ├── componentScores: object
│   │       └── detectedIssues: array
│   │
│   ├── condition_assessment_requests/
│   │   └── {requestId}
│   │       ├── bookId: string
│   │       ├── status: string
│   │       └── createdAt: timestamp
│   │
│   └── listings/
│       └── {listingId}
│           ├── bookId: string
│           ├── platform: string
│           ├── externalId: string
│           ├── status: string
│           └── listedAt: timestamp
│
└── market_data/
    └── {dataId}
        ├── isbn: string
        ├── prices: array
        ├── source: string
        └── scrapedAt: timestamp
```

---

## 🚀 Cloud Build Configuration

**Datei:** [`cloudbuild.yaml`](cloudbuild.yaml) (Ingestion Agent)  
**Datei:** [`cloudbuild.backend.yaml`](cloudbuild.backend.yaml) (Backend)

### Build Args

```yaml
# Cloud Build überschreibt automatisch:
PROJECT_ID: $_PROJECT_ID  # GCP Projekt ID
REGION: $_REGION          # Deployment Region

# Deployment Optionen
--allow-unauthenticated: false  # WICHTIG: Auth erforderlich!
--min-instances: 0             # Cold Starts erlauben
--max-instances: 100           # Auto-Scale Limit
--memory: 2Gi                  # RAM pro Instance
--cpu: 2                       # vCPUs
--timeout: 540s                # 9 Minuten Max
```

---

## ⚙️ Standard-Werte (Code Defaults)

Wenn Environment Variable fehlt, nutzt Code folgende Defaults:

### Ingestion Agent
```python
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-pro")
MIN_CONFIDENCE_THRESHOLD = float(os.getenv("MIN_CONFIDENCE_THRESHOLD", "0.6"))
USE_ENHANCED_RESEARCH = os.getenv("USE_ENHANCED_RESEARCH", "true").lower() == "true"
ENABLE_PARALLEL_APIS = os.getenv("ENABLE_PARALLEL_APIS", "true").lower() == "true"
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "10"))
```

### Data Fusion Engine
```python
DEFAULT_CACHE_TTL = 3600  # 1 hour
MAX_SOURCES = 3
CONFIDENCE_BOOST_MULTIPLE_SOURCES = 0.1
```

### Firestore Client
```python
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds
```

---

## ⚠️ Kritische Konfiguration-Issues

### 1. Environment Variable Namen Inkonsistenz

**Problem:**
```bash
# Verschiedene Namen für GCP Projekt:
GCP_PROJECT         # Ingestion Agent
GOOGLE_CLOUD_PROJECT # Condition Assessor
GCP_PROJECT_ID      # Backend
```

**Lösung:** Standardisieren auf `GCP_PROJECT` überall

### 2. Pub/Sub Topic Namen

**Dokumentation vs. Code:**
```bash
# Dokumentation: image-uploads
# Code: trigger-ingestion
```

**Lösung:** Dokumentation korrigieren auf `trigger-ingestion`

### 3. Rate Limiter Production-Readiness

**Problem:**
```python
storage_uri="memory://"  # Nicht für Multi-Instance!
```

**Lösung:** Redis Backend für Production:
```python
storage_uri="redis://redis-host:6379"
```

### 4. eBay Credentials

**Problem:** Fehlen komplett für Ambassador Agent

**Lösung:** eBay Developer Portal registrieren, Sandbox Credentials eintragen

---

## 📚 Konfigurations-Best-Practices

### Secrets Management

✅ **RICHTIG:**
```bash
# GCP Secret Manager nutzen
gcloud secrets create GOOGLE_BOOKS_API_KEY --data-file=api-key.txt
gcloud run services update SERVICE --set-secrets=GOOGLE_BOOKS_API_KEY=GOOGLE_BOOKS_API_KEY:latest
```

❌ **FALSCH:**
```bash
# API Keys in .env.yaml committen
GOOGLE_BOOKS_API_KEY: "AIza_real_key_here"
```

### Environment-Spezifische Configs

```bash
# Development
.env.development

# Staging
.env.staging

# Production
.env.production

# Nie .env Files committen!
# Nur .env.example mit Dummy-Werten
```

---

## 🔍 Konfiguration Debugging

### Agents (Cloud Run)

```bash
# Logs prüfen für geladene Config
gcloud run services logs read ingestion-agent --limit=100 | grep "Environment:"

# Environment Variables anzeigen
gcloud run services describe ingestion-agent --format="value(spec.template.spec.containers[0].env)"
```

### Backend

```bash
# Health Check mit Config anzeigen
curl https://backend-url/api/health

# Firestore Config prüfen
gcloud firestore indexes list
```

---

**Dokument-Version:** 2.0 (System-LLM Refactoring)  
**Vollständigkeit:** 95% (eBay Credentials pending)  
**Nächstes Update:** Nach Agent-Deployments  
**Wartung:** Sync mit Code-Änderungen erforderlich
