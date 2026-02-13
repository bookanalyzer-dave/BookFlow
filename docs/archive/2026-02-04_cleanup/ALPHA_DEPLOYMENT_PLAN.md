# Alpha Deployment Plan

**Status:** Infrastruktur bereit ✅
**GCP Project:** true-campus-475614-p4
**Region:** europe-west1

## Phase 1: Backend Deployment (Dashboard)

### 1.1 Dashboard Backend auf Cloud Run

**Ziel:** Dashboard Backend API auf Cloud Run deployen

**Vorbereitung:**
- [ ] [`dashboard/backend/Dockerfile`](dashboard/backend/Dockerfile:1) prüfen
- [x] Environment Variables aus [`.env`](dashboard/backend/.env:1) geprüft und für Deployment vorbereitet
- [ ] Service Account Permissions prüfen

**Deployment-Befehl:**
```bash
gcloud run deploy dashboard-backend \
  --source=./dashboard/backend \
  --region=europe-west1 \
  --platform=managed \
  --allow-unauthenticated
# Hinweis: Umgebungsvariablen sollten sicher in der Cloud Run Service-Konfiguration
# oder über Secret Manager gesetzt werden, nicht direkt aus der .env-Datei.
# Beispiel für eine Variable: --set-env-vars="GCP_PROJECT_ID=true-campus-475614-p4"
```

**Erwartetes Ergebnis:**
- Service URL: https://dashboard-backend-XXXXX-ew.a.run.app
- Status: ✅ RUNNING
- Health Check: /api/health returns 200

**Verifikation:**
```bash
curl https://YOUR_BACKEND_URL/api/health
```

## Phase 2: Frontend Deployment

### 2.1 Frontend Build

**Vorbereitung:**
- [ ] [`dashboard/frontend/package.json`](dashboard/frontend/package.json:1) prüfen
- [x] Firebase Config in [`firebaseConfig.js`](dashboard/frontend/src/firebaseConfig.js:1) auf Umgebungsvariablen umgestellt
- [x] `.env`-Datei für Frontend mit `VITE_BACKEND_API_URL` und Firebase-Keys erstellt

**Build-Befehl:**
```bash
cd dashboard/frontend
npm install
npm run build
```

### 2.2 Firebase Hosting Deploy

**Deployment-Befehl:**
```bash
npm run deploy
```

**Erwartetes Ergebnis:**
- Hosting URL: https://YOUR_PROJECT.web.app
- Status: ✅ DEPLOYED

## Phase 3: Agent Deployment

### 3.1 Ingestion Agent

**Deployment:**
```bash
gcloud run deploy ingestion-agent \
  --source=./agents/ingestion-agent \
  --region=europe-west1 \
  --platform=managed \
  --no-allow-unauthenticated \
  --set-env-vars="$(cat agents/ingestion-agent/.env.yaml | yq -r 'to_entries | .[] | .key + "=" + .value' | xargs | tr ' ' ',')"
```

**Pub/Sub Trigger:**
```bash
gcloud eventarc triggers create ingestion-agent-trigger \
  --destination-run-service=ingestion-agent \
  --destination-run-region=europe-west1 \
  --event-filters="type=google.cloud.pubsub.topic.v1.messagePublished" \
  --event-filters="serviceName=pubsub.googleapis.com"
```

### 3.2 Condition Assessor Agent

**Deployment:**
```bash
gcloud run deploy condition-assessor \
  --source=./agents/condition-assessor \
  --region=europe-west1 \
  --platform=managed \
  --no-allow-unauthenticated \
  --set-env-vars="$(cat agents/condition-assessor/.env.yaml | yq -r 'to_entries | .[] | .key + "=" + .value' | xargs | tr ' ' ',')"
```

**Firestore Trigger:**
```bash
gcloud eventarc triggers create condition-assessor-trigger \
  --destination-run-service=condition-assessor \
  --destination-run-region=europe-west1 \
  --event-filters="type=google.cloud.firestore.document.v1.created" \
  --event-filters-path-pattern="database=(default)/documents/users/{userId}/condition_assessment_requests/{bookId}" \
  --service-account="YOUR_SERVICE_ACCOUNT_EMAIL"
```
**Wichtiger Hinweis:** Ersetze `YOUR_SERVICE_ACCOUNT_EMAIL` durch die E-Mail-Adresse des Dienstkontos, das die Berechtigung hat, auf Firestore zuzugreifen und Cloud Run Services aufzurufen.

### 3.3 Weitere Agents (Optional für Alpha)

Die folgenden Agents sind optional und können später deployed werden:
- Scout Agent (Marktforschung)
- Strategist Agent (Pricing)
- Ambassador Agent (Marketplace Listing)
- Sentinel Agent & Webhook (Sales Monitoring)

## Phase 4: Verifikation

### 4.1 Health Checks

**Dashboard Backend:**
```bash
curl https://dashboard-backend-URL/api/health
```

**Agents:**
```bash
# Prüfe ob Services laufen
gcloud run services list --region=europe-west1
```

### 4.2 End-to-End Test

**Test-Workflow:**
1. Dashboard öffnen
2. Login mit Test-User
3. Bild hochladen
4. Prüfen ob Ingestion Agent triggered wird
5. Prüfen ob Condition Assessor reagiert
6. Ergebnis im Dashboard prüfen

### 4.3 Logs prüfen

```bash
# Backend Logs
gcloud logs tail dashboard-backend --region=europe-west1

# Agent Logs
gcloud logs tail ingestion-agent --region=europe-west1
```

## Rollback-Plan

Falls kritische Fehler auftreten:

**Backend Rollback:**
```bash
gcloud run services update dashboard-backend \
  --region=europe-west1 \
  --image=PREVIOUS_IMAGE_URL
```

**Frontend Rollback:**
```bash
firebase hosting:rollback
```

## Erfolgs-Kriterien

- [ ] Dashboard Backend erreichbar und Health Check OK
- [ ] Frontend deployed und erreichbar
- [ ] Login/Registrierung funktioniert
- [ ] Mindestens Ingestion Agent deployed
- [ ] Mindestens Condition Assessor deployed
- [ ] Test-Upload läuft erfolgreich durch

## Bekannte Einschränkungen (Alpha)

- Nur 2 Agents aktiv (Ingestion, Condition Assessment)
- Kein automatisches Marketplace Listing
- Manuelles Pricing erforderlich
- Eingeschränktes Monitoring

## Nächste Schritte nach Alpha

- Weitere Agents deployen
- Automated Monitoring aktivieren
- Load Testing durchführen
- Beta Launch vorbereiten