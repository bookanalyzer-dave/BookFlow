# Quick Reference Guide - Intelligent Book Sales Pipeline

**Projekt:** Intelligent Book Sales Pipeline  
**GCP Project:** project-52b2fab8-15a1-4b66-9f3  
**Region:** europe-west1

---

## 🚀 Quick Start (1-Minute)

```bash
# Set Project
export PROJECT_ID="project-52b2fab8-15a1-4b66-9f3"
export REGION="europe-west1"
gcloud config set project $PROJECT_ID

# Quick Health Check
for service in ingestion-agent strategist-agent ambassador-agent dashboard-backend; do
  URL=$(gcloud run services describe $service --region=$REGION --format='value(status.url)' 2>/dev/null)
  [ -n "$URL" ] && curl -sf "${URL}/health" >/dev/null && echo "✅ $service" || echo "❌ $service"
done
```

---

## 📋 Essential Commands

### Health Checks

```bash
# Backend Health
curl https://dashboard-backend-xxx.run.app/api/health

# Rate Limit Status
curl https://dashboard-backend-xxx.run.app/api/rate-limit-status

# All Services Health (1min)
gcloud run services list --region=europe-west1 --format="table(name,status.url)"
```

### View Logs

```bash
# Tail specific service
gcloud run logs tail [SERVICE_NAME] --region=europe-west1

# Recent errors only
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR" --limit=50

# Agent-specific logs
gcloud logging read "resource.labels.service_name=ingestion-agent" --limit=100
```

### Service Management

```bash
# List all services
gcloud run services list --region=europe-west1

# Get service URL
gcloud run services describe [SERVICE_NAME] --region=europe-west1 --format='value(status.url)'

# Update service (e.g., environment variable)
gcloud run services update [SERVICE_NAME] --region=europe-west1 --update-env-vars=KEY=VALUE

# Rollback to previous revision
PREV=$(gcloud run revisions list --service=[SERVICE] --region=europe-west1 --format='value(name)' | sed -n 2p)
gcloud run services update-traffic [SERVICE] --region=europe-west1 --to-revisions=$PREV=100
```

### Firestore Operations

```bash
# Export database (backup)
gcloud firestore export gs://${PROJECT_ID}-firestore-backups/$(date +%Y%m%d)

# Import database (restore)
gcloud firestore import gs://${PROJECT_ID}-firestore-backups/[BACKUP_FOLDER]

# Check database status
gcloud firestore databases describe --database="(default)"
```

### Pub/Sub Management

```bash
# List topics
gcloud pubsub topics list

# Publish test message
gcloud pubsub topics publish trigger-ingestion --message='{"test": "message"}'

# Pull subscription messages
gcloud pubsub subscriptions pull book-analyzed-sub --limit=10

# Drain subscription (clear backlog)
while gcloud pubsub subscriptions pull book-analyzed-sub --auto-ack --limit=100 --format=json | grep -q .; do
  echo "Draining..."
done
```

### Secret Management

```bash
# List secrets
gcloud secrets list

# Get secret value (careful!)
gcloud secrets versions access latest --secret=[SECRET_NAME]

# Add new secret version
echo -n "NEW_VALUE" | gcloud secrets versions add [SECRET_NAME] --data-file=-

# Update service with new secret
gcloud run services update [SERVICE] --region=europe-west1 \
  --update-secrets=[ENV_VAR]=[SECRET_NAME]:latest
```

---

## 🛠️ Development Commands

### Local Development

```bash
# Backend
cd dashboard/backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python main.py

# Frontend
cd dashboard/frontend
npm install
npm run dev

# Agent (local test)
cd agents/ingestion-agent
pip install -r requirements.txt
python main.py
```

### Testing

```bash
# Python tests
pytest shared/user_llm_manager/ --cov

# Integration tests
python tests/manual_scripts/extended_integration_test.py

# E2E tests
python tests/manual_scripts/comprehensive_e2e_test.py

# Frontend E2E
cd dashboard/frontend
npx playwright test
```

### Build & Deploy

```bash
# Build all agents (CI/CD)
gcloud builds submit --config=cloudbuild.yaml

# Deploy single agent
docker build -t gcr.io/${PROJECT_ID}/ingestion-agent:latest \
  -f agents/ingestion-agent/Dockerfile .
docker push gcr.io/${PROJECT_ID}/ingestion-agent:latest
gcloud run deploy ingestion-agent --image=gcr.io/${PROJECT_ID}/ingestion-agent:latest \
  --region=europe-west1 --platform=managed

# Deploy frontend
cd dashboard/frontend
npm run build
firebase deploy --only hosting
```

---

## 🚨 Emergency Commands

### Stop All Traffic

```bash
# Set traffic to 0 for a service
gcloud run services update-traffic [SERVICE] --region=europe-west1 --to-revisions=LATEST=0
```

### Emergency Rollback

```bash
# Rollback service
PREVIOUS=$(gcloud run revisions list --service=[SERVICE] --region=europe-west1 \
  --format='value(name)' | sed -n 2p)
gcloud run services update-traffic [SERVICE] --region=europe-west1 \
  --to-revisions=${PREVIOUS}=100
```

### Force Restart All Services

```bash
for service in $(gcloud run services list --region=europe-west1 --format='value(name)'); do
  echo "Restarting $service..."
  gcloud run services update $service --region=europe-west1 \
    --update-env-vars=RESTART_TIMESTAMP=$(date +%s)
done
```

### Clear Pub/Sub Backlog

```bash
# Drain specific subscription
gcloud pubsub subscriptions seek [SUBSCRIPTION] --time=$(date -u +%Y-%m-%dT%H:%M:%SZ)
```

### Emergency Secret Rotation

```bash
# Generate new key
NEW_KEY=$(python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

# Add new version
echo -n "$NEW_KEY" | gcloud secrets versions add llm-encryption-key --data-file=-

# Update services
gcloud run services update dashboard-backend --region=europe-west1 \
  --update-secrets=LLM_ENCRYPTION_KEY=llm-encryption-key:latest
```

---

## 📊 Monitoring Commands

### Check Error Rate

```bash
# Errors in last hour
gcloud logging read "resource.type=cloud_run_revision AND severity>=ERROR \
  AND timestamp>=\"$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)\"" --limit=100
```

### Cost Analysis

```bash
# Get billing account
gcloud billing accounts list

# View current month costs (via Console)
echo "https://console.cloud.google.com/billing/${PROJECT_ID}"
```

### Performance Metrics

```bash
# Request count
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/request_count"' \
  --format=json | jq '.[] | {service: .resource.labels.service_name, count: .points[0].value.int64Value}'

# CPU usage
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/container/cpu/utilizations"' \
  --format=json
```

---

## 🔐 Security Commands

### Check IAM Permissions

```bash
# Project-level IAM
gcloud projects get-iam-policy $PROJECT_ID

# Service account permissions
gcloud iam service-accounts get-iam-policy [SERVICE_ACCOUNT_EMAIL]

# Secret access
gcloud secrets get-iam-policy [SECRET_NAME]
```

### Audit Logs

```bash
# View admin activity
gcloud logging read "protoPayload.serviceName=cloudresourcemanager.googleapis.com" --limit=50

# Firestore access logs
gcloud logging read "protoPayload.serviceName=firestore.googleapis.com" --limit=50
```

---

## 📁 Critical File Locations

### Configuration
- Firestore Rules: [`firestore.rules`](firestore.rules)
- CI/CD Pipeline: [`cloudbuild.yaml`](cloudbuild.yaml)
- Backend Config: [`dashboard/backend/.env.example`](dashboard/backend/.env.example)

### Documentation
- Architecture: [`ARCHITECTURE.md`](ARCHITECTURE.md)
- Operations: [`OPERATIONS_RUNBOOK.md`](OPERATIONS_RUNBOOK.md)
- Deployment: [`docs/deployment/PRODUCTION_DEPLOYMENT_GUIDE.md`](docs/deployment/PRODUCTION_DEPLOYMENT_GUIDE.md)
- Final Summary: [`docs/archive/PROJECT_FINAL_SUMMARY.md`](docs/archive/PROJECT_FINAL_SUMMARY.md)

### Agents
- Ingestion: [`agents/ingestion-agent/main.py`](agents/ingestion-agent/main.py)
- Condition: [`agents/condition-assessor/main.py`](agents/condition-assessor/main.py)
- Strategist: [`agents/strategist-agent/main.py`](agents/strategist-agent/main.py)
- Ambassador: [`agents/ambassador-agent/main.py`](agents/ambassador-agent/main.py)

### Shared Libraries
- LLM Manager: [`shared/user_llm_manager/`](shared/user_llm_manager/)
- Firestore Client: [`shared/firestore/client.py`](shared/firestore/client.py)
- Health Checks: [`shared/health_check.py`](shared/health_check.py)

---

## 🆘 Troubleshooting Quick Wins

### Service Won't Start
```bash
# Check logs
gcloud run logs tail [SERVICE] --region=europe-west1

# Check environment variables
gcloud run services describe [SERVICE] --region=europe-west1 --format=yaml | grep env -A 20

# Verify image exists
gcloud container images list --repository=gcr.io/${PROJECT_ID}
```

### Authentication Errors
```bash
# Check Firebase config
gcloud run services describe dashboard-backend --region=europe-west1 --format=yaml | grep -A 5 secrets

# Verify service account
gcloud iam service-accounts list
```

### Pub/Sub Not Triggering
```bash
# Check Eventarc triggers
gcloud eventarc triggers list --location=europe-west1

# Verify subscription
gcloud pubsub subscriptions describe [SUBSCRIPTION]

# Check service account permissions
gcloud projects get-iam-policy $PROJECT_ID | grep eventarc
```

### Firestore Access Denied
```bash
# Check security rules
firebase firestore:rules:get

# Verify service account has datastore.user role
gcloud projects get-iam-policy $PROJECT_ID | grep datastore
```

---

## 📞 Emergency Contacts

### Documentation
- Operations Runbook: [`OPERATIONS_RUNBOOK.md`](OPERATIONS_RUNBOOK.md)
- Backup Strategy: [`docs/operations/BACKUP_STRATEGY.md`](docs/operations/BACKUP_STRATEGY.md)
- Deployment Guide: [`docs/deployment/PRODUCTION_DEPLOYMENT_GUIDE.md`](docs/deployment/PRODUCTION_DEPLOYMENT_GUIDE.md)

### GCP Console URLs
- Project Dashboard: https://console.cloud.google.com/home/dashboard?project=project-52b2fab8-15a1-4b66-9f3
- Cloud Run: https://console.cloud.google.com/run?project=project-52b2fab8-15a1-4b66-9f3
- Cloud Logging: https://console.cloud.google.com/logs?project=project-52b2fab8-15a1-4b66-9f3
- Firestore: https://console.cloud.google.com/firestore?project=project-52b2fab8-15a1-4b66-9f3
- Pub/Sub: https://console.cloud.google.com/cloudpubsub?project=project-52b2fab8-15a1-4b66-9f3

### Team Contacts
- Project Lead: [TBD]
- DevOps Lead: [TBD]
- On-Call (Alpha): Manual monitoring only

---

## 📝 Common Workflows

### Deploy New Version

```bash
# 1. Build and push
docker build -t gcr.io/${PROJECT_ID}/[AGENT]:v1.1 -f agents/[AGENT]/Dockerfile .
docker push gcr.io/${PROJECT_ID}/[AGENT]:v1.1

# 2. Deploy with traffic split (canary)
gcloud run deploy [AGENT] --image=gcr.io/${PROJECT_ID}/[AGENT]:v1.1 \
  --region=europe-west1 --no-traffic

# 3. Test new revision
NEW_REV=$(gcloud run revisions list --service=[AGENT] --region=europe-west1 --format='value(name)' | head -1)
gcloud run services update-traffic [AGENT] --region=europe-west1 --to-revisions=$NEW_REV=10

# 4. Roll out gradually
gcloud run services update-traffic [AGENT] --region=europe-west1 --to-revisions=$NEW_REV=50
gcloud run services update-traffic [AGENT] --region=europe-west1 --to-revisions=$NEW_REV=100
```

### Backup & Restore

```bash
# 1. Backup Firestore
gcloud firestore export gs://${PROJECT_ID}-firestore-backups/$(date +%Y%m%d)

# 2. Backup Configuration
mkdir -p config-backup
gcloud projects get-iam-policy $PROJECT_ID > config-backup/iam-policy.yaml
for service in $(gcloud run services list --region=europe-west1 --format='value(name)'); do
  gcloud run services describe $service --region=europe-west1 --format=yaml > "config-backup/service-${service}.yaml"
done

# 3. Restore (if needed)
gcloud firestore import gs://${PROJECT_ID}-firestore-backups/[BACKUP_ID]
```

### Add New User (Alpha)

```bash
# 1. User registriert sich via Dashboard
# 2. Verify in Firebase Console
# 3. Check Firestore user document created
gcloud firestore documents describe users/[USER_ID]

# 4. Monitor first upload
gcloud logging read "resource.labels.service_name=ingestion-agent AND jsonPayload.user_id=[USER_ID]" --limit=50
```

---

## 🎯 Pre-Launch Checklist (Quick)

### Alpha Launch (5 min check)

- [ ] All services deployed and healthy
- [ ] Cloud Logging active
- [ ] Error Reporting configured
- [ ] Firestore backups running
- [ ] Environment variables set
- [ ] Smoke tests passed

**Command:**
```bash
# Run all checks
bash OPERATIONS_RUNBOOK.md  # Quick Health Check section
```

### Daily Monitoring (2 min)

- [ ] Check error logs
- [ ] Verify all services healthy
- [ ] Check user activity
- [ ] Review costs

**Command:**
```bash
# Daily check script
gcloud logging read "severity>=ERROR AND timestamp>=\"$(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ)\"" --limit=20
gcloud run services list --region=europe-west1 --format="table(name,status.conditions[0].status)"
```

---

## 💡 Pro Tips

1. **Set Aliases** (add to ~/.bashrc):
   ```bash
   alias gcr='gcloud run'
   alias glog='gcloud logging read'
   alias gfs='gcloud firestore'
   ```

2. **Use jq for JSON parsing**:
   ```bash
   gcloud run services describe [SERVICE] --format=json | jq '.status.url'
   ```

3. **Watch logs in real-time**:
   ```bash
   gcloud run logs tail [SERVICE] --region=europe-west1 | grep -i error
   ```

4. **Save common filters**:
   ```bash
   export ERROR_FILTER='resource.type=cloud_run_revision AND severity>=ERROR'
   gcloud logging read "$ERROR_FILTER" --limit=50
   ```

5. **Quick service restart**:
   ```bash
   gcloud run services update [SERVICE] --region=europe-west1 --update-env-vars=_=$(date +%s)
   ```

---

**Last Updated:** 2025-11-01  
**Version:** 1.0
**For detailed commands:** See [`docs/deployment/PRODUCTION_DEPLOYMENT_GUIDE.md`](docs/deployment/PRODUCTION_DEPLOYMENT_GUIDE.md)
**For troubleshooting:** See [`docs/operations/OPERATIONS_RUNBOOK.md`](docs/operations/OPERATIONS_RUNBOOK.md)
