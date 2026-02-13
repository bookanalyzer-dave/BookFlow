# ⚡ Alpha Launch Quick-Start Guide

## 🎯 Ziel
Minimaler Setup für funktionsfähigen Alpha Launch in **unter 10 Minuten**.

---

## 🚀 Express-Setup (5-10 Minuten)

### Schritt 1: Authentifizierung (1 Minute)
```bash
gcloud auth login
gcloud config set project true-campus-475614-p4
```

### Schritt 2: Kritische APIs aktivieren (2 Minuten)
```bash
gcloud services enable \
    run.googleapis.com \
    firestore.googleapis.com \
    storage.googleapis.com \
    pubsub.googleapis.com \
    vision.googleapis.com \
    logging.googleapis.com
```

### Schritt 3: Basis-Infrastruktur (2 Minuten)
```bash
# Storage Bucket
gsutil mb -l europe-west1 gs://true-campus-475614-p4-book-images

# Pub/Sub Topics (nur die wichtigsten)
gcloud pubsub topics create book-analyzed
gcloud pubsub topics create book-identified

# Firestore (falls noch nicht vorhanden - kann Fehler werfen, ist OK)
gcloud firestore databases create --location=europe-west1 --type=firestore-native || echo "Firestore bereits vorhanden"
```

### Schritt 4: Logging Setup (2-3 Minuten)
```bash
python setup_cloud_logging.py --project-id=true-campus-475614-p4 --skip-test
```

### ✅ Fertig für Alpha Launch!

---

## 📋 Was jetzt funktioniert

✅ **Agents können deployt werden**
- Ingestion Agent
- Condition Assessor
- Strategist Agent

✅ **Core Features sind verfügbar**
- Image Upload zu Cloud Storage
- Vision API für Bucherkennung
- Firestore für Datenspeicherung
- Pub/Sub für Agent-Kommunikation
- Cloud Logging für Monitoring

❌ **Was NOCH NICHT funktioniert**
- eBay/Amazon Integration (benötigt Secrets)
- Email Alerts bei Fehlern
- Erweiterte Error Grouping

---

## 🔧 Was du SPÄTER hinzufügen solltest

### 1. Error Reporting (wenn erste Fehler auftreten)
```bash
python setup_error_reporting.py --project-id=true-campus-475614-p4 --alert-email=deine@email.com
```

### 2. Marketplace Secrets (wenn eBay/Amazon Integration benötigt wird)
```bash
# Platzhalter erstellen
bash setup_secrets.sh

# Echte Werte setzen
echo -n "DEIN_ECHTER_EBAY_TOKEN" | gcloud secrets versions add ebay-auth-token --data-file=-
echo -n "DEIN_ECHTER_AMAZON_TOKEN" | gcloud secrets versions add amazon-auth-token --data-file=-
```

### 3. Restliche Pub/Sub Topics
```bash
gcloud pubsub topics create delist-book-everywhere
gcloud pubsub topics create sale-notification-received
```

---

## 🧪 Test ob alles funktioniert

```bash
# 1. Storage testen
gsutil ls gs://true-campus-475614-p4-book-images

# 2. Pub/Sub testen
gcloud pubsub topics list

# 3. Firestore testen
gcloud firestore databases describe --database="(default)"

# 4. Logging testen
gcloud logging read "severity >= INFO" --limit=10
```

---

## 🚨 Wenn etwas nicht funktioniert

### Problem: "Permission denied"
```bash
# Lösung: Prüfe deine Rolle im Projekt
gcloud projects get-iam-policy true-campus-475614-p4 | grep "$(gcloud config get-value account)"

# Du brauchst mindestens "Owner" oder eine Kombination aus:
# - roles/editor
# - roles/logging.admin
# - roles/storage.admin
```

### Problem: "Bucket already exists"
```bash
# Das ist OK! Überspringen und weitermachen.
```

### Problem: "Firestore already exists"
```bash
# Das ist OK! Überspringen und weitermachen.
```

### Problem: Python Packages fehlen
```bash
pip install google-cloud-logging google-cloud-error-reporting google-api-core python-json-logger
```

---

## 📦 Nächster Schritt: Agents deployen

```bash
# Beispiel: Ingestion Agent deployen
cd agents/ingestion-agent
gcloud run deploy ingestion-agent \
    --source=. \
    --region=europe-west1 \
    --allow-unauthenticated \
    --set-env-vars="GCP_PROJECT_ID=true-campus-475614-p4"
```

---

## 📊 Monitoring nach Deployment

```bash
# Logs anschauen
gcloud logging read "resource.type=cloud_run_revision" --limit=50 --format=json

# Oder in Cloud Console:
# https://console.cloud.google.com/logs/query?project=true-campus-475614-p4
```

---

## 🎓 Für mehr Details

Siehe [`ALPHA_LAUNCH_SETUP_GUIDE.md`](ALPHA_LAUNCH_SETUP_GUIDE.md) für:
- Vollständige Setup-Anleitung
- Troubleshooting-Tipps
- Manuelle Alternative-Befehle (Windows PowerShell)
- Agent Integration Code-Beispiele
- Error Handling Best Practices

---

## ⏱️ Zeit-Investment

| Task | Zeit | Priorität |
|------|------|-----------|
| Express Setup (oben) | 5-10 Min | 🔴 KRITISCH |
| Error Reporting | 3-5 Min | 🟡 WICHTIG |
| Secrets Setup | 2-3 Min | 🟢 OPTIONAL* |
| Agent Integration | 10-15 Min | 🟡 WICHTIG |

*nur wenn eBay/Amazon Features sofort benötigt werden

---

## ✅ Alpha Launch Readiness

Nach Express Setup:
- [ ] APIs aktiviert
- [ ] Storage Bucket erstellt
- [ ] Pub/Sub Topics (minimal) erstellt
- [ ] Firestore läuft
- [ ] Logging konfiguriert

**Status: READY für Core Features Testing! 🚀**

Weitere Features (Error Reporting, Secrets) können während des Alphas hinzugefügt werden.