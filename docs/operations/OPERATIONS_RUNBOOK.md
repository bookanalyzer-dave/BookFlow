# Operations Runbook - Alpha Launch

**Version:** 1.0  
**Last Updated:** 2025-11-01  
**Environment:** Alpha  
**Project:** Intelligent Book Sales Pipeline

---

## 📋 Inhaltsverzeichnis

1. [Schnellzugriff](#schnellzugriff)
2. [Common Issues & Solutions](#common-issues--solutions)
3. [Emergency Procedures](#emergency-procedures)
4. [Health Check Commands](#health-check-commands)
5. [Agent-Specific Troubleshooting](#agent-specific-troubleshooting)
6. [Database Operations](#database-operations)
7. [Monitoring & Logs](#monitoring--logs)

---

## Schnellzugriff

### Wichtige Links

- **Cloud Console:** https://console.cloud.google.com/home/dashboard?project=project-52b2fab8-15a1-4b66-9f3
- **Cloud Logging:** https://console.cloud.google.com/logs?project=project-52b2fab8-15a1-4b66-9f3
- **Error Reporting:** https://console.cloud.google.com/errors?project=project-52b2fab8-15a1-4b66-9f3
- **Cloud Run Services:** https://console.cloud.google.com/run?project=project-52b2fab8-15a1-4b66-9f3
- **Firestore Console:** https://console.cloud.google.com/firestore?project=project-52b2fab8-15a1-4b66-9f3

### Emergency Contacts

| Role | Contact | Availability |
|------|---------|--------------|
| DevOps Lead | TBD | Business Hours |
| Backend Lead | TBD | Business Hours |
| On-Call (Alpha) | TBD | Mon-Fri 9-17 CET |

---

## Common Issues & Solutions

### 1. User kann sich nicht anmelden

**Symptome:**
- Login-Fehler im Frontend
- "Invalid token" Fehlermeldung
- Firebase Authentication Fehler

**Diagnose:**
```bash
# Check Firebase Auth Status
gcloud auth list --project=project-52b2fab8-15a1-4b66-9f3

# Check Backend Logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=dashboard-backend AND textPayload=~'auth'" --limit=50 --project=project-52b2fab8-15a1-4b66-9f3
```

**Lösungen:**

#### Problem: Token abgelaufen
```bash
# User muss sich neu einloggen
# Im Frontend: Logout → Login
```

#### Problem: Firebase Configuration falsch
```bash
# Check Firebase Config
cat dashboard/frontend/src/firebaseConfig.js

# Verify environment variables
gcloud run services describe dashboard-backend --region=europe-west1 --project=project-52b2fab8-15a1-4b66-9f3 --format="value(spec.template.spec.containers[0].env)"
```

#### Problem: Backend kann Token nicht verifizieren
```bash
# Check Service Account Key
ls -la service-account-key.json

# Test Token Verification
python -c "
from firebase_admin import auth, credentials
import firebase_admin
cred = credentials.Certificate('service-account-key.json')
firebase_admin.initialize_app(cred)
print('Firebase Admin SDK initialized successfully')
"
```

**Eskalation:** Wenn Problem nach 15min nicht gelöst → Backend Lead kontaktieren

---

### 2. Bilder werden nicht hochgeladen

**Symptome:**
- Upload hängt im Frontend
- Signed URL Fehler
- GCS Upload Fehler

**Diagnose:**
```bash
# Check GCS Bucket
gsutil ls gs://project-52b2fab8-15a1-4b66-9f3-book-images/

# Check Backend Upload Endpoint
curl -X POST https://dashboard-backend-xxx.run.app/api/books/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"filename": "test.jpg", "contentType": "image/jpeg"}'

# Check recent upload errors
gcloud logging read "resource.labels.service_name=dashboard-backend AND textPayload=~'upload'" --limit=20 --project=project-52b2fab8-15a1-4b66-9f3
```

**Lösungen:**

#### Problem: Signed URL expired
```bash
# Signed URLs sind 15min gültig
# User muss Upload neu starten
# Check URL generation in backend:
grep "generate_signed_url" dashboard/backend/main.py
```

#### Problem: GCS Permissions fehlen
```bash
# Check Service Account Permissions
gcloud projects get-iam-policy project-52b2fab8-15a1-4b66-9f3 \
  --flatten="bindings[].members" \
  --filter="bindings.members:serviceAccount" \
  --format="table(bindings.role)"

# Add Storage Admin role if missing
gcloud projects add-iam-policy-binding project-52b2fab8-15a1-4b66-9f3 \
  --member="serviceAccount:YOUR-SA@project-52b2fab8-15a1-4b66-9f3.iam.gserviceaccount.com" \
  --role="roles/storage.admin"
```

#### Problem: CORS Configuration
```bash
# Check CORS config
gsutil cors get gs://project-52b2fab8-15a1-4b66-9f3-book-images/

# Apply CORS if needed
gsutil cors set cors.json gs://project-52b2fab8-15a1-4b66-9f3-book-images/
```

**Eskalation:** Wenn Uploads komplett blockiert → P1 Incident, sofort eskalieren

---

### 3. Agent-Fehler / Timeouts

**Symptome:**
- Book Status bleibt auf "ingested" stecken
- Agent wirft Fehler in Logs
- Timeout-Fehler

**Diagnose:**
```bash
# Check Agent Status
gcloud run services list --platform=managed --region=europe-west1 --project=project-52b2fab8-15a1-4b66-9f3

# Check specific agent logs
gcloud logging read "resource.labels.service_name=ingestion-agent" --limit=50 --project=project-52b2fab8-15a1-4b66-9f3

# Check Pub/Sub messages
gcloud pubsub topics list --project=project-52b2fab8-15a1-4b66-9f3
gcloud pubsub subscriptions list --project=project-52b2fab8-15a1-4b66-9f3
```

**Lösungen:**

#### Problem: Agent Timeout
```bash
# Check agent timeout settings
gcloud run services describe ingestion-agent --region=europe-west1 --project=project-52b2fab8-15a1-4b66-9f3 --format="value(spec.template.spec.timeoutSeconds)"

# Increase timeout if needed (max 3600s)
gcloud run services update ingestion-agent \
  --timeout=300 \
  --region=europe-west1 \
  --project=project-52b2fab8-15a1-4b66-9f3
```

#### Problem: Agent ist down
```bash
# Restart agent (force new revision)
gcloud run services update ingestion-agent \
  --region=europe-west1 \
  --project=project-52b2fab8-15a1-4b66-9f3 \
  --update-env-vars=RESTART_TIME=$(date +%s)
```

#### Problem: Pub/Sub Backlog
```bash
# Check subscription backlog
gcloud pubsub subscriptions describe trigger-ingestion-sub --project=project-52b2fab8-15a1-4b66-9f3

# Manually acknowledge stuck messages (careful!)
# gcloud pubsub subscriptions pull trigger-ingestion-sub --auto-ack --limit=10 --project=project-52b2fab8-15a1-4b66-9f3
```

**Eskalation:** Wenn Agent nach Restart nicht funktioniert → DevOps Lead kontaktieren

---

### 4. LLM API-Fehler

**Symptome:**
- "LLM request failed" Fehler
- Condition Assessment schlägt fehl
- User LLM Budget überschritten

**Diagnose:**
```bash
# Check LLM Usage
# Query Firestore for user's LLM usage
python -c "
from shared.firestore.client import get_firestore_client
db = get_firestore_client()
usage = db.collection('users').document('USER_ID').collection('llm_usage').limit(10).stream()
for doc in usage:
    print(doc.to_dict())
"

# Check LLM Error Logs
gcloud logging read "jsonPayload.error_type=~'LLM'" --limit=20 --project=project-52b2fab8-15a1-4b66-9f3
```

**Lösungen:**

#### Problem: User API Key ungültig
```bash
# User muss API Key neu eingeben
# Check credential status in Firestore:
# users/{uid}/llm_credentials/{provider}
```

#### Problem: System Fallback schlägt fehl
```bash
# Check Vertex AI Quota
gcloud services quota list --service=aiplatform.googleapis.com --project=project-52b2fab8-15a1-4b66-9f3

# Check service account permissions
gcloud projects get-iam-policy project-52b2fab8-15a1-4b66-9f3 \
  --flatten="bindings[].members" \
  --filter="bindings.role:roles/aiplatform.user"
```

#### Problem: Rate Limiting
```bash
# Check rate limit logs
gcloud logging read "jsonPayload.error=~'rate.limit'" --limit=20 --project=project-52b2fab8-15a1-4b66-9f3

# User muss warten oder API Key mit höherem Limit verwenden
```

**Eskalation:** Persistent LLM failures → Backend Lead kontaktieren

---

## Emergency Procedures

### System-Wide Outage

**Immediate Actions:**
1. ✅ Verify outage scope (all users or specific?)
2. ✅ Check Cloud Status: https://status.cloud.google.com/
3. ✅ Check Cloud Run Services health
4. ✅ Review recent deployments
5. ✅ Notify users (if >10min outage expected)

**Recovery Steps:**
```bash
# 1. Check all services
gcloud run services list --platform=managed --region=europe-west1 --project=project-52b2fab8-15a1-4b66-9f3

# 2. Check for recent changes
gcloud logging read "protoPayload.methodName=~'deploy'" --limit=10 --project=project-52b2fab8-15a1-4b66-9f3

# 3. Rollback if needed (see below)
```

### Rollback Procedure

```bash
# List recent revisions
gcloud run revisions list --service=dashboard-backend --region=europe-west1 --project=project-52b2fab8-15a1-4b66-9f3

# Rollback to previous revision
PREVIOUS_REVISION=$(gcloud run revisions list --service=dashboard-backend --region=europe-west1 --project=project-52b2fab8-15a1-4b66-9f3 --format="value(name)" --limit=2 | tail -n 1)

gcloud run services update-traffic dashboard-backend \
  --to-revisions=$PREVIOUS_REVISION=100 \
  --region=europe-west1 \
  --project=project-52b2fab8-15a1-4b66-9f3

# Verify traffic shift
gcloud run services describe dashboard-backend --region=europe-west1 --project=project-52b2fab8-15a1-4b66-9f3 --format="value(status.traffic)"
```

### Database Emergency Recovery

```bash
# 1. Stop all write operations (if possible)
# 2. Create emergency backup
gcloud firestore export gs://project-52b2fab8-15a1-4b66-9f3-backups/emergency-$(date +%Y%m%d-%H%M%S) --project=project-52b2fab8-15a1-4b66-9f3

# 3. For data corruption: Restore from backup (see BACKUP_STRATEGY.md)
```

### Emergency Contacts Escalation

1. **0-15 min:** Attempt self-resolution using this runbook
2. **15-30 min:** Contact DevOps Lead / Backend Lead
3. **30+ min:** Escalate to Project Lead
4. **Critical Data Loss:** Immediate escalation to all

---

## Health Check Commands

### Quick Health Check (1 minute)

```bash
#!/bin/bash
# quick_health_check.sh

PROJECT_ID="project-52b2fab8-15a1-4b66-9f3"
REGION="europe-west1"

echo "=== Quick Health Check ==="
echo ""

# 1. Backend Health
echo "1. Backend Service:"
curl -s https://dashboard-backend-xxx.run.app/api/health | jq .
echo ""

# 2. Firestore Connection
echo "2. Firestore:"
python -c "from shared.firestore.client import get_firestore_client; print('✓ Connected')" 2>&1
echo ""

# 3. Cloud Run Services
echo "3. Cloud Run Services:"
gcloud run services list --platform=managed --region=$REGION --project=$PROJECT_ID --format="table(metadata.name, status.conditions[0].status)"
echo ""

# 4. Recent Errors
echo "4. Recent Errors (last 5min):"
gcloud logging read "severity=ERROR AND timestamp>$(date -u -d '5 minutes ago' +%Y-%m-%dT%H:%M:%SZ)" --limit=5 --project=$PROJECT_ID --format="value(textPayload)"
echo ""

echo "=== Health Check Complete ==="
```

### Comprehensive Health Check (5 minutes)

```bash
#!/bin/bash
# comprehensive_health_check.sh

PROJECT_ID="project-52b2fab8-15a1-4b66-9f3"
REGION="europe-west1"

echo "=== Comprehensive Health Check ==="
echo ""

# 1. All Cloud Run Services
echo "1. Cloud Run Services Status:"
for service in dashboard-backend ingestion-agent condition-assessor strategist-agent ambassador-agent sentinel-webhook; do
    echo -n "  $service: "
    gcloud run services describe $service --region=$REGION --project=$PROJECT_ID --format="value(status.conditions[0].status)" 2>/dev/null || echo "NOT FOUND"
done
echo ""

# 2. Firestore Health
echo "2. Firestore Health:"
python <<EOF
from shared.firestore.client import get_firestore_client
db = get_firestore_client()
users = db.collection('users').limit(1).get()
print(f"  ✓ Connected, {len(list(users))} user(s) found")
EOF
echo ""

# 3. GCS Bucket
echo "3. Cloud Storage:"
gsutil ls gs://project-52b2fab8-15a1-4b66-9f3-book-images/ 2>&1 | head -n 1
echo ""

# 4. Pub/Sub Topics
echo "4. Pub/Sub Topics:"
gcloud pubsub topics list --project=$PROJECT_ID --format="value(name)" | wc -l | xargs echo "  Topics:"
echo ""

# 5. Error Rate (last hour)
echo "5. Error Rate (last hour):"
gcloud logging read "severity=ERROR AND timestamp>$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)" --project=$PROJECT_ID --format=json | jq 'length' | xargs echo "  Errors:"
echo ""

# 6. Active Users (last 24h)
echo "6. Active Users (last 24h):"
gcloud logging read "jsonPayload.user_id!=\"\" AND timestamp>$(date -u -d '24 hours ago' +%Y-%m-%dT%H:%M:%SZ)" --project=$PROJECT_ID --format="value(jsonPayload.user_id)" | sort -u | wc -l | xargs echo "  Users:"
echo ""

echo "=== Comprehensive Check Complete ==="
```

### Agent Response Time Check

```bash
# Test agent response times
python <<EOF
import time
import requests

agents = {
    "ingestion-agent": "https://ingestion-agent-xxx.run.app/health",
    "condition-assessor": "https://condition-assessor-xxx.run.app/health"
}

for agent, url in agents.items():
    start = time.time()
    try:
        response = requests.get(url, timeout=10)
        duration = time.time() - start
        print(f"{agent}: {duration:.2f}s - {response.status_code}")
    except Exception as e:
        print(f"{agent}: FAILED - {e}")
EOF
```

---

## Agent-Specific Troubleshooting

### Ingestion Agent

**Check Processing Status:**
```bash
# View recent ingestion logs
gcloud logging read "resource.labels.service_name=ingestion-agent" --limit=20 --project=project-52b2fab8-15a1-4b66-9f3

# Check for Vision API errors
gcloud logging read "resource.labels.service_name=ingestion-agent AND textPayload=~'vision'" --limit=10 --project=project-52b2fab8-15a1-4b66-9f3
```

**Force Reprocess Book:**
```bash
# Via API
curl -X POST https://dashboard-backend-xxx.run.app/api/books/BOOK_ID/reprocess \
  -H "Authorization: Bearer TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Corrected Title"}'
```

### Condition Assessor

**Check Assessment Status:**
```bash
# Query Firestore for assessments
python <<EOF
from shared.firestore.client import get_firestore_client
db = get_firestore_client()
assessments = db.collection('users').document('USER_ID').collection('condition_assessments').get()
for a in assessments:
    data = a.to_dict()
    print(f"{a.id}: {data.get('grade')} - {data.get('overall_score')}%")
EOF
```

### Ambassador Agent (eBay Listings)

**Check Listing Status:**
```bash
# View listing logs
gcloud logging read "resource.labels.service_name=ambassador-agent" --limit=20 --project=project-52b2fab8-15a1-4b66-9f3

# Check for eBay API errors
gcloud logging read "textPayload=~'eBay.*error'" --limit=10 --project=project-52b2fab8-15a1-4b66-9f3
```

---

## Database Operations

### Query Book Status

```bash
# Using Python
python <<EOF
from shared.firestore.client import get_firestore_client
db = get_firestore_client()

# Get book by ID
book = db.collection('users').document('USER_ID').collection('books').document('BOOK_ID').get()
if book.exists:
    print(book.to_dict())
else:
    print("Book not found")
EOF
```

### Update Book Status Manually

```bash
# Update book status (use with caution!)
python <<EOF
from shared.firestore.client import get_firestore_client, update_book
update_book('USER_ID', 'BOOK_ID', {'status': 'needs_review', 'manual_intervention': True})
print("Book status updated")
EOF
```

### Check User LLM Usage

```bash
python <<EOF
from shared.firestore.client import get_firestore_client
db = get_firestore_client()

usage_docs = db.collection('users').document('USER_ID').collection('llm_usage').order_by('timestamp', direction='DESCENDING').limit(10).stream()
for doc in usage_docs:
    data = doc.to_dict()
    print(f"{data.get('timestamp')}: {data.get('provider')} - ${data.get('cost'):.4f}")
EOF
```

---

## Monitoring & Logs

### View Real-Time Logs

```bash
# Stream logs from all services
gcloud logging tail --project=project-52b2fab8-15a1-4b66-9f3

# Stream specific service logs
gcloud logging tail "resource.labels.service_name=dashboard-backend" --project=project-52b2fab8-15a1-4b66-9f3

# Filter for errors only
gcloud logging tail "severity>=ERROR" --project=project-52b2fab8-15a1-4b66-9f3
```

### Search Logs for Specific User

```bash
# Find all logs for a user
USER_ID="abc123"
gcloud logging read "jsonPayload.user_id=\"$USER_ID\" OR jsonPayload.uid=\"$USER_ID\"" --limit=50 --project=project-52b2fab8-15a1-4b66-9f3
```

### Export Logs for Analysis

```bash
# Export last hour of logs
gcloud logging read "timestamp>$(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%SZ)" --project=project-52b2fab8-15a1-4b66-9f3 --format=json > logs_export.json

# Analyze with jq
cat logs_export.json | jq '.[] | select(.severity=="ERROR") | .textPayload'
```

---

## Performance Monitoring

### Check Response Times

```bash
# Query for slow requests (>5s)
gcloud logging read "httpRequest.latency>\"5s\"" --limit=20 --project=project-52b2fab8-15a1-4b66-9f3
```

### Check Resource Usage

```bash
# CPU/Memory usage
gcloud monitoring time-series list \
  --filter='metric.type="run.googleapis.com/container/cpu/utilizations"' \
  --project=project-52b2fab8-15a1-4b66-9f3
```

---

## Maintenance Windows

### Scheduled Maintenance

**Process:**
1. Announce maintenance 24h in advance (email to alpha users)
2. Set status page to "Maintenance"
3. Perform updates during low-traffic hours (22:00-02:00 CET)
4. Test thoroughly before reopening
5. Monitor closely for 1h after maintenance

**Deployment During Maintenance:**
```bash
# Deploy with zero downtime
gcloud run deploy SERVICE_NAME \
  --image=gcr.io/PROJECT/IMAGE:TAG \
  --region=europe-west1 \
  --no-traffic \
  --project=project-52b2fab8-15a1-4b66-9f3

# Test new revision
# If OK: Route traffic
gcloud run services update-traffic SERVICE_NAME \
  --to-latest \
  --region=europe-west1 \
  --project=project-52b2fab8-15a1-4b66-9f3
```

---

## Appendix

### Useful Commands Cheat Sheet

```bash
# Quick service restart
gcloud run services update SERVICE --update-env-vars=DUMMY=$(date +%s) --region=europe-west1 --project=project-52b2fab8-15a1-4b66-9f3

# View service URL
gcloud run services describe SERVICE --region=europe-west1 --project=project-52b2fab8-15a1-4b66-9f3 --format="value(status.url)"

# Check service account
gcloud iam service-accounts list --project=project-52b2fab8-15a1-4b66-9f3

# Test Firestore connection
python -c "from shared.firestore.client import get_firestore_client; db=get_firestore_client(); print('OK')"
```

### Log Severity Levels

- `DEFAULT` - Routine information
- `DEBUG` - Debug information
- `INFO` - Informational messages
- `NOTICE` - Normal but significant
- `WARNING` - Warning messages
- `ERROR` - Error conditions
- `CRITICAL` - Critical conditions
- `ALERT` - Action must be taken immediately
- `EMERGENCY` - System is unusable

---

**Last Review:** 2025-11-01  
**Next Review:** After 2 weeks of Alpha operation  
**Maintained By:** DevOps Team
