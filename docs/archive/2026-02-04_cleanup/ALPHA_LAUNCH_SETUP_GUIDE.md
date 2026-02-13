# Alpha Launch Setup Guide

## 🎯 Übersicht

Dieser Guide führt dich durch das Setup der GCP-Infrastruktur für den Alpha Launch des Book Management Systems. Die Scripts automatisieren das Setup von Cloud Logging, Error Reporting, GCP-Ressourcen und Secrets.

---

## ✅ Voraussetzungen

### Erforderliche Tools
- [ ] **Python 3.9+** installiert
- [ ] **gcloud CLI** installiert und authentifiziert
- [ ] **GCP Project**: `true-campus-475614-p4` aktiv
- [ ] **Bash Shell** (für .sh Scripts unter Windows: Git Bash oder WSL)

### Erforderliche Python Packages
```bash
pip install google-cloud-logging google-cloud-error-reporting google-api-core python-json-logger
```

### Erforderliche GCP APIs
Die Scripts aktivieren folgende APIs automatisch:
- Cloud Run API (`run.googleapis.com`)
- Cloud Pub/Sub API (`pubsub.googleapis.com`)
- Cloud Storage API (`storage.googleapis.com`)
- Firestore API (`firestore.googleapis.com`)
- Vision API (`vision.googleapis.com`)
- Vertex AI API (`aiplatform.googleapis.com`)
- Secret Manager API (`secretmanager.googleapis.com`)
- Cloud Build API (`cloudbuild.googleapis.com`)
- Cloud Logging API (`logging.googleapis.com`)
- Error Reporting API (`clouderrorreporting.googleapis.com`)

### Erforderliche IAM Permissions
Dein GCP-Benutzer benötigt folgende Rollen:
- `roles/owner` ODER folgende kombinierte Rollen:
  - `roles/logging.admin` (Cloud Logging Setup)
  - `roles/errorreporting.admin` (Error Reporting Setup)
  - `roles/iam.serviceAccountAdmin` (Service Account Management)
  - `roles/storage.admin` (Cloud Storage Buckets)
  - `roles/pubsub.admin` (Pub/Sub Topics)
  - `roles/datastore.owner` (Firestore)
  - `roles/secretmanager.admin` (Secret Manager)
  - `roles/serviceusage.serviceUsageAdmin` (API Aktivierung)

### GCP CLI Authentifizierung prüfen
```bash
# Aktuellen Account prüfen
gcloud auth list

# Bei Bedarf neu authentifizieren
gcloud auth login

# Projekt setzen
gcloud config set project true-campus-475614-p4

# Aktuelles Projekt bestätigen
gcloud config get-value project
```

---

## 📋 Setup-Reihenfolge (Empfohlen)

### Phase 1: Grundlegende GCP-Infrastruktur

#### Schritt 1: GCP Infrastructure Setup
**Was wird erstellt:**
- Cloud Storage Bucket für Buchbilder
- Pub/Sub Topics für Agent-Kommunikation
- Firestore-Datenbank (Native Mode)

**Ausführung:**
```bash
# Unter Windows mit Git Bash oder WSL:
bash setup_gcp.sh

# ODER manuell unter PowerShell die Befehle einzeln ausführen (siehe Abschnitt "Alternative")
```

**Erwartete Ausgabe:**
```
GCP-Setup wird gestartet für Projekt: true-campus-475614-p4
Aktiviere erforderliche GCP-APIs...
Operation "operations/..." finished successfully.
APIs erfolgreich aktiviert.
Erstelle Cloud Storage Bucket: gs://true-campus-475614-p4-book-images
Creating gs://true-campus-475614-p4-book-images/...
Bucket erfolgreich erstellt.
Erstelle Pub/Sub-Themen...
Created topic [projects/true-campus-475614-p4/topics/trigger-ingestion].
...
Pub/Sub-Themen erfolgreich erstellt.
Erstelle Firestore-Datenbank im Native-Modus...
Create request issued for: [(default)]
Firestore-Datenbank erfolgreich erstellt.
===============================================
GCP-Ressourcen-Setup erfolgreich abgeschlossen!
===============================================
```

**Bei Fehlern:**
- **"Permission denied"**: Prüfe IAM-Berechtigungen (siehe Voraussetzungen)
- **"Bucket already exists"**: Bucket existiert bereits, kein Problem
- **"Topic already exists"**: Topics existieren bereits, kein Problem
- **"Firestore already exists"**: Datenbank existiert bereits, kein Problem
- **"Bash not found" (Windows)**: Verwende Git Bash, WSL oder manuelle PowerShell-Befehle

**Verifikation:**
```bash
# Storage Bucket prüfen
gsutil ls gs://true-campus-475614-p4-book-images

# Pub/Sub Topics prüfen
gcloud pubsub topics list

# Firestore prüfen
gcloud firestore databases describe --database="(default)"
```

---

### Phase 2: Monitoring & Logging Setup

#### Schritt 2: Cloud Logging Setup
**Was wird konfiguriert:**
- Cloud Logging API
- Log Sinks (Error Logs, Agent Logs, Backend Logs)
- Strukturiertes JSON-Format Logging
- 30-Tage Retention Policy
- Logging-Konfigurationsdateien für Agents

**Ausführung:**
```bash
python setup_cloud_logging.py --project-id=true-campus-475614-p4 --retention-days=30
```

**Optionale Parameter:**
```bash
# Logging-Test überspringen
python setup_cloud_logging.py --project-id=true-campus-475614-p4 --skip-test

# Andere Retention Period
python setup_cloud_logging.py --project-id=true-campus-475614-p4 --retention-days=90
```

**Erwartete Ausgabe:**
```
============================================================
Cloud Logging Setup for Alpha Launch
============================================================
2025-11-02 03:00:00 - INFO - Enabling Cloud Logging API...
2025-11-02 03:00:05 - INFO - ✓ Cloud Logging API enabled
2025-11-02 03:00:05 - INFO - Creating log sinks...
2025-11-02 03:00:10 - INFO - ✓ Created sink: error-logs-sink
2025-11-02 03:00:12 - INFO - ✓ Created sink: agent-logs-sink
2025-11-02 03:00:14 - INFO - ✓ Created sink: backend-logs-sink
...
╔════════════════════════════════════════════════════════════════╗
║         Cloud Logging Setup Complete - Alpha Ready            ║
╚════════════════════════════════════════════════════════════════╝
```

**Erstellte Dateien:**
- `logging_config.json` - Strukturiertes Logging Config
- `logging_env_config.json` - Umgebungs-spezifische Configs
- `logging_example.py` - Beispiel-Code für Integration
- `logging_snippets/` - Agent-spezifische Code-Snippets

**Bei Fehlern:**
- **"Permission denied"**: Benötigt `roles/logging.admin`
- **"Sink already exists"**: Sink existiert bereits, wird übersprungen
- **"Failed to set retention policy"**: Manuelle Konfiguration in Console erforderlich

**Verifikation:**
```bash
# Log Sinks prüfen
gcloud logging sinks list

# Logs in Console öffnen
# https://console.cloud.google.com/logs/query?project=true-campus-475614-p4
```

---

#### Schritt 3: Error Reporting Setup
**Was wird konfiguriert:**
- Error Reporting API
- Error Grouping Rules
- Alert Policies (optional mit Email)
- Error Handling Decorator für Agents
- Agent-spezifische Error Configs

**Ausführung:**
```bash
# MIT Email-Alerts (empfohlen für Production):
python setup_error_reporting.py --project-id=true-campus-475614-p4 --alert-email=deine@email.com

# OHNE Email-Alerts (nur für Testing):
python setup_error_reporting.py --project-id=true-campus-475614-p4
```

**Optionale Parameter:**
```bash
# Error-Test überspringen
python setup_error_reporting.py --project-id=true-campus-475614-p4 --skip-test
```

**Erwartete Ausgabe:**
```
============================================================
Error Reporting Setup for Alpha Launch
============================================================
2025-11-02 03:05:00 - INFO - Enabling Error Reporting API...
2025-11-02 03:05:05 - INFO - ✓ Error Reporting API enabled
2025-11-02 03:05:05 - INFO - Creating alert policies...
2025-11-02 03:05:10 - INFO - Creating email notification channel for: deine@email.com
2025-11-02 03:05:15 - INFO - ✓ Email notification channel created
...
╔════════════════════════════════════════════════════════════════╗
║      Error Reporting Setup Complete - Alpha Ready             ║
╚════════════════════════════════════════════════════════════════╝
```

**Erstellte Dateien:**
- `error_grouping_config.json` - Error Grouping Rules
- `error_reporting_integration.py` - Integration Code
- `error_handling_decorator.py` - Error Decorator für Agents
- `error_configs/` - Agent-spezifische Error Configs
- `error_dashboard_queries.json` - Vordefinierte Dashboard Queries

**Bei Fehlern:**
- **"Permission denied"**: Benötigt `roles/errorreporting.admin`
- **"Failed to create notification channel"**: Manuelle Erstellung in Console
- **Email nicht erhalten**: Prüfe Spam-Ordner und Email-Adresse

**Verifikation:**
```bash
# Error Reporting Console öffnen
# https://console.cloud.google.com/errors?project=true-campus-475614-p4
```

---

### Phase 3: Secrets Management

#### Schritt 4: Secrets Setup
**Was wird erstellt:**
- Secret Manager Secrets mit Platzhalter-Werten
- `ebay-auth-token`
- `amazon-auth-token`

⚠️ **WICHTIG**: Dieses Script erstellt nur Platzhalter! Du musst die Secrets manuell mit echten Werten aktualisieren.

**Ausführung:**
```bash
# Unter Windows mit Git Bash oder WSL:
bash setup_secrets.sh

# ODER manuell unter PowerShell (siehe "Alternative Manuelle Ausführung")
```

**Erwartete Ausgabe:**
```
Erstelle eBay-Auth-Token-Secret...
Created secret [ebay-auth-token].
Created version [1] of secret [ebay-auth-token].
eBay-Auth-Token-Secret mit einem Platzhalterwert erstellt.
Bitte aktualisieren Sie es mit Ihrem tatsächlichen Token.

Erstelle Amazon-Auth-Token-Secret...
Created secret [amazon-auth-token].
Created version [1] of secret [amazon-auth-token].
Amazon-Auth-Token-Secret mit einem Platzhalterwert erstellt.
Bitte aktualisieren Sie es mit Ihrem tatsächlichen Token.

Secret-Setup abgeschlossen.
```

**Bei Fehlern:**
- **"Permission denied"**: Benötigt `roles/secretmanager.admin`
- **"Secret already exists"**: Secret existiert bereits, verwende Update-Befehl
- **"Bash not found"**: Verwende Git Bash, WSL oder manuelle Befehle

**Secrets aktualisieren (MANUELL ERFORDERLICH):**
```bash
# eBay Token aktualisieren
echo -n "DEIN_ECHTER_EBAY_TOKEN" | gcloud secrets versions add ebay-auth-token --data-file=-

# Amazon Token aktualisieren
echo -n "DEIN_ECHTER_AMAZON_TOKEN" | gcloud secrets versions add amazon-auth-token --data-file=-
```

**Verifikation:**
```bash
# Secrets auflisten
gcloud secrets list

# Secret-Wert prüfen (ACHTUNG: zeigt den Wert im Terminal!)
gcloud secrets versions access latest --secret="ebay-auth-token"
```

---

## 🔍 Komplette Verifikation

Nach Abschluss aller Schritte:

```bash
# 1. GCP APIs prüfen
gcloud services list --enabled | grep -E "(run|pubsub|firestore|logging|error)"

# 2. Storage Bucket prüfen
gsutil ls -L gs://true-campus-475614-p4-book-images

# 3. Pub/Sub Topics prüfen
gcloud pubsub topics list

# 4. Firestore prüfen
gcloud firestore databases describe --database="(default)"

# 5. Log Sinks prüfen
gcloud logging sinks list

# 6. Secrets prüfen
gcloud secrets list

# 7. Config-Dateien prüfen
ls -la logging_*.json error_*.json *.py
```

**Erwartete Dateien im Root-Verzeichnis:**
- ✓ `logging_config.json`
- ✓ `logging_env_config.json`
- ✓ `logging_example.py`
- ✓ `error_grouping_config.json`
- ✓ `error_reporting_integration.py`
- ✓ `error_handling_decorator.py`
- ✓ `error_dashboard_queries.json`
- ✓ `logging_snippets/` (Verzeichnis)
- ✓ `error_configs/` (Verzeichnis)

---

## 🚨 Troubleshooting

### Häufige Fehler und Lösungen

#### 1. Permission Denied Errors
```
ERROR: (gcloud...) User does not have permission to access...
```
**Lösung:**
- Prüfe IAM-Rollen: `gcloud projects get-iam-policy true-campus-475614-p4`
- Benötigte Rollen im Projekt hinzufügen (Owner oder spezifische Rollen)
- Mit richtigem Account authentifizieren: `gcloud auth login`

#### 2. Python Package Import Errors
```
ModuleNotFoundError: No module named 'google.cloud'
```
**Lösung:**
```bash
pip install --upgrade google-cloud-logging google-cloud-error-reporting google-api-core python-json-logger
```

#### 3. Bash Script unter Windows nicht ausführbar
```
'bash' is not recognized as an internal or external command
```
**Lösung:**
- Installiere Git Bash: https://git-scm.com/downloads
- ODER verwende WSL: https://docs.microsoft.com/en-us/windows/wsl/install
- ODER führe Befehle manuell in PowerShell aus (siehe Alternative)

#### 4. Firestore Already Exists Error
```
ERROR: (gcloud.firestore.databases.create) ALREADY_EXISTS
```
**Lösung:**
- Das ist OK! Die Datenbank existiert bereits
- Überspringe diesen Schritt oder kommentiere ihn im Script aus

#### 5. Quota/Limit Exceeded
```
ERROR: Quota exceeded for quota metric 'API requests'
```
**Lösung:**
- Warte einige Minuten und versuche es erneut
- Prüfe Quotas: https://console.cloud.google.com/iam-admin/quotas
- Erhöhe Quotas falls nötig (oder kontaktiere GCP Support)

#### 6. Secret Manager Permissions
```
ERROR: Permission 'secretmanager.secrets.create' denied
```
**Lösung:**
```bash
# Service Account IAM-Rolle hinzufügen
gcloud projects add-iam-policy-binding true-campus-475614-p4 \
    --member="user:DEINE_EMAIL@gmail.com" \
    --role="roles/secretmanager.admin"
```

---

## 🔄 Alternative: Manuelle Schritt-für-Schritt Ausführung

Falls die Scripts nicht funktionieren, hier die **manuellen Befehle** für PowerShell:

### Manuelle GCP Infrastructure Setup (statt setup_gcp.sh)

```powershell
# Variables setzen
$GCP_PROJECT_ID = "true-campus-475614-p4"
$GCP_REGION = "europe-west1"

# 1. APIs aktivieren
gcloud services enable run.googleapis.com --project=$GCP_PROJECT_ID
gcloud services enable pubsub.googleapis.com --project=$GCP_PROJECT_ID
gcloud services enable storage.googleapis.com --project=$GCP_PROJECT_ID
gcloud services enable firestore.googleapis.com --project=$GCP_PROJECT_ID
gcloud services enable vision.googleapis.com --project=$GCP_PROJECT_ID
gcloud services enable aiplatform.googleapis.com --project=$GCP_PROJECT_ID
gcloud services enable secretmanager.googleapis.com --project=$GCP_PROJECT_ID
gcloud services enable cloudbuild.googleapis.com --project=$GCP_PROJECT_ID

# 2. Storage Bucket erstellen
$BUCKET_NAME = "$GCP_PROJECT_ID-book-images"
gsutil mb -p $GCP_PROJECT_ID -l $GCP_REGION gs://$BUCKET_NAME

# 3. Pub/Sub Topics erstellen
gcloud pubsub topics create trigger-ingestion --project=$GCP_PROJECT_ID
gcloud pubsub topics create book-identified --project=$GCP_PROJECT_ID
gcloud pubsub topics create delist-book-everywhere --project=$GCP_PROJECT_ID
gcloud pubsub topics create sale-notification-received --project=$GCP_PROJECT_ID

# 4. Firestore erstellen (falls noch nicht vorhanden)
gcloud firestore databases create --location=$GCP_REGION --type=firestore-native --project=$GCP_PROJECT_ID
```

### Manuelle Secrets Setup (statt setup_secrets.sh)

```powershell
# eBay Token Secret
gcloud secrets create ebay-auth-token --replication-policy="automatic" --project=true-campus-475614-p4
"EBAY_AUTH_TOKEN_PLACEHOLDER" | gcloud secrets versions add ebay-auth-token --data-file=- --project=true-campus-475614-p4

# Amazon Token Secret
gcloud secrets create amazon-auth-token --replication-policy="automatic" --project=true-campus-475614-p4
"AMAZON_AUTH_TOKEN_PLACEHOLDER" | gcloud secrets versions add amazon-auth-token --data-file=- --project=true-campus-475614-p4

# Echte Tokens setzen (ERFORDERLICH!)
# Ersetze die Platzhalter mit echten Werten:
# "DEIN_ECHTER_TOKEN" | gcloud secrets versions add ebay-auth-token --data-file=-
```

---

## 📊 Setup-Prioritäten für Alpha Launch

### KRITISCH (Muss funktionieren):
1. ✅ **GCP Infrastructure** (Schritt 1) - Storage, Pub/Sub, Firestore
2. ✅ **Cloud Logging** (Schritt 2) - Monitoring ist essentiell
3. ⚠️ **Secrets Setup** (Schritt 4) - NUR wenn eBay/Amazon Features genutzt werden

### WICHTIG (Sollte funktionieren):
4. ✅ **Error Reporting** (Schritt 3) - Hilft bei Debugging

### OPTIONAL (Kann später konfiguriert werden):
5. ⏭️ Email Alerts für Error Reporting
6. ⏭️ Custom Log Retention > 30 Tage
7. ⏭️ Erweiterte Monitoring Dashboards

---

## 🎯 Quick-Start für Alpha Launch

**Minimal-Setup (5 Minuten):**

```bash
# 1. Authentifizierung
gcloud auth login
gcloud config set project true-campus-475614-p4

# 2. Kritische APIs aktivieren
gcloud services enable run.googleapis.com firestore.googleapis.com storage.googleapis.com pubsub.googleapis.com vision.googleapis.com

# 3. Storage & Pub/Sub
gsutil mb -l europe-west1 gs://true-campus-475614-p4-book-images
gcloud pubsub topics create trigger-ingestion
gcloud pubsub topics create book-identified

# 4. Logging aktivieren
python setup_cloud_logging.py --project-id=true-campus-475614-p4 --skip-test

# FERTIG für Alpha Testing!
```

**Später hinzufügen:**
- Error Reporting (wenn Probleme auftreten)
- Secrets (wenn eBay/Amazon Integration benötigt wird)
- Email Alerts (wenn kritische Fehler überwacht werden sollen)

---

## 📝 Nächste Schritte nach Setup

### 1. Agent Integration
Die erstellten Config-Dateien in Agents integrieren:

```python
# In jedem Agent main.py hinzufügen:
import logging.config
import json
from google.cloud import logging as cloud_logging

# Cloud Logging Setup
logging_client = cloud_logging.Client()
logging_client.setup_logging()

# Strukturiertes Logging verwenden
logger = logging.getLogger(__name__)
logger.info("Agent started", extra={
    "agent": "ingestion-agent",
    "user_id": user_id,
    "book_id": book_id
})
```

### 2. Error Handling hinzufügen
```python
# Error Handling Decorator verwenden
from error_handling_decorator import handle_errors

@handle_errors(agent_name='ingestion-agent')
async def process_book(book_id: str, user_id: str):
    # Agent logic hier
    pass
```

### 3. Requirements.txt aktualisieren
```txt
# In jedem Agent requirements.txt hinzufügen:
google-cloud-logging>=3.8.0
google-cloud-error-reporting>=1.9.0
python-json-logger>=2.0.7
```

### 4. Deployment
```bash
# Agents nach Cloud Run deployen
gcloud run deploy ingestion-agent --source=./agents/ingestion-agent --region=europe-west1

# Logs überwachen
gcloud logging read "resource.type=cloud_run_revision" --limit=50
```

---

## 📚 Nützliche Links

- **Cloud Console**: https://console.cloud.google.com/
- **Logs Viewer**: https://console.cloud.google.com/logs/query?project=true-campus-475614-p4
- **Error Reporting**: https://console.cloud.google.com/errors?project=true-campus-475614-p4
- **Secret Manager**: https://console.cloud.google.com/security/secret-manager?project=true-campus-475614-p4
- **Cloud Storage**: https://console.cloud.google.com/storage/browser?project=true-campus-475614-p4
- **Pub/Sub**: https://console.cloud.google.com/cloudpubsub/topic/list?project=true-campus-475614-p4
- **Firestore**: https://console.cloud.google.com/firestore?project=true-campus-475614-p4

---

## ✅ Setup Checklist

Nach Abschluss solltest du folgendes haben:

- [ ] GCP Project `true-campus-475614-p4` ist aktiv
- [ ] Alle erforderlichen APIs sind aktiviert
- [ ] Cloud Storage Bucket `true-campus-475614-p4-book-images` existiert
- [ ] Pub/Sub Topics (trigger-ingestion, book-identified, etc.) existieren
- [ ] Firestore Datenbank (Native Mode) ist erstellt
- [ ] Cloud Logging ist konfiguriert mit Log Sinks
- [ ] Error Reporting ist aktiviert
- [ ] Secrets sind erstellt (mit echten Werten aktualisiert)
- [ ] Config-Dateien sind generiert (logging_*.json, error_*.json)
- [ ] Agent-Snippets sind verfügbar (logging_snippets/, error_configs/)

**Status:** ✅ ALPHA LAUNCH READY!