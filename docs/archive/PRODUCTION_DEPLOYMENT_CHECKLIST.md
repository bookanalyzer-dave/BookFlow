# Production Deployment Checklist

**Projekt:** Intelligent Book Sales Pipeline  
**Version:** 1.0  
**Letzte Aktualisierung:** 2025-11-01  
**GCP Project:** true-campus-475614-p4  
**Region:** europe-west1

---

## 📋 Inhaltsverzeichnis

1. [Pre-Deployment Phase](#pre-deployment-phase)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Agent Deployment](#agent-deployment)
4. [Configuration & Secrets](#configuration--secrets)
5. [Monitoring & Observability](#monitoring--observability)
6. [Testing & Validation](#testing--validation)
7. [Documentation](#documentation)
8. [Launch Phases](#launch-phases)
9. [Post-Launch](#post-launch)

---

## Legende

- ⛔ **CRITICAL** - Blocker für jedes Deployment
- 🔴 **HIGH** - Erforderlich für Beta/GA
- 🟡 **MEDIUM** - Empfohlen für GA
- 🟢 **LOW** - Nice-to-have / Post-Launch

**Zeitschätzungen:** Angegeben in Personentagen (PT) oder Stunden (h)

---

# Pre-Deployment Phase

**Geschätzte Dauer:** 5-10 Tage  
**Team:** Dev + DevOps + Security

## Code Review & Quality Gates

### ⛔ Critical
- [ ] **Code Freeze für Production Branch** (2h)
  - Main/Production Branch geschützt
  - Alle Features merged und getestet
  - Release-Tag erstellt (`v1.0.0-alpha`)

- [ ] **Security Code Review abgeschlossen** (2 PT)
  - Keine hardcoded Secrets/API Keys
  - Alle Credentials über Secret Manager
  - SQL Injection / XSS Vulnerabilities geprüft
  - OWASP Top 10 Review durchgeführt

### 🔴 High Priority
- [ ] **Automated Test Suite erfolgreich** (1 PT)
  - Unit Tests: >80% Coverage
  - Integration Tests: Alle kritischen Flows
  - E2E Tests durchgeführt ([`comprehensive_e2e_test.py`](comprehensive_e2e_test.py))
  - Status: ⚠️ **Noch nicht vollständig ausgeführt**

- [ ] **Python Environment validiert** (4h)
  - Python 3.11 oder 3.12 (NICHT 3.13 - Kompatibilitätsprobleme)
  - Alle Dependencies installierbar
  - Keine CVE-Vulnerabilities in Dependencies

- [ ] **Linting & Formatting Standards** (2h)
  - Black/Pylint durchgelaufen
  - Type Hints validiert
  - Import Order standardisiert

### 🟡 Medium Priority
- [ ] **Performance Profiling** (1 PT)
  - Memory Leaks geprüft
  - CPU-intensive Operations identifiziert
  - Database Query Optimization

- [ ] **Documentation Review** (4h)
  - Code Comments aktuell
  - README.md vollständig
  - API Docs generiert

---

## Security Audit

### ⛔ Critical
- [ ] **Firestore Security Rules deployed** (2h)
  - [`firestore.rules`](firestore.rules) validiert
  - Multi-Tenancy Isolation getestet
  - Service Account Permissions verifiziert
  - Status: ✅ **Implementiert, aber Test erforderlich**

- [ ] **Encryption at Rest aktiviert** (1h)
  - Firestore: Standard GCP Encryption
  - Cloud Storage: Customer-Managed Keys (optional)
  - Secret Manager für alle Credentials

- [ ] **API Authentication** (4h)
  - Firebase Auth JWT-Validation funktional
  - Token Expiry & Refresh implementiert
  - Authorization Middleware aktiv
  - Status: ✅ **Implementiert**

### 🔴 High Priority
- [ ] **External Penetration Test** (3-5 PT)
  - **Empfohlener Vendor:** HackerOne, Bugcrowd
  - OWASP Testing gegen alle Endpoints
  - DDoS Resistance Test
  - **Timeline:** 2 Wochen vor GA-Launch

- [ ] **Secret Rotation Plan** (1 PT)
  - Service Account Keys rotierbar
  - API Keys rotation documented
  - Emergency Rotation Procedure

- [ ] **Rate Limiting konfiguriert** (1 PT)
  - Cloud Armor Rules für Dashboard Backend
  - Per-User Rate Limits (LLM Usage)
  - Firestore Write Limits
  - **Aktueller Status:** ⚠️ Nur Provider-Level, nicht global

### 🟡 Medium Priority
- [ ] **GDPR Compliance Check** (2 PT)
  - Data Retention Policies definiert
  - User Data Export Functionality
  - Right to be Forgotten implementiert
  - Privacy Policy aktualisiert

- [ ] **Vulnerability Scanning** (4h)
  - Snyk/Dependabot aktiviert
  - Container Image Scanning (GCR)
  - Infrastructure as Code Scanning

---

## Performance Testing

### 🔴 High Priority
- [ ] **Load Testing durchgeführt** (2-3 PT)
  - Tool: Apache JMeter / Locust / k6
  - **Target:** 100 concurrent users
  - **Test Scenarios:**
    - Image Upload unter Last
    - Simultane LLM Requests
    - Firestore Query Performance
  - **Aktueller Status:** ❌ **NICHT DURCHGEFÜHRT**

- [ ] **Stress Testing** (1 PT)
  - System Breaking Point identifiziert
  - Graceful Degradation verifiziert
  - Auto-Scaling Behavior getestet

- [ ] **Latency Benchmarks dokumentiert** (4h)
  - Response Time Targets definiert:
    - Auth: <500ms ✅
    - Image Upload: <1s ✅
    - Condition Assessment: <30s ✅
    - Pricing: <10s ✅

### 🟡 Medium Priority
- [ ] **Database Query Optimization** (1 PT)
  - Composite Indices für häufige Queries
  - Query Explain Plans analysiert
  - N+1 Query Problems behoben

- [ ] **CDN Configuration für Frontend** (4h)
  - Cloud CDN oder Cloudflare
  - Static Asset Caching
  - GZIP Compression

---

## Dependency Management

### 🔴 High Priority
- [ ] **Dependency Lock Files aktualisiert** (2h)
  - `requirements.txt` gepinnt auf exakte Versionen
  - `package-lock.json` committed
  - Docker Base Images getaggt

- [ ] **Vulnerability Scan durchgeführt** (2h)
  ```bash
  pip-audit
  npm audit
  ```

### 🟡 Medium Priority
- [ ] **License Compliance Check** (4h)
  - Alle Dependencies GPL-kompatibel
  - License.txt generiert

---

## Backup & Rollback Strategy

### ⛔ Critical
- [ ] **Firestore Backup konfiguriert** (2h)
  - Automated Daily Backups
  - Point-in-Time Recovery (7 Tage)
  - Backup Restore getestet

- [ ] **Rollback Procedure dokumentiert** (4h)
  - Cloud Run Revision Rollback
  - Database Schema Rollback Plan
  - Emergency Contacts definiert

### 🔴 High Priority
- [ ] **Blue-Green Deployment Setup** (1 PT)
  - Traffic Splitting konfiguriert
  - Canary Deployment möglich
  - Instant Rollback verfügbar

---

## Incident Response Plan

### 🔴 High Priority
- [ ] **On-Call Rotation definiert** (4h)
  - PagerDuty / Opsgenie Setup
  - Escalation Matrix
  - Shift Schedule (für GA)

- [ ] **Runbooks erstellt** (2 PT)
  - Common Issues & Fixes
  - Service Restart Procedures
  - Database Recovery Steps
  - **Aktueller Status:** ❌ **NICHT VORHANDEN**

### 🟡 Medium Priority
- [ ] **Post-Mortem Template** (2h)
  - Root Cause Analysis Format
  - Action Items Tracking

---

# Infrastructure Setup

**Geschätzte Dauer:** 3-5 Tage  
**Team:** DevOps + Backend

## GCP Project Configuration

### ⛔ Critical
- [ ] **GCP Project erstellt & konfiguriert** (1h)
  - Project ID: `true-campus-475614-p4` ✅
  - Billing Account verknüpft
  - Budget Alerts konfiguriert (monatlich)

- [ ] **IAM & Service Accounts** (4h)
  - Least-Privilege Principle angewendet
  - Service Accounts pro Agent
  - **Aktueller Status:** ⚠️ Breite Rechte für Testing

- [ ] **APIs aktiviert** (30min)
  ```bash
  gcloud services enable \
    run.googleapis.com \
    pubsub.googleapis.com \
    storage.googleapis.com \
    firestore.googleapis.com \
    vision.googleapis.com \
    aiplatform.googleapis.com \
    secretmanager.googleapis.com \
    cloudbuild.googleapis.com \
    logging.googleapis.com \
    monitoring.googleapis.com \
    clouderrorreporting.googleapis.com
  ```
  - Status: ✅ **Basis-APIs aktiviert** (siehe [`setup_gcp.sh`](setup_gcp.sh))

### 🔴 High Priority
- [ ] **VPC & Networking** (4h)
  - VPC Peering für Firestore
  - Cloud NAT für egress traffic
  - Firewall Rules dokumentiert

- [ ] **Cost Optimization** (1 PT)
  - Committed Use Discounts geprüft
  - Cloud Run Min/Max Instances konfiguriert
  - Budget Alerts bei 50%, 80%, 100%

---

## Firebase/Firestore Setup

### ⛔ Critical
- [ ] **Firebase Project erstellt** (30min)
  - Firebase Console konfiguriert
  - Authentication aktiviert
  - Status: ✅ **Configured**

- [ ] **Firestore Database** (1h)
  - Native Mode aktiviert ✅
  - Region: `europe-west1` ✅
  - Security Rules deployed
  - Composite Indices erstellt

- [ ] **Firestore Collections strukturiert** (2h)
  ```
  /users/{userId}/
    ├── books/{bookId}
    ├── llm_credentials/{credId}
    ├── llm_usage/{usageId}
    ├── llm_settings/config
    ├── llm_audit/{auditId}
    └── condition_assessments/{assessmentId}
  ```
  - Status: ✅ **Implementiert**

### 🔴 High Priority
- [ ] **TTL Policies konfiguriert** (1h)
  - `market_data`: 60 Tage TTL
  - `llm_audit`: 90 Tage TTL
  - Old Image URLs: 30 Tage

- [ ] **Backup Schedule** (2h)
  - Daily Automated Backups
  - Retention: 30 Tage
  - Cross-Region Backup (optional)

---

## Cloud Storage Buckets

### ⛔ Critical
- [ ] **Buckets erstellt & konfiguriert** (1h)
  - `${PROJECT_ID}-book-images` ✅
  - Lifecycle Policy: Delete nach 90 Tagen
  - CORS Configuration für Frontend

- [ ] **Access Control** (2h)
  - Signed URLs für Uploads ✅
  - User-specific Upload Paths ✅
  - Public Read deaktiviert

### 🔴 High Priority
- [ ] **CDN Integration** (2h)
  - Cloud CDN für Image Delivery
  - Cache Control Headers

---

## Cloud Functions / Cloud Run Deployment

### ⛔ Critical
- [ ] **Container Registry Setup** (30min)
  - GCR oder Artifact Registry
  - Image Tagging Strategy

- [ ] **Alle Agents deployed** (siehe [Agent Deployment](#agent-deployment))

### 🔴 High Priority
- [ ] **Auto-Scaling konfiguriert** (2h)
  - Min Instances: 1 (für kritische Services)
  - Max Instances: 100 (oder nach Load Test)
  - CPU/Memory Limits gesetzt

- [ ] **Health Checks aktiviert** (1h)
  - Liveness Probes
  - Readiness Probes

---

## Pub/Sub Topics & Subscriptions

### ⛔ Critical
- [ ] **Topics erstellt** (30min)
  ```
  - book-analyzed ✅
  - book-identified ✅
  - market-data-updated ✅
  - book-listing-requests ✅
  - delist-book-everywhere ✅
  - sale-notification-received ✅
  ```
  - Status: ✅ **Erstellt** (siehe [`cloudbuild.yaml`](cloudbuild.yaml))

- [ ] **Subscriptions konfiguriert** (1h)
  - Retry Policies definiert
  - Dead Letter Topics eingerichtet
  - **Aktueller Status:** ⚠️ DLQ fehlt

### 🔴 High Priority
- [ ] **Message Ordering** (2h)
  - Bei kritischen Flows aktiviert
  - Idempotency sichergestellt

---

## Vertex AI Setup

### ⛔ Critical
- [ ] **Vertex AI APIs aktiviert** (15min)
  - `aiplatform.googleapis.com` ✅
  - Quota Limits geprüft

- [ ] **Model Access verifiziert** (1h)
  - Gemini 2.0 Flash verfügbar ✅
  - Vision Model zugänglich ✅
  - Rate Limits dokumentiert

### 🔴 High Priority
- [ ] **Cost Monitoring für LLM Usage** (1 PT)
  - Budget Alerts pro User
  - Cost Attribution Tags

---

## SSL/TLS Certificates

### 🔴 High Priority
- [ ] **Custom Domain konfiguriert** (2h)
  - Domain auf Cloud Run gemappt
  - Managed SSL Certificate
  - HTTPS erzwungen

### 🟡 Medium Priority
- [ ] **Certificate Renewal automatisiert** (1h)
  - Let's Encrypt Auto-Renewal
  - Expiry Monitoring

---

# Agent Deployment

**Geschätzte Dauer:** 2-3 Tage  
**Team:** Backend + DevOps

Alle Agents werden als **Cloud Run Services** deployed. Basis-Deployment via [`cloudbuild.yaml`](cloudbuild.yaml) ✅

## Ingestion Agent

### ⛔ Critical
- [ ] **Docker Image gebaut & gepusht** (30min)
  ```bash
  docker build -t gcr.io/${PROJECT}/ingestion-agent:latest \
    -f agents/ingestion-agent/Dockerfile .
  docker push gcr.io/${PROJECT}/ingestion-agent:latest
  ```
  - Status: ✅ **In cloudbuild.yaml**

- [ ] **Cloud Run Service deployed** (15min)
  - Memory: 512Mi ✅
  - CPU: 1
  - Max Instances: 10
  - Status: ✅ **Configured**

- [ ] **Eventarc Trigger erstellt** (30min)
  - Topic: `book-analyzed` ✅
  - Service Account: `ingestion-agent-invoker` ✅
  - Status: ✅ **Configured**

### 🔴 High Priority
- [ ] **Environment Variables gesetzt** (15min)
  ```yaml
  GCP_PROJECT_ID: true-campus-475614-p4
  VERTEX_AI_LOCATION: europe-west1
  GOOGLE_BOOKS_API_KEY: (from Secret Manager)
  ```

- [ ] **Integration Tests durchgeführt** (1 PT)
  - Multi-Image Upload
  - Google Books API Integration
  - Vertex AI Vision Analysis
  - **Status:** ⚠️ **Teilweise getestet**

### 🟡 Medium Priority
- [ ] **Smoke Tests nach Deployment** (30min)
  - Manual Upload Test
  - Log Verification

---

## Condition Assessor Agent

### ⛔ Critical
- [ ] **Docker Image deployed** (30min)
  - Image: `condition-assessor:latest` ✅
  - Memory: 512Mi ✅

- [ ] **Firestore Trigger konfiguriert** (30min)
  - Collection: `users/{userId}/books`
  - Event: onCreate/onUpdate
  - **Status:** ⚠️ **Trigger-Mechanismus prüfen**

### 🔴 High Priority
- [ ] **Condition Assessment Tests** (1 PT)
  - Test mit echten Buchbildern
  - Grading Accuracy validiert
  - Price Factor Calculation getestet
  - **Status:** ⚠️ **Keine Live-Tests**

- [ ] **Manual Override UI funktional** (2h)
  - User kann Assessment korrigieren
  - Reprocessing triggert korrekt

---

## Strategist Agent

### ⛔ Critical
- [ ] **Docker Image deployed** (30min)
  - Image: `strategist-agent:latest` ✅
  - Memory: 512Mi ✅

- [ ] **Eventarc Trigger** (30min)
  - Topic: `market-data-updated` ✅
  - Service Account: `strategist-agent-invoker` ✅

### 🔴 High Priority
- [ ] **Pricing Algorithm validiert** (2 PT)
  - Backtest gegen historische Daten
  - Competitor Price Analysis
  - **Status:** ❌ **NICHT VALIDIERT**

- [ ] **Google Books API Integration** (1h)
  - Rate Limits respektiert
  - Error Handling getestet

### 🟡 Medium Priority
- [ ] **A/B Testing Framework** (3 PT)
  - Pricing Strategy Variants
  - Conversion Tracking

---

## Scribe Agent

### 🟡 Medium Priority
- [ ] **Agent deployed (wenn noch separat)** (1h)
  - **Note:** Funktionalität in Ingestion Agent integriert
  - Separater Agent optional für Rewrite-Funktionalität

- [ ] **Description Quality Metrics** (2 PT)
  - Human Review Process
  - Quality Scoring
  - **Status:** ❌ **NICHT VORHANDEN**

---

## Ambassador Agent

### ⛔ Critical
- [ ] **Docker Image deployed** (30min)
  - Image: `ambassador-agent:latest` ✅
  - Memory: 1Gi ✅

- [ ] **Eventarc Triggers** (1h)
  - Topic: `book-listing-requests` ✅
  - Topic: `delist-book-everywhere` ✅

### 🔴 High Priority
- [ ] **eBay API Production Testing** (2-3 PT)
  - OAuth Flow verifiziert
  - Sandbox Listings erstellt
  - Production Credentials gesetzt
  - **Status:** ⚠️ **Nur Sandbox**

- [ ] **Listing Lifecycle Tests** (1 PT)
  - Create → Update → Delete
  - Error Handling für API Failures
  - Inventory Sync

### 🟡 Medium Priority
- [ ] **Multi-Platform Support** (5+ PT)
  - Amazon Integration
  - AbeBooks Integration
  - Platform-agnostic Architecture ✅

---

## Sentinel Agent & Webhook

### ⛔ Critical
- [ ] **Sentinel Webhook deployed** (30min)
  - Image: `sentinel-webhook:latest` ✅
  - Allow Unauthenticated (für eBay Webhooks) ✅

- [ ] **Sentinel Agent deployed** (30min)
  - Event Processing Logic
  - Status Update zu Firestore

### 🔴 High Priority
- [ ] **Webhook Security** (1 PT)
  - eBay Signature Validation
  - Rate Limiting
  - IP Whitelisting (optional)

- [ ] **End-to-End Sale Test** (1 PT)
  - Mock Sale Event
  - Delisting getriggert
  - Status Updates verifiziert

---

## Scout Agent

### 🟡 Medium Priority
- [ ] **Cloud Run Service deployed** (30min)
  - Image: `scout-agent:latest` ✅
  - Periodisches Scheduling

- [ ] **Cloud Scheduler konfiguriert** (1h)
  - Täglicher Run
  - Market Data Collection
  - TTL Policy aktiv (60 Tage)

- [ ] **Web Scraping Legal Compliance** (1 PT)
  - robots.txt respektiert
  - Rate Limiting implementiert

---

# Configuration & Secrets

**Geschätzte Dauer:** 1-2 Tage  
**Team:** DevOps + Security

## Secret Manager

### ⛔ Critical
- [ ] **Secret Manager aktiviert** (15min)
  ```bash
  gcloud services enable secretmanager.googleapis.com
  ```

- [ ] **Alle Secrets migriert** (2h)
  ```
  - FIREBASE_SERVICE_ACCOUNT_KEY ✅
  - GOOGLE_BOOKS_API_KEY
  - EBAY_OAUTH_CLIENT_ID
  - EBAY_OAUTH_CLIENT_SECRET
  - ENCRYPTION_KEY (User LLM Management)
  - DATABASE_ENCRYPTION_KEY
  ```

- [ ] **Service Account Access konfiguriert** (1h)
  - Agents haben Secret Accessor Role
  - Principle of Least Privilege

### 🔴 High Priority
- [ ] **Secret Rotation Plan** (1 PT)
  - Dokumentierte Rotation Procedures
  - Emergency Rotation getestet

---

## Environment Variables

### ⛔ Critical
- [ ] **Environment Variables pro Agent gesetzt** (2h)
  - Über Cloud Run Console oder `.env.yaml`
  - Keine Secrets in Environment Variables (nur Referenzen)

### Beispiel für Ingestion Agent:
```yaml
GCP_PROJECT_ID: true-campus-475614-p4
VERTEX_AI_LOCATION: europe-west1
FIRESTORE_DATABASE: (default)
GOOGLE_BOOKS_API_KEY: (Secret Manager Referenz)
```

---

## API Keys & Third-Party Credentials

### 🔴 High Priority
- [ ] **eBay Production Credentials** (1 PT)
  - OAuth Client ID/Secret
  - Developer Account verifiziert
  - Sandbox → Production Migration
  - **Status:** ⚠️ **Sandbox-Only**

- [ ] **Google Books API Key** (1h)
  - Production Quota erhöht
  - Rate Limits dokumentiert

### 🟡 Medium Priority
- [ ] **Future API Integrations vorbereitet** (4h)
  - Amazon MWS
  - AbeBooks Partner API

---

## Firebase Configuration

### ⛔ Critical
- [ ] **Firebase SDK Config im Frontend** (30min)
  - [`dashboard/frontend/src/firebaseConfig.js`](dashboard/frontend/src/firebaseConfig.js) ✅
  - API Keys korrekt (Public ist OK für Firebase Client)

- [ ] **Service Account Key für Backend** (30min)
  - [`service-account-key.json`](service-account-key.json) ✅
  - **WICHTIG:** Nicht in Git committen ✅

---

# Monitoring & Observability

**Geschätzte Dauer:** 2-3 Tage  
**Team:** DevOps + Backend

## Cloud Logging

### ⛔ Critical
- [ ] **Cloud Logging aktiviert** (15min)
  ```bash
  gcloud services enable logging.googleapis.com
  ```
  - **Status:** ❌ **NICHT KONFIGURIERT**

- [ ] **Log Sinks konfiguriert** (1h)
  - Error Logs → BigQuery
  - Audit Logs → Cloud Storage
  - Log Retention: 30 Tage

### 🔴 High Priority
- [ ] **Structured Logging implementiert** (1 PT)
  - JSON Format
  - Consistent Log Levels
  - Trace IDs für Request Tracking

- [ ] **Log-based Metrics** (2h)
  - Error Rate per Agent
  - LLM Request Count
  - Upload Success Rate

---

## Error Reporting

### ⛔ Critical
- [ ] **Error Reporting aktiviert** (15min)
  ```bash
  gcloud services enable clouderrorreporting.googleapis.com
  ```
  - **Status:** ❌ **NICHT KONFIGURIERT**

- [ ] **Error Tracking integriert** (1h)
  - Python Error Reporting Client
  - Automatic Exception Capture
  - Stack Traces verfügbar

### 🔴 High Priority
- [ ] **Error Alerting** (2h)
  - PagerDuty Integration
  - Slack Notifications
  - Error Rate Thresholds

---

## Cloud Monitoring Dashboards

### 🔴 High Priority
- [ ] **Custom Dashboards erstellt** (1 PT)
  
  **Dashboard 1: System Health**
  - Cloud Run Request Count
  - Error Rate per Service
  - P50/P95/P99 Latencies
  - CPU/Memory Usage

  **Dashboard 2: Business Metrics**
  - Books Uploaded (Daily/Weekly)
  - LLM Requests per Provider
  - Listings Created
  - Sales Notifications

  **Dashboard 3: Cost Monitoring**
  - LLM Cost per User
  - Cloud Run Cost
  - Firestore Read/Write Cost

### 🟡 Medium Priority
- [ ] **Grafana Integration** (1 PT)
  - Advanced Visualizations
  - Custom Queries

---

## Alerts & Notifications

### 🔴 High Priority
- [ ] **Critical Alerts konfiguriert** (1 PT)
  
  **Alert 1: High Error Rate**
  - Condition: Error Rate > 5% für 5min
  - Notification: PagerDuty P1
  
  **Alert 2: Service Down**
  - Condition: Health Check fails 3x
  - Notification: PagerDuty P0
  
  **Alert 3: High Latency**
  - Condition: P95 > 10s für 10min
  - Notification: Slack
  
  **Alert 4: Budget Exceeded**
  - Condition: Daily Cost > Threshold
  - Notification: Email + Slack

### 🟡 Medium Priority
- [ ] **Warning Alerts** (4h)
  - LLM Quota Approaching Limit
  - Firestore Write Anomaly
  - Unusual Traffic Patterns

---

## Performance Metrics & Tracing

### 🔴 High Priority
- [ ] **Cloud Trace aktiviert** (1h)
  - Distributed Tracing
  - Request Flow Visualization
  - Bottleneck Identification

- [ ] **Custom Metrics** (1 PT)
  ```python
  - llm_request_duration
  - book_processing_time
  - marketplace_listing_success_rate
  ```

### 🟡 Medium Priority
- [ ] **Profiling aktiviert** (2h)
  - Cloud Profiler
  - Memory/CPU Profiling

---

## Usage Analytics

### 🔴 High Priority
- [ ] **LLM Usage Tracking Dashboard** (1 PT)
  - Cost per User/per Agent
  - Provider Distribution
  - Token Usage Trends
  - **Status:** ✅ **Backend implementiert** ([`tracking/usage.py`](shared/user_llm_manager/tracking/usage.py))

- [ ] **User Activity Analytics** (1 PT)
  - Daily Active Users
  - Books Uploaded per User
  - Listing Success Rate

### 🟡 Medium Priority
- [ ] **Google Analytics Integration** (4h)
  - Frontend User Behavior
  - Conversion Funnels

---

# Testing & Validation

**Geschätzte Dauer:** 3-5 Tage  
**Team:** QA + Backend

## Smoke Tests nach Deployment

### ⛔ Critical
- [ ] **Basic Functionality Tests** (2h)
  - User Registration/Login ✅
  - Image Upload ✅
  - Book Display ✅
  - LLM Settings Update ✅

- [ ] **Agent Health Checks** (1h)
  ```bash
  # Jeder Agent Endpoint erreichbar
  curl https://ingestion-agent-xxx.run.app/health
  curl https://strategist-agent-xxx.run.app/health
  # etc.
  ```

### 🔴 High Priority
- [ ] **Critical User Flows** (2h)
  - End-to-End Book Upload → Listing
  - LLM Provider Switch
  - Condition Assessment Override

---

## End-to-End Tests in Production Environment

### 🔴 High Priority
- [ ] **E2E Test Suite ausgeführt** (1 PT)
  - [`comprehensive_e2e_test.py`](comprehensive_e2e_test.py) gegen Production
  - Alle 11 Test-Kategorien
  - **Status:** ❌ **NOCH NICHT GEGEN PRODUCTION**

- [ ] **Multi-User Isolation Tests** (4h)
  - 2+ Test Users simultan
  - Cross-User Access verhindern
  - Data Leakage prüfen

### 🟡 Medium Priority
- [ ] **Browser Compatibility Tests** (4h)
  - Chrome, Firefox, Safari, Edge
  - Mobile Responsive Design

---

## Load Testing

### 🔴 High Priority (für Beta)
- [ ] **Load Test mit 100 concurrent users** (2 PT)
  - Tool: Apache JMeter / Locust
  - Test Duration: 30min
  - Scenarios:
    - Image Upload Storm
    - Simultane Listings
    - Heavy LLM Usage
  - **Status:** ❌ **NICHT DURCHGEFÜHRT**

- [ ] **Ergebnisse dokumentiert** (4h)
  - Response Time Distribution
  - Error Rate unter Last
  - Resource Utilization
  - Bottlenecks identifiziert

### 🟡 Medium Priority (für GA)
- [ ] **Spike Test** (1 PT)
  - Sudden Traffic Increase
  - Auto-Scaling Behavior

- [ ] **Endurance Test** (1 PT)
  - 24h Continuous Load
  - Memory Leaks identifiziert

---

## Failover & Recovery Tests

### 🔴 High Priority
- [ ] **Database Restore Test** (2h)
  - Firestore Backup → Restore
  - Point-in-Time Recovery
  - Data Integrity verifiziert

- [ ] **Service Failure Simulation** (1 PT)
  - Agent Crash → Auto-Restart
  - Pub/Sub Message Retry
  - Circuit Breaker Behavior

### 🟡 Medium Priority
- [ ] **Disaster Recovery Drill** (4h)
  - Complete System Restore
  - RTO/RPO Targets erreicht

---

## Security Penetration Tests

### 🔴 High Priority (vor GA)
- [ ] **OWASP Top 10 Tests** (3 PT)
  - SQL Injection (Firestore)
  - XSS (Frontend)
  - CSRF Protection
  - Authentication Bypass
  - **Timeline:** 2-3 Wochen vor GA

- [ ] **API Security Tests** (1 PT)
  - JWT Token Manipulation
  - Authorization Bypass
  - Rate Limiting Evasion

### 🟡 Medium Priority
- [ ] **Infrastructure Security Scan** (1 PT)
  - Open Ports
  - Misconfigured IAM Roles
  - Public Buckets

---

# Documentation

**Geschätzte Dauer:** 2-3 Tage  
**Team:** Tech Writer + Dev

## API Documentation

### 🔴 High Priority
- [ ] **OpenAPI/Swagger Spec generiert** (1 PT)
  - Alle Dashboard Backend Endpoints
  - Request/Response Schemas
  - Authentication Requirements

- [ ] **API Documentation hosted** (4h)
  - Swagger UI deployed
  - Beispiel Requests

### 🟡 Medium Priority
- [ ] **Postman Collection** (4h)
  - Vorkonfigurierte Requests
  - Environment Variables

---

## Operations Runbooks

### 🔴 High Priority
- [ ] **Runbook: Service Restart** (2h)
  ```markdown
  # Service Restart Procedure
  1. Identify failing service
  2. Check logs for errors
  3. Roll back to previous version
  4. ...
  ```

- [ ] **Runbook: Database Recovery** (2h)
  - Backup Restore Steps
  - Data Validation

- [ ] **Runbook: Emergency Procedures** (2h)
  - System-wide Outage
  - Security Breach Response
  - DDoS Mitigation

- [ ] **Runbook: Common Issues** (1 PT)
  - LLM API Failures
  - eBay Listing Errors
  - Image Upload Issues
  - **Status:** ❌ **NICHT VORHANDEN**

### 🟡 Medium Priority
- [ ] **Runbook: Scaling Operations** (4h)
  - Manual Scaling Steps
  - Performance Tuning

---

## User Documentation

### 🔴 High Priority
- [ ] **User Guide erstellt** (1 PT)
  - Getting Started
  - Uploading Books
  - LLM Settings Configuration
  - Troubleshooting

- [ ] **FAQ Dokument** (4h)
  - Common Questions
  - Error Messages Explained

### 🟡 Medium Priority
- [ ] **Video Tutorials** (2 PT)
  - Onboarding Walkthrough
  - Advanced Features

---

## Deployment Playbook

### 🔴 High Priority
- [ ] **Deployment Commands dokumentiert** (4h)
  - Siehe [`DEPLOYMENT_COMMANDS.md`](DEPLOYMENT_COMMANDS.md) (zu erstellen)
  - Step-by-Step Deployment
  - Rollback Procedures

- [ ] **Change Log Template** (1h)
  - Version Numbering
  - Release Notes Format

---

## Disaster Recovery Procedures

### 🔴 High Priority
- [ ] **DR Plan dokumentiert** (1 PT)
  - RPO/RTO Targets definiert
  - Backup Locations
  - Recovery Steps
  - Contact Information

- [ ] **Business Continuity Plan** (1 PT)
  - Communication Plan
  - Stakeholder Notification

---

# Launch Phases

## 🟢 Alpha Launch Checklist (10-50 Users)

**Timeline:** Ready NOW (nach Pre-Deployment Fixes)  
**Duration:** 2-4 Wochen  
**Monitoring:** Manual / Daily Check-ins

### Requirements
- [x] User Authentication funktional ✅
- [x] Basic Upload Pipeline ✅
- [x] LLM Management ✅
- [ ] Error Monitoring aktiviert ⛔
- [ ] Manual Support verfügbar
- [ ] Rollback Plan dokumentiert ⛔
- [ ] Alpha User Consent & NDA

### Success Metrics
- 0 Critical Bugs
- <1% Error Rate
- User Feedback collected
- System stable für 1 Woche

### Can Skip (für Alpha)
- Load Testing
- External Penetration Tests
- 24/7 On-Call
- Multi-Platform Listings
- Advanced Analytics

### Action Items
1. Fix Critical Pre-Deployment Items
2. Activate Cloud Logging & Error Reporting
3. Create Emergency Contact List
4. Recruit 10-20 Alpha Users
5. Schedule Daily Check-ins

**Status:** ⚠️ **Fast bereit - Critical Items erforderlich**

---

## 🟡 Beta Launch Checklist (100-500 Users)

**Timeline:** 1-2 Wochen nach Alpha (wenn stabil)  
**Duration:** 4-8 Wochen  
**Monitoring:** Automated / Weekly Reviews

### Requirements (zusätzlich zu Alpha)
- [ ] Load Testing abgeschlossen (100 concurrent users) 🔴
- [ ] Automated Monitoring & Alerting 🔴
- [ ] Error Rate <0.5%
- [ ] Response Time Targets validiert 🔴
- [ ] Runbooks für häufige Issues 🔴
- [ ] eBay Sandbox Tests erfolgreich 🔴
- [ ] Rate Limiting konfiguriert 🔴
- [ ] Basic On-Call Rotation (Business Hours)

### Success Metrics
- <0.1% Critical Error Rate
- P95 Latency <5s
- User Retention >60%
- NPS Score >40

### Can Still Skip (für Beta)
- 24/7 On-Call
- Multi-Marketplace Support
- Advanced Analytics Dashboard
- External Penetration Tests (wenn Budget knapp)

### Action Items
1. Complete all HIGH Priority Items
2. Setup Automated Alerts
3. Conduct Load Testing
4. Create User Onboarding Flow
5. Establish Support Ticket System

**Status:** ⚠️ **Erfordert 1-2 Wochen Vorbereitung**

---

## 🔴 General Availability Checklist (1000+ Users)

**Timeline:** 4-6 Wochen nach Beta  
**Duration:** Indefinite (Production)  
**Monitoring:** 24/7 / Real-time Alerting

### Requirements (ALL must be ✅)
- [ ] ALL High Priority Items abgeschlossen ⛔
- [ ] External Penetration Test bestanden 🔴
- [ ] Load Testing für 1000+ users 🔴
- [ ] 24/7 On-Call Team bereit 🔴
- [ ] SLA Targets definiert & validiert 🔴
  - Uptime: 99.9% (43min downtime/month)
  - Response Time: P95 <2s
  - Error Rate: <0.01%
- [ ] Disaster Recovery getestet 🔴
- [ ] GDPR Compliance vollständig 🔴
- [ ] Legal Terms & Privacy Policy finalisiert 🔴
- [ ] Customer Support Team trainiert 🔴
- [ ] Marketing/PR Launch Plan 🔴

### Success Metrics
- 99.9% Uptime
- <0.01% Error Rate
- NPS Score >50
- User Acquisition Cost optimiert

### Must Have (nicht optional)
- Automated Incident Response
- Performance Optimization abgeschlossen
- Cost Optimization implementiert
- Multi-Region Deployment (optional, aber empfohlen)
- Comprehensive Analytics

### Action Items
1. Complete ALL Critical & High Priority Items
2. Conduct Full Security Audit
3. Setup 24/7 Support
4. Finalize Legal Documentation
5. Prepare Marketing Launch

**Status:** ❌ **4-6 Wochen Vorbereitung erforderlich**

---

# Post-Launch

## Week 1 Post-Launch

### ⛔ Critical
- [ ] **Daily Health Checks** (15min/Tag)
  - Error Rate Monitoring
  - User Feedback Review
  - System Performance

- [ ] **Incident Response bereit** (24/7)
  - On-Call erreichbar
  - Escalation funktional

### 🔴 High Priority
- [ ] **User Feedback Collection** (ongoing)
  - In-App Surveys
  - Support Ticket Analysis
  - Feature Requests logged

- [ ] **Performance Monitoring** (2x täglich)
  - Dashboard Review
  - Anomaly Detection
  - Cost Tracking

---

## Month 1 Post-Launch

### 🔴 High Priority
- [ ] **Post-Launch Review** (4h)
  - What went well?
  - What went wrong?
  - Action Items für Verbesserungen

- [ ] **Performance Optimization** (1 PT)
  - Bottlenecks addressed
  - Cost Optimization
  - Query Performance Tuning

### 🟡 Medium Priority
- [ ] **Feature Enhancements** (ongoing)
  - Based on User Feedback
  - Roadmap Prioritization

- [ ] **Documentation Updates** (4h)
  - Known Issues
  - FAQ erweitert

---

## Ongoing (Quarterly)

### 🟡 Medium Priority
- [ ] **Security Audit** (1 PT)
  - Dependency Updates
  - Vulnerability Scanning
  - Penetration Testing

- [ ] **Disaster Recovery Drill** (4h)
  - Test Backup Restore
  - Validate RTO/RPO

- [ ] **Capacity Planning** (1 PT)
  - Growth Projections
  - Infrastructure Scaling
  - Budget Forecasting

---

# Summary: Critical Path to Launch

## Für Alpha Launch (✅ GO)
**Timeline:** 3-5 Tage

1. ⛔ Cloud Logging & Error Reporting aktivieren (2h)
2. ⛔ Firestore Security Rules validieren (2h)
3. ⛔ Backup & Rollback Plan dokumentieren (4h)
4. ⛔ Emergency Contact List erstellen (1h)
5. 🔴 Basic Runbooks erstellen (4h)
6. 🔴 Smoke Tests durchführen (2h)

**Geschätzt:** 1-2 PT

---

## Für Beta Launch (⚠️ 1-2 Wochen)
**Timeline:** 10-15 Tage nach Alpha

1. 🔴 Load Testing durchführen (2 PT)
2. 🔴 Automated Monitoring & Alerting (1 PT)
3. 🔴 eBay Sandbox Tests (2 PT)
4. 🔴 Rate Limiting implementieren (1 PT)
5. 🔴 Operations Runbooks vervollständigen (1 PT)
6. 🔴 On-Call Rotation setup (4h)

**Geschätzt:** 7-8 PT

---

## Für GA Launch (❌ 4-6 Wochen)
**Timeline:** 30-45 Tage nach Beta

1. 🔴 External Penetration Test (3-5 PT + 2 Wochen Vendor)
2. 🔴 Load Testing für 1000+ users (2 PT)
3. 🔴 24/7 On-Call Team & Training (2 PT)
4. 🔴 GDPR Compliance finalisieren (2 PT)
5. 🔴 Disaster Recovery Tests (1 PT)
6. 🔴 Legal & Privacy Policy (1 PT + Legal Review)
7. 🟡 Performance Optimization (2 PT)
8. 🟡 Cost Optimization (1 PT)
9. 🟡 Advanced Analytics (1 PT)

**Geschätzt:** 15-20 PT + External Dependencies

---

# Kontakte & Verantwortlichkeiten

## Rollen

| Rolle | Verantwortlich für | Kontakt |
|-------|-------------------|---------|
| **Project Lead** | Overall Coordination | TBD |
| **DevOps Lead** | Infrastructure, Deployment | TBD |
| **Backend Lead** | Agent Development, APIs | TBD |
| **Frontend Lead** | Dashboard, User Experience | TBD |
| **Security Lead** | Security Audit, Compliance | TBD |
| **QA Lead** | Testing, Validation | TBD |

## On-Call Rotation (für Beta/GA)

| Week | Primary | Secondary | Escalation |
|------|---------|-----------|------------|
| Week 1 | TBD | TBD | Project Lead |
| Week 2 | TBD | TBD | Project Lead |
| ... | | | |

---

**Dokument-Version:** 1.0  
**Erstellt am:** 2025-11-01  
**Nächstes Review:** Nach Alpha Launch  
**Änderungen:** Tracking in Git History

---

## Changelog

| Datum | Version | Änderungen | Author |
|-------|---------|------------|--------|
| 2025-11-01 | 1.0 | Initial Checklist basierend auf E2E-Test-Report | Architect Mode |