# Production Deployment Guide

**Projekt:** Intelligent Book Sales Pipeline
**Status:** Production Ready
**GCP Project ID:** `project-52b2fab8-15a1-4b66-9f3`
**Region:** `europe-west1`
**Aktualisiert:** 2026-02-04

---

## 📋 Inhaltsverzeichnis

1. [Prerequisites](#prerequisites)
2. [Initial Setup (Automated)](#initial-setup-automated)
3. [Infrastructure Deployment](#infrastructure-deployment)
4. [Agent Deployment](#agent-deployment)
5. [Configuration & Secrets](#configuration--secrets)
6. [Monitoring Setup](#monitoring-setup)
7. [Validation & Health Checks](#validation--health-checks)
8. [Rollback Procedures](#rollback-procedures)
9. [Emergency Commands](#emergency-commands)

---

## Prerequisites

### System Requirements
```bash
# Verify installations
gcloud --version  # Google Cloud SDK 400+
docker --version  # Docker 20+
python --version  # Python 3.11+
node --version    # Node.js 18+
```

### Authentication & Project Setup
```bash
# Authenticate with GCP
gcloud auth login

# Set project
export PROJECT_ID="project-52b2fab8-15a1-4b66-9f3"
export REGION="europe-west1"
export ZONE="europe-west1-b"

gcloud config set project $PROJECT_ID
gcloud config set compute/region $REGION
gcloud config set compute/zone $ZONE

# Verify current project
gcloud config get-value project
```

---

## Initial Setup (Automated)

Wir empfehlen die Nutzung der bereitgestellten Setup-Skripte für die Basiskonfiguration.

### GCP Ressourcen Setup
Führt die grundlegende Einrichtung von APIs, Storage Buckets, Pub/Sub Topics und Firestore durch.

```bash
# Ausführen des Setup-Skripts
bash scripts/setup/setup_gcp.sh
```

### Manuelle Verifikation der Ressourcen
Falls das Skript nicht genutzt wird, müssen folgende Ressourcen manuell erstellt werden (siehe [Infrastructure Deployment](#infrastructure-deployment)).

---

## Infrastructure Deployment

### Step 1: Create Cloud Storage Bucket
```bash
# Book images bucket
export BUCKET_NAME="${PROJECT_ID}-book-images"

gsutil mb -p $PROJECT_ID -c STANDARD -l $REGION gs://${BUCKET_NAME}

# Enable versioning (for recovery)
gsutil versioning set on gs://${BUCKET_NAME}

# Set lifecycle policy (delete old objects after 90 days)
cat > lifecycle.json << EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 90}
      }
    ]
  }
}
EOF

gsutil lifecycle set lifecycle.json gs://${BUCKET_NAME}

# Configure CORS for frontend uploads
cat > cors.json << EOF
[
  {
    "origin": ["http://localhost:5173", "https://your-frontend-domain.com"],
    "method": ["GET", "POST", "PUT"],
    "responseHeader": ["Content-Type"],
    "maxAgeSeconds": 3600
  }
]
EOF

gsutil cors set cors.json gs://${BUCKET_NAME}
```

### Step 2: Create Pub/Sub Topics
Stelle sicher, dass die aktuellen Topic-Namen verwendet werden.

```bash
# Core Topics
gcloud pubsub topics create trigger-ingestion
gcloud pubsub topics create trigger-condition-assessment
gcloud pubsub topics create condition-assessment-completed
gcloud pubsub topics create book-listing-requests
gcloud pubsub topics create delist-book-everywhere
gcloud pubsub topics create sale-notification-received

# Dead Letter Topics (DLQ)
gcloud pubsub topics create trigger-ingestion-dlq
gcloud pubsub topics create condition-assessment-completed-dlq
gcloud pubsub topics create book-listing-requests-dlq
```

### Step 3: Create Pub/Sub Subscriptions with DLQ
```bash
# Subscription for trigger-ingestion (Ingestion Agent)
gcloud pubsub subscriptions create trigger-ingestion-sub \
  --topic=trigger-ingestion \
  --ack-deadline=60 \
  --message-retention-duration=7d \
  --dead-letter-topic=trigger-ingestion-dlq \
  --max-delivery-attempts=5

# Subscription for condition-assessment-completed (Strategist Agent)
gcloud pubsub subscriptions create condition-assessment-completed-sub \
  --topic=condition-assessment-completed \
  --ack-deadline=120 \
  --message-retention-duration=7d \
  --dead-letter-topic=condition-assessment-completed-dlq \
  --max-delivery-attempts=5

# Subscription for book-listing-requests (Ambassador Agent)
gcloud pubsub subscriptions create book-listing-requests-sub \
  --topic=book-listing-requests \
  --ack-deadline=120 \
  --message-retention-duration=7d \
  --dead-letter-topic=book-listing-requests-dlq \
  --max-delivery-attempts=3
```

### Step 4: Setup Firestore
```bash
# Create Firestore database (if not exists)
gcloud firestore databases create \
  --location=$REGION \
  --type=firestore-native

# Deploy security rules
firebase deploy --only firestore:rules
```

### Step 5: Create Firestore Indexes
```bash
# Deploy indexes via Firebase CLI
firebase deploy --only firestore:indexes
```

---

## Agent Deployment

### Preparation: Build Shared Package
```bash
# Build shared package (from project root)
cd shared
python setup.py bdist_wheel
cd ..
```

### Deploy Ingestion Agent
```bash
# Build & Push
docker build -t gcr.io/${PROJECT_ID}/ingestion-agent:latest \
  -f agents/ingestion-agent/Dockerfile .
docker push gcr.io/${PROJECT_ID}/ingestion-agent:latest

# Deploy
gcloud run deploy ingestion-agent \
  --image=gcr.io/${PROJECT_ID}/ingestion-agent:latest \
  --region=$REGION \
  --platform=managed \
  --memory=512Mi \
  --service-account=ingestion-agent-invoker@${PROJECT_ID}.iam.gserviceaccount.com \
  --set-env-vars="GCP_PROJECT_ID=${PROJECT_ID},VERTEX_AI_LOCATION=${REGION}"

# Eventarc Trigger
gcloud eventarc triggers create ingestion-agent-trigger \
  --destination-run-service=ingestion-agent \
  --destination-run-region=$REGION \
  --location=$REGION \
  --transport-topic=trigger-ingestion \
  --event-filters=type=google.cloud.pubsub.topic.v1.messagePublished \
  --service-account=ingestion-agent-invoker@${PROJECT_ID}.iam.gserviceaccount.com
```

### Deploy Condition Assessor Agent
```bash
# Build & Push
docker build -t gcr.io/${PROJECT_ID}/condition-assessor:latest \
  -f agents/condition-assessor/Dockerfile .
docker push gcr.io/${PROJECT_ID}/condition-assessor:latest

# Deploy
gcloud run deploy condition-assessor \
  --image=gcr.io/${PROJECT_ID}/condition-assessor:latest \
  --region=$REGION \
  --platform=managed \
  --memory=512Mi \
  --service-account=ingestion-agent-invoker@${PROJECT_ID}.iam.gserviceaccount.com \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=${PROJECT_ID}"

# Trigger: Wird via Pub/Sub 'trigger-condition-assessment' oder direkt aufgerufen
```

### Deploy Strategist Agent
```bash
# Build & Push
docker build -t gcr.io/${PROJECT_ID}/strategist-agent:latest \
  -f agents/strategist-agent/Dockerfile .
docker push gcr.io/${PROJECT_ID}/strategist-agent:latest

# Deploy
gcloud run deploy strategist-agent \
  --image=gcr.io/${PROJECT_ID}/strategist-agent:latest \
  --region=$REGION \
  --platform=managed \
  --memory=512Mi \
  --service-account=strategist-agent-invoker@${PROJECT_ID}.iam.gserviceaccount.com \
  --set-env-vars="GCP_PROJECT=${PROJECT_ID}"

# Eventarc Trigger
gcloud eventarc triggers create strategist-agent-trigger \
  --destination-run-service=strategist-agent \
  --destination-run-region=$REGION \
  --location=$REGION \
  --transport-topic=condition-assessment-completed \
  --event-filters=type=google.cloud.pubsub.topic.v1.messagePublished \
  --service-account=strategist-agent-invoker@${PROJECT_ID}.iam.gserviceaccount.com
```

### Deploy Ambassador Agent
```bash
# Build & Push
docker build -t gcr.io/${PROJECT_ID}/ambassador-agent:latest \
  -f agents/ambassador-agent/Dockerfile .
docker push gcr.io/${PROJECT_ID}/ambassador-agent:latest

# Deploy
gcloud run deploy ambassador-agent \
  --image=gcr.io/${PROJECT_ID}/ambassador-agent:latest \
  --region=$REGION \
  --platform=managed \
  --memory=1Gi \
  --service-account=ambassador-agent-invoker@${PROJECT_ID}.iam.gserviceaccount.com \
  --set-env-vars="GCP_PROJECT=${PROJECT_ID}"

# Eventarc Triggers
gcloud eventarc triggers create ambassador-listing-trigger \
  --destination-run-service=ambassador-agent \
  --destination-run-region=$REGION \
  --location=$REGION \
  --transport-topic=book-listing-requests \
  --event-filters=type=google.cloud.pubsub.topic.v1.messagePublished \
  --service-account=ambassador-agent-invoker@${PROJECT_ID}.iam.gserviceaccount.com

gcloud eventarc triggers create ambassador-delist-trigger \
  --destination-run-service=ambassador-agent \
  --destination-run-region=$REGION \
  --location=$REGION \
  --transport-topic=delist-book-everywhere \
  --event-filters=type=google.cloud.pubsub.topic.v1.messagePublished \
  --service-account=ambassador-agent-invoker@${PROJECT_ID}.iam.gserviceaccount.com
```

### Deploy Sentinel Agent & Webhook
```bash
# Sentinel Webhook (Public Endpoint)
docker build -t gcr.io/${PROJECT_ID}/sentinel-webhook:latest -f agents/sentinel-webhook/Dockerfile .
docker push gcr.io/${PROJECT_ID}/sentinel-webhook:latest

gcloud run deploy sentinel-webhook \
  --image=gcr.io/${PROJECT_ID}/sentinel-webhook:latest \
  --region=$REGION \
  --allow-unauthenticated

# Sentinel Agent (Worker)
docker build -t gcr.io/${PROJECT_ID}/sentinel-agent:latest -f agents/sentinel-agent/Dockerfile .
docker push gcr.io/${PROJECT_ID}/sentinel-agent:latest

gcloud run deploy sentinel-agent \
  --image=gcr.io/${PROJECT_ID}/sentinel-agent:latest \
  --region=$REGION \
  --no-allow-unauthenticated \
  --service-account=sentinel-agent-invoker@${PROJECT_ID}.iam.gserviceaccount.com

# Trigger
gcloud eventarc triggers create sentinel-agent-trigger \
  --destination-run-service=sentinel-agent \
  --destination-run-region=$REGION \
  --location=$REGION \
  --transport-topic=sale-notification-received \
  --event-filters=type=google.cloud.pubsub.topic.v1.messagePublished \
  --service-account=sentinel-agent-invoker@${PROJECT_ID}.iam.gserviceaccount.com
```

### Deploy Dashboard Backend
```bash
docker build -t gcr.io/${PROJECT_ID}/dashboard-backend:latest -f dashboard/backend/Dockerfile .
docker push gcr.io/${PROJECT_ID}/dashboard-backend:latest

gcloud run deploy dashboard-backend \
  --image=gcr.io/${PROJECT_ID}/dashboard-backend:latest \
  --region=$REGION \
  --allow-unauthenticated \
  --service-account=backend-sa@${PROJECT_ID}.iam.gserviceaccount.com
```

---

## Configuration & Secrets

Wir nutzen den Google Secret Manager für sensible Daten.

### Secrets Setup (Automatisch)
```bash
bash scripts/setup/setup_secrets.sh
```

### Secrets Manuell Aktualisieren
Die automatisch erstellten Secrets enthalten Platzhalter. Diese müssen mit echten Werten überschrieben werden:

```bash
# eBay OAuth Credentials
echo -n "YOUR_REAL_EBAY_CLIENT_ID" | gcloud secrets versions add ebay-oauth-client-id --data-file=-
echo -n "YOUR_REAL_EBAY_CLIENT_SECRET" | gcloud secrets versions add ebay-oauth-client-secret --data-file=-

# Google Books API Key
echo -n "YOUR_REAL_API_KEY" | gcloud secrets versions add google-books-api-key --data-file=-
```

### Service-Update mit Secrets
Nach dem Erstellen/Update der Secrets müssen die Services aktualisiert werden:

```bash
gcloud run services update ambassador-agent \
  --region=$REGION \
  --update-secrets=EBAY_CLIENT_ID=ebay-oauth-client-id:latest,EBAY_CLIENT_SECRET=ebay-oauth-client-secret:latest

gcloud run services update ingestion-agent \
  --region=$REGION \
  --update-secrets=GOOGLE_BOOKS_API_KEY=google-books-api-key:latest
```

---

## Monitoring Setup

### Logging & Error Reporting
Die Logging-Konfiguration erfolgt automatisch bei der Initialisierung. Stellen Sie sicher, dass alle Agents die `logging_config.json` verwenden.

### Monitoring Policy
Erstellen Sie Alerts für kritische Zustände:
1. **High Error Rate:** > 5% Fehlerquote
2. **Service Down:** Uptime Check < 90%

```bash
# Beispiel: Uptime Check erstellen
gcloud monitoring uptime create dashboard-backend-check \
  --resource-type=uptime-url \
  --host=$(gcloud run services describe dashboard-backend --region=$REGION --format='value(status.url)' | sed 's|https://||') \
  --path=/health \
  --period=60s
```

---

## Validation & Health Checks

### Verify Infrastructure
```bash
# Check Topics
gcloud pubsub topics list

# Check Services
gcloud run services list --region=$REGION
```

### Smoke Test
```bash
# Publish Test Message
gcloud pubsub topics publish trigger-ingestion --message='{"test": "smoke_test", "book_id": "test_123"}'
```

---

## Rollback Procedures

### Service Rollback
```bash
# Rollback to previous revision
PREVIOUS_REVISION=$(gcloud run revisions list --service=ingestion-agent --region=$REGION --format='value(name)' | sed -n 2p)

gcloud run services update-traffic ingestion-agent \
  --region=$REGION \
  --to-revisions=${PREVIOUS_REVISION}=100
```

---

## Emergency Commands

### Drain Subscription
Wenn eine Queue blockiert ist oder fehlerhafte Nachrichten enthält:
```bash
while true; do
  MESSAGES=$(gcloud pubsub subscriptions pull trigger-ingestion-sub --auto-ack --limit=100 --format=json)
  if [ -z "$MESSAGES" ] || [ "$MESSAGES" == "[]" ]; then break; fi
  echo "Drained batch..."
done
```

### Stop Service Traffic
```bash
gcloud run services update-traffic dashboard-backend --region=$REGION --to-revisions=LATEST=0
```

