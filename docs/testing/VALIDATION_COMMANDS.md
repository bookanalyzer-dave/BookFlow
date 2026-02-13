# Validierungs-Commands für Condition Assessment Debug

## 1. Pub/Sub Topic prüfen

```bash
# Check if topic exists
gcloud pubsub topics describe trigger-condition-assessment --project=bookscout-440210
```

**Erwartetes Ergebnis:**
```
name: projects/bookscout-440210/topics/trigger-condition-assessment
```

**Falls nicht vorhanden:**
```bash
# Create topic
gcloud pubsub topics create trigger-condition-assessment --project=bookscout-440210
```

---

## 2. Pub/Sub Subscription prüfen

```bash
# Check if subscription exists
gcloud pubsub subscriptions describe condition-assessment-subscription --project=bookscout-440210
```

**Erwartetes Ergebnis:**
```
name: projects/bookscout-440210/subscriptions/condition-assessment-subscription
topic: projects/bookscout-440210/topics/trigger-condition-assessment
pushConfig:
  pushEndpoint: https://condition-assessor-252725930721.europe-west1.run.app
```

**Falls nicht vorhanden:**
```bash
# Create subscription
gcloud pubsub subscriptions create condition-assessment-subscription \
  --topic=trigger-condition-assessment \
  --push-endpoint=https://condition-assessor-252725930721.europe-west1.run.app \
  --push-auth-service-account=bookscout-440210@appspot.gserviceaccount.com \
  --project=bookscout-440210
```

---

## 3. Ingestion Agent Deployment Status prüfen

```bash
# Check deployed version
gcloud run services describe ingestion-agent \
  --region=europe-west1 \
  --project=bookscout-440210 \
  --format="table(metadata.name,status.url,metadata.creationTimestamp,status.latestCreatedRevisionName)"
```

**Interpretation:**
- `metadata.creationTimestamp`: Wann wurde deployed?
- Falls älter als Code-Änderung → **Alte Version deployed**

---

## 4. Ingestion Agent Logs prüfen (letzte Ausführung)

```bash
# Logs vom User-Upload (00:07:47 UTC = 01:07:47 CET)
gcloud logging read "resource.type=cloud_run_revision \
  AND resource.labels.service_name=ingestion-agent \
  AND timestamp>='2025-12-21T23:00:00Z' \
  AND timestamp<='2025-12-22T00:15:00Z'" \
  --limit=100 \
  --project=bookscout-440210 \
  --format=json
```

**Suche nach:**
- ✅ `"Successfully published condition assessment job to Pub/Sub"` → **Neue Version**
- ❌ `"Calling condition-assessor at https://"` → **Alte Version (HTTP)**

---

## 5. Condition Assessor Logs prüfen (zur gleichen Zeit)

```bash
# Logs zur Zeit des Uploads
gcloud logging read "resource.type=cloud_run_revision \
  AND resource.labels.service_name=condition-assessor \
  AND timestamp>='2025-12-21T23:00:00Z' \
  AND timestamp<='2025-12-22T00:15:00Z'" \
  --limit=100 \
  --project=bookscout-440210 \
  --format=json
```

**Suche nach:**
- ✅ `"CONDITION ASSESSOR: New CloudEvent received"` → **CloudEvent empfangen**
- ❌ Keine relevanten Logs → **Nichts empfangen (HTTP statt CloudEvent)**

---

## 6. Firestore Daten prüfen (Console oder CLI)

### Via Firebase Console:
1. Öffne: https://console.firebase.google.com/project/bookscout-440210/firestore/data
2. Navigate zu: `users/{uid}/condition_assessments/{bookId}`
3. Prüfe ob Dokument existiert

### Via gcloud CLI:
```bash
# List all condition assessments for a user (replace USER_ID)
gcloud firestore export gs://bookscout-440210.appspot.com/firestore-exports \
  --collection-ids=condition_assessments \
  --project=bookscout-440210
```

**Falls leer:** Condition Assessor hat nichts geschrieben (bestätigt Problem)

---

## 7. Live-Test nach Deployment

### A) Deploy das Fix-Script ausführen:
```bash
chmod +x fix_condition_assessment_deployment.sh
./fix_condition_assessment_deployment.sh
```

### B) Oder manuell deployen:
```bash
# 1. Topic erstellen (falls nötig)
gcloud pubsub topics create condition-assessment-jobs --project=bookscout-440210

# 2. Subscription erstellen (falls nötig)
gcloud pubsub subscriptions create condition-assessment-subscription \
  --topic=condition-assessment-jobs \
  --push-endpoint=https://condition-assessor-252725930721.europe-west1.run.app \
  --push-auth-service-account=bookscout-440210@appspot.gserviceaccount.com \
  --project=bookscout-440210

# 3. Ingestion Agent deployen
gcloud run deploy ingestion-agent \
  --source=./agents/ingestion-agent \
  --region=europe-west1 \
  --project=bookscout-440210 \
  --platform=managed \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=bookscout-440210" \
  --timeout=540 \
  --memory=1Gi
```

### C) Test mit neuem Upload:
1. Lade 3 Bilder eines Buches im Frontend hoch
2. Warte auf Ingestion-Abschluss
3. Prüfe Logs:

```bash
# Ingestion Agent Logs (sollte Pub/Sub zeigen)
gcloud logging read "resource.type=cloud_run_revision \
  AND resource.labels.service_name=ingestion-agent \
  AND severity>=INFO" \
  --limit=50 \
  --project=bookscout-440210 \
  --format="table(timestamp,textPayload)"

# Condition Assessor Logs (sollte CloudEvent zeigen)
gcloud logging read "resource.type=cloud_run_revision \
  AND resource.labels.service_name=condition-assessor \
  AND severity>=INFO" \
  --limit=50 \
  --project=bookscout-440210 \
  --format="table(timestamp,textPayload)"
```

---

## 8. Erwartete Log-Muster nach Fix

### Ingestion Agent (neue Version):
```
✅ Created condition assessment request in Firestore for book {book_id}
📤 Publishing to Pub/Sub topic: projects/bookscout-440210/topics/condition-assessment-jobs
📦 Payload: book_id={book_id}, user_id={uid}, images_count=3
✅ Successfully published condition assessment job to Pub/Sub
📨 Pub/Sub Message ID: 1234567890
🎯 Condition Assessor should now receive CloudEvent and process book {book_id}
```

### Condition Assessor (empfängt CloudEvent):
```
================================================================================
🎯 CONDITION ASSESSOR: New CloudEvent received
================================================================================
📨 CloudEvent type: google.cloud.pubsub.topic.v1.messagePublished
📨 CloudEvent source: //pubsub.googleapis.com/projects/bookscout-440210/topics/condition-assessment-jobs
📦 Decoded message payload: {"book_id": "...", "user_id": "...", "image_urls": [...]}
✅ Received condition assessment job
   👤 User ID: {uid}
   📚 Book ID: {book_id}
   🖼️  Images: 3
📝 Updating book status to 'processing_condition'...
✅ Book {book_id} status updated to 'processing_condition'
🚀 Starting async condition assessment process...
🔄 process_assessment() started for book {book_id}
🤖 Initializing VertexAIConditionAssessor...
🔍 Starting GenAI condition assessment with 3 images...
✅ GenAI assessment complete. Grade: Good, Score: 75.0
💾 Writing assessment to Firestore: users/{uid}/condition_assessments/{book_id}
   Grade: Good
   Score: 75.0%
   Confidence: 85%
   Price Factor: 0.75
✅ Assessment data written to Firestore
📝 Updating book document with condition results...
✅ Book document updated with status 'condition_assessed'
✅ Request status updated to 'completed'
🎉 Successfully assessed condition for book {book_id}
✅ Condition assessment completed successfully for book {book_id}
================================================================================
```

---

## 9. Troubleshooting

### Problem: "Permission Denied" bei Pub/Sub
```bash
# Grant Pub/Sub Publisher role to Cloud Run service account
gcloud projects add-iam-policy-binding bookscout-440210 \
  --member="serviceAccount:252725930721-compute@developer.gserviceaccount.com" \
  --role="roles/pubsub.publisher"
```

### Problem: Subscription kann nicht zu Cloud Run pushen
```bash
# Grant invoker role to Pub/Sub service account
gcloud run services add-iam-policy-binding condition-assessor \
  --region=europe-west1 \
  --member="serviceAccount:service-252725930721@gcp-sa-pubsub.iam.gserviceaccount.com" \
  --role="roles/run.invoker" \
  --project=bookscout-440210
```

### Problem: Alte Logs/Cache
```bash
# Force new revision deployment
gcloud run deploy ingestion-agent \
  --source=./agents/ingestion-agent \
  --region=europe-west1 \
  --no-traffic \
  --tag=test \
  --project=bookscout-440210

# Then promote to production
gcloud run services update-traffic ingestion-agent \
  --to-latest \
  --region=europe-west1 \
  --project=bookscout-440210
```

---

## 10. Schnelle Diagnose-Checkliste

- [ ] Pub/Sub Topic `condition-assessment-jobs` existiert?
- [ ] Pub/Sub Subscription `condition-assessment-subscription` existiert?
- [ ] Subscription push-endpoint ist `https://condition-assessor-252725930721.europe-west1.run.app`?
- [ ] Ingestion Agent wurde **nach** Code-Änderung deployed?
- [ ] Ingestion Agent Logs zeigen "Successfully published to Pub/Sub"?
- [ ] Condition Assessor Logs zeigen "New CloudEvent received"?
- [ ] Firestore Collection `users/{uid}/condition_assessments/{bookId}` hat Daten?
- [ ] Frontend zeigt Condition Assessment Ergebnisse?

**Falls alle ✅ → Problem gelöst!**
