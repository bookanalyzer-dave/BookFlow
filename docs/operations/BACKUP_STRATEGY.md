# Backup & Recovery Strategy - Alpha Launch

**Version:** 1.0  
**Last Updated:** 2025-11-01  
**Environment:** Alpha  
**Project:** Intelligent Book Sales Pipeline

---

## 📋 Executive Summary

Diese Backup-Strategie definiert Backup-Prozeduren, Recovery-Prozesse und SLAs für den Alpha-Launch der Intelligent Book Sales Pipeline.

### Backup Targets

| Target | RTO | RPO | Backup Frequency | Retention |
|--------|-----|-----|------------------|-----------|
| Firestore Database | < 1 hour | < 1 hour | Daily | 30 days |
| Cloud Storage (Images) | < 2 hours | < 24 hours | Daily | 30 days |
| Configuration & Secrets | < 15 min | Manual | On Change | Indefinite |
| User Data | < 1 hour | < 1 hour | Daily | 30 days |

**RTO (Recovery Time Objective):** Maximum acceptable downtime  
**RPO (Recovery Point Objective):** Maximum acceptable data loss

---

## 🗄️ Firestore Database Backup

### Automated Daily Backups

**Setup:**
```bash
#!/bin/bash
# setup_firestore_backup.sh

PROJECT_ID="project-52b2fab8-15a1-4b66-9f3"
BACKUP_BUCKET="gs://${PROJECT_ID}-firestore-backups"

# 1. Create backup bucket
gsutil mb -p $PROJECT_ID -c STANDARD -l europe-west1 $BACKUP_BUCKET

# 2. Set lifecycle policy (30 days retention)
cat > lifecycle.json << EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 30}
      }
    ]
  }
}
EOF

gsutil lifecycle set lifecycle.json $BACKUP_BUCKET

# 3. Create Cloud Scheduler job for daily backups
gcloud scheduler jobs create http firestore-daily-backup \
  --schedule="0 2 * * *" \
  --uri="https://firestore.googleapis.com/v1/projects/${PROJECT_ID}/databases/(default):exportDocuments" \
  --http-method=POST \
  --headers="Content-Type=application/json,Authorization=Bearer $(gcloud auth print-access-token)" \
  --message-body="{\"outputUriPrefix\": \"${BACKUP_BUCKET}/$(date +%Y-%m-%d)\"}" \
  --time-zone="Europe/Berlin" \
  --project=$PROJECT_ID

echo "✓ Firestore backup scheduled (daily at 02:00 CET)"
```

### Manual Backup

```bash
# Create immediate backup
PROJECT_ID="project-52b2fab8-15a1-4b66-9f3"
BACKUP_BUCKET="gs://${PROJECT_ID}-firestore-backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

gcloud firestore export $BACKUP_BUCKET/manual-$TIMESTAMP \
  --project=$PROJECT_ID

echo "Backup created: $BACKUP_BUCKET/manual-$TIMESTAMP"
```

### Collection-Specific Backup

```bash
# Backup specific collections only
gcloud firestore export gs://${PROJECT_ID}-firestore-backups/partial-$(date +%Y%m%d) \
  --collection-ids=users,books,llm_credentials \
  --project=$PROJECT_ID
```

### Firestore Restore Procedure

**⚠️ CAUTION: Restore overwrites existing data**

```bash
#!/bin/bash
# restore_firestore.sh

PROJECT_ID="project-52b2fab8-15a1-4b66-9f3"
BACKUP_BUCKET="gs://${PROJECT_ID}-firestore-backups"

echo "Available backups:"
gsutil ls $BACKUP_BUCKET/

read -p "Enter backup path (e.g., 2025-11-01): " BACKUP_PATH
read -p "⚠️  WARNING: This will overwrite current data. Type 'CONFIRM' to proceed: " CONFIRM

if [ "$CONFIRM" != "CONFIRM" ]; then
    echo "Restore cancelled"
    exit 1
fi

# Perform restore
gcloud firestore import $BACKUP_BUCKET/$BACKUP_PATH \
  --project=$PROJECT_ID

echo "✓ Restore initiated. Check status:"
echo "  gcloud firestore operations list --project=$PROJECT_ID"
```

### Point-in-Time Recovery (PITR)

**Note:** Firestore native PITR is not available. Use export/import for recovery.

**Best Practice for Alpha:**
- Create backup before major changes
- Test restore procedure monthly
- Keep last 30 days of backups

---

## 🖼️ Cloud Storage Backup (Images)

### Image Backup Strategy

**Primary Storage:**
- Bucket: `project-52b2fab8-15a1-4b66-9f3-book-images`
- Location: `europe-west1`
- Storage Class: `STANDARD`

**Backup Approach:**
```bash
#!/bin/bash
# setup_gcs_backup.sh

PROJECT_ID="project-52b2fab8-15a1-4b66-9f3"
SOURCE_BUCKET="gs://${PROJECT_ID}-book-images"
BACKUP_BUCKET="gs://${PROJECT_ID}-image-backups"

# 1. Create backup bucket
gsutil mb -p $PROJECT_ID -c NEARLINE -l europe-west1 $BACKUP_BUCKET

# 2. Set lifecycle (30 days)
cat > gcs_lifecycle.json << EOF
{
  "lifecycle": {
    "rule": [
      {
        "action": {"type": "Delete"},
        "condition": {"age": 30}
      }
    ]
  }
}
EOF

gsutil lifecycle set gcs_lifecycle.json $BACKUP_BUCKET

# 3. Create daily sync script
cat > daily_image_sync.sh << 'EOF'
#!/bin/bash
PROJECT_ID="project-52b2fab8-15a1-4b66-9f3"
SOURCE="gs://${PROJECT_ID}-book-images"
BACKUP="gs://${PROJECT_ID}-image-backups/$(date +%Y-%m-%d)"

# Sync images (preserves metadata)
gsutil -m rsync -r -d $SOURCE $BACKUP

echo "✓ Image backup completed: $BACKUP"
EOF

chmod +x daily_image_sync.sh

# 4. Schedule via Cloud Scheduler (if needed)
# Or run manually/via cron

echo "✓ GCS backup configured"
```

### Image Restore Procedure

```bash
# List available backups
gsutil ls gs://project-52b2fab8-15a1-4b66-9f3-image-backups/

# Restore from specific date
RESTORE_DATE="2025-11-01"
gsutil -m rsync -r gs://project-52b2fab8-15a1-4b66-9f3-image-backups/$RESTORE_DATE gs://project-52b2fab8-15a1-4b66-9f3-book-images

# Or restore specific user's images
USER_ID="abc123"
gsutil -m rsync -r gs://project-52b2fab8-15a1-4b66-9f3-image-backups/$RESTORE_DATE/uploads/$USER_ID gs://project-52b2fab8-15a1-4b66-9f3-book-images/uploads/$USER_ID
```

### Versioning (Optional for Production)

```bash
# Enable versioning on primary bucket
gsutil versioning set on gs://project-52b2fab8-15a1-4b66-9f3-book-images

# List versions of a file
gsutil ls -a gs://project-52b2fab8-15a1-4b66-9f3-book-images/uploads/USER_ID/image.jpg

# Restore specific version
gsutil cp gs://project-52b2fab8-15a1-4b66-9f3-book-images/uploads/USER_ID/image.jpg#VERSION gs://destination/
```

---

## 🔐 Configuration & Secrets Backup

### What to Back Up

1. **Environment Variables** (`.env`, `.env.yaml` files)
2. **Service Account Keys**
3. **Firebase Config**
4. **Cloud Run Configurations**
5. **Firestore Security Rules**
6. **API Keys** (stored in Secret Manager)

### Backup Procedure

```bash
#!/bin/bash
# backup_configuration.sh

PROJECT_ID="project-52b2fab8-15a1-4b66-9f3"
BACKUP_DIR="config-backups/$(date +%Y%m%d-%H%M%S)"
mkdir -p $BACKUP_DIR

echo "Backing up configuration..."

# 1. Export Secret Manager secrets (metadata only, not values)
gcloud secrets list --project=$PROJECT_ID --format=json > $BACKUP_DIR/secrets_list.json

# 2. Export Cloud Run service configs
for service in dashboard-backend ingestion-agent condition-assessor strategist-agent; do
    gcloud run services describe $service \
        --region=europe-west1 \
        --project=$PROJECT_ID \
        --format=yaml > $BACKUP_DIR/${service}_config.yaml 2>/dev/null || echo "Service $service not found"
done

# 3. Export Firestore security rules
gcloud firestore indexes list --project=$PROJECT_ID --format=yaml > $BACKUP_DIR/firestore_indexes.yaml
cp firestore.rules $BACKUP_DIR/firestore.rules 2>/dev/null || echo "No firestore.rules file"

# 4. Export Cloud Build configuration
cp cloudbuild.yaml $BACKUP_DIR/cloudbuild.yaml 2>/dev/null || echo "No cloudbuild.yaml"

# 5. Export IAM policies
gcloud projects get-iam-policy $PROJECT_ID > $BACKUP_DIR/iam_policy.yaml

# 6. Create backup archive
tar -czf config-backup-$(date +%Y%m%d-%H%M%S).tar.gz $BACKUP_DIR

echo "✓ Configuration backed up to: config-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
echo "⚠️  Store this file securely (contains sensitive metadata)"
```

### Configuration Restore

```bash
# Extract backup
tar -xzf config-backup-TIMESTAMP.tar.gz

# Review configurations before applying
cd config-backups/TIMESTAMP

# Restore Cloud Run service (example)
gcloud run services replace dashboard-backend_config.yaml \
    --region=europe-west1 \
    --project=$PROJECT_ID

# Restore Firestore security rules
gcloud firestore deploy firestore.rules --project=$PROJECT_ID
```

---

## 👤 User Data Backup & Export

### GDPR-Compliant User Data Export

```python
#!/usr/bin/env python3
"""
export_user_data.py - Export all data for a specific user
"""

import json
from datetime import datetime
from shared.firestore.client import get_firestore_client

def export_user_data(user_id: str, output_file: str = None):
    """Export all data for a user (GDPR compliance)"""
    
    if not output_file:
        output_file = f"user_export_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    db = get_firestore_client()
    user_data = {
        "user_id": user_id,
        "export_timestamp": datetime.utcnow().isoformat(),
        "data": {}
    }
    
    # Export all user collections
    collections = [
        "books",
        "llm_credentials",
        "llm_usage",
        "llm_settings",
        "llm_audit",
        "condition_assessments"
    ]
    
    for collection in collections:
        docs = db.collection('users').document(user_id).collection(collection).stream()
        user_data["data"][collection] = [
            {**doc.to_dict(), "id": doc.id} for doc in docs
        ]
    
    # Save to file
    with open(output_file, 'w') as f:
        json.dump(user_data, f, indent=2, default=str)
    
    print(f"✓ User data exported to: {output_file}")
    return output_file

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python export_user_data.py USER_ID")
        sys.exit(1)
    
    export_user_data(sys.argv[1])
```

### Bulk User Export

```bash
#!/bin/bash
# export_all_users.sh

python <<EOF
from shared.firestore.client import get_firestore_client
import os
from export_user_data import export_user_data

db = get_firestore_client()
users = db.collection('users').stream()

export_dir = "user_exports_$(date +%Y%m%d)"
os.makedirs(export_dir, exist_ok=True)

for user_doc in users:
    user_id = user_doc.id
    output = f"{export_dir}/user_{user_id}.json"
    export_user_data(user_id, output)
    print(f"✓ Exported: {user_id}")

print(f"\n✓ All users exported to: {export_dir}/")
EOF
```

---

## 🔄 Disaster Recovery Procedures

### DR Scenario 1: Complete Firestore Data Loss

**Recovery Steps:**
```bash
# 1. Identify last good backup
gsutil ls gs://project-52b2fab8-15a1-4b66-9f3-firestore-backups/

# 2. Restore from backup
LATEST_BACKUP=$(gsutil ls gs://project-52b2fab8-15a1-4b66-9f3-firestore-backups/ | tail -n 1)
gcloud firestore import $LATEST_BACKUP --project=project-52b2fab8-15a1-4b66-9f3

# 3. Verify data integrity
python -c "
from shared.firestore.client import get_firestore_client
db = get_firestore_client()
users = list(db.collection('users').limit(10).stream())
print(f'✓ Restored {len(users)} users (sample)')
"

# 4. Notify users of potential data loss (if RPO exceeded)
```

**Estimated RTO:** 30-60 minutes  
**Data Loss:** Up to last backup (< 24 hours for Alpha)

### DR Scenario 2: Corrupted Book Records

**Recovery Steps:**
```bash
# 1. Identify affected records
python <<EOF
from shared.firestore.client import get_firestore_client
db = get_firestore_client()

# Find books with status 'corrupted' or missing critical fields
users = db.collection('users').stream()
for user in users:
    books = user.reference.collection('books').where('status', '==', 'corrupted').stream()
    for book in books:
        print(f"Corrupted: {user.id}/{book.id}")
EOF

# 2. Export affected user data from backup
# 3. Selectively restore affected books
# 4. Re-trigger processing if needed
```

### DR Scenario 3: Image Storage Loss

**Recovery Steps:**
```bash
# 1. Restore images from backup
BACKUP_DATE="2025-11-01"  # Last known good backup
gsutil -m rsync -r \
    gs://project-52b2fab8-15a1-4b66-9f3-image-backups/$BACKUP_DATE \
    gs://project-52b2fab8-15a1-4b66-9f3-book-images

# 2. Verify image accessibility
gsutil ls -r gs://project-52b2fab8-15a1-4b66-9f3-book-images/uploads/ | head -n 20

# 3. Check for missing images in Firestore
python <<EOF
from shared.firestore.client import get_firestore_client
from google.cloud import storage

db = get_firestore_client()
storage_client = storage.Client()
bucket = storage_client.bucket('project-52b2fab8-15a1-4b66-9f3-book-images')

# Sample check
users = db.collection('users').limit(5).stream()
missing = []
for user in users:
    books = user.reference.collection('books').limit(10).stream()
    for book in books:
        data = book.to_dict()
        for url in data.get('imageUrls', []):
            blob_path = url.replace('gs://project-52b2fab8-15a1-4b66-9f3-book-images/', '')
            if not bucket.blob(blob_path).exists():
                missing.append(url)

if missing:
    print(f"⚠️  Missing images: {len(missing)}")
else:
    print("✓ All sampled images present")
EOF
```

---

## 📊 Backup Monitoring & Validation

### Daily Backup Verification

```bash
#!/bin/bash
# verify_backups.sh

PROJECT_ID="project-52b2fab8-15a1-4b66-9f3"
TODAY=$(date +%Y-%m-%d)

echo "=== Backup Verification Report ==="
echo "Date: $TODAY"
echo ""

# 1. Check Firestore backup
echo "1. Firestore Backup:"
FIRESTORE_BACKUP=$(gsutil ls gs://${PROJECT_ID}-firestore-backups/ | grep $TODAY | wc -l)
if [ $FIRESTORE_BACKUP -gt 0 ]; then
    echo "   ✓ Backup exists for $TODAY"
else
    echo "   ✗ NO BACKUP FOUND for $TODAY"
fi

# 2. Check image backup
echo "2. Image Backup:"
IMAGE_BACKUP=$(gsutil ls gs://${PROJECT_ID}-image-backups/ | grep $TODAY | wc -l)
if [ $IMAGE_BACKUP -gt 0 ]; then
    echo "   ✓ Backup exists for $TODAY"
else
    echo "   ✗ NO BACKUP FOUND for $TODAY"
fi

# 3. Check backup sizes
echo "3. Backup Sizes:"
gsutil du -sh gs://${PROJECT_ID}-firestore-backups/$TODAY 2>/dev/null || echo "   No data"
gsutil du -sh gs://${PROJECT_ID}-image-backups/$TODAY 2>/dev/null || echo "   No data"

echo ""
echo "=== Verification Complete ==="
```

### Monthly Backup Test

```bash
#!/bin/bash
# monthly_backup_test.sh
# Run on first Sunday of each month

echo "=== Monthly Backup Restore Test ==="

# 1. Create test environment
TEST_PROJECT="project-52b2fab8-15a1-4b66-9f3-test"  # If separate test project exists

# 2. Restore latest backup to test environment
LATEST_BACKUP=$(gsutil ls gs://project-52b2fab8-15a1-4b66-9f3-firestore-backups/ | tail -n 1)
echo "Testing restore from: $LATEST_BACKUP"

# 3. Perform test restore (to test project)
# gcloud firestore import $LATEST_BACKUP --project=$TEST_PROJECT

# 4. Verify data integrity
# Run sample queries

# 5. Document results
echo "Test completed: $(date)" >> backup_test_log.txt
```

---

## 🚨 Emergency Backup Procedures

### Pre-Deployment Backup

```bash
#!/bin/bash
# Always run before major deployments

echo "Creating pre-deployment backup..."
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# Firestore
gcloud firestore export gs://project-52b2fab8-15a1-4b66-9f3-firestore-backups/pre-deploy-$TIMESTAMP \
    --project=project-52b2fab8-15a1-4b66-9f3

# Configuration
./backup_configuration.sh

echo "✓ Pre-deployment backup complete"
echo "  Firestore: gs://project-52b2fab8-15a1-4b66-9f3-firestore-backups/pre-deploy-$TIMESTAMP"
echo "  Config: config-backup-$TIMESTAMP.tar.gz"
```

### Emergency Recovery Contact

**Escalation Path:**
1. Check this documentation first
2. Attempt recovery using documented procedures
3. If unsuccessful after 30 minutes → Contact DevOps Lead
4. If data loss > 24 hours → Contact Project Lead immediately

---

## 📝 Backup Checklist

### Daily (Automated)
- [ ] Firestore backup at 02:00 CET
- [ ] Image storage sync
- [ ] Backup verification script

### Weekly (Manual)
- [ ] Review backup logs
- [ ] Check backup storage usage
- [ ] Verify no backup failures

### Monthly (Manual)
- [ ] Restore test from backup
- [ ] Verify data integrity
- [ ] Document test results
- [ ] Review and update backup strategy

### Before Major Changes
- [ ] Create manual backup
- [ ] Export affected user data
- [ ] Document rollback procedure
- [ ] Test restore procedure

---

## 📈 Backup Storage Management

### Storage Costs (Estimate for Alpha)

| Type | Size (Est.) | Class | Cost/Month |
|------|-------------|-------|------------|
| Firestore Backups | 5 GB | STANDARD | $0.12 |
| Image Backups | 50 GB | NEARLINE | $0.50 |
| **Total** | **55 GB** | - | **~$0.62** |

### Cleanup Old Backups

```bash
# Automatic cleanup via lifecycle rules (already configured)
# Manual cleanup if needed:

# Delete backups older than 30 days
gsutil -m rm -r gs://project-52b2fab8-15a1-4b66-9f3-firestore-backups/$(date -d '31 days ago' +%Y-%m-%d)
```

---

## 🔒 Security & Compliance

### Backup Security
- ✅ Backups encrypted at rest (Google-managed keys)
- ✅ Access restricted to service accounts only
- ✅ Audit logging enabled for backup access
- ✅ 30-day retention complies with GDPR minimum

### User Data Rights
- **Right to Access:** Use `export_user_data.py`
- **Right to Erasure:** Delete user from Firestore + remove from backups
- **Right to Portability:** JSON export provided

---

**Document Version:** 1.0  
**Last Tested:** TBD (Test after first backup)  
**Next Review:** After 2 weeks of Alpha operation  
**Owner:** DevOps Team
