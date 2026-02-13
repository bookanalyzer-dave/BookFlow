# GCP Migrationsleitfaden: Projekt-Transfer

Dieses Dokument beschreibt den Prozess der Migration des BookFlow-Projekts von der aktuellen GCP-Projekt-ID (`project-52b2fab8-15a1-4b66-9f3`) auf ein neues Google Cloud Konto oder Projekt.

## Inhaltsverzeichnis
1. [Vorbereitung im Zielkonto](#1-vorbereitung-im-zielkonto)
2. [Infrastruktur-Migration](#2-infrastruktur-migration)
3. [Daten-Migration](#3-daten-migration)
4. [Deployment](#4-deployment)
5. [Validierung](#5-validierung)

---

## 1. Vorbereitung im Zielkonto

In diesem Schritt wird das Grundgerüst im neuen Google Cloud Konto erstellt.

### 1.1 Neues GCP-Projekt erstellen
1. Navigieren Sie zur [Google Cloud Console](https://console.cloud.google.com/).
2. Erstellen Sie ein neues Projekt. 
3. Notieren Sie sich die neue **Projekt-ID** (im Folgenden `NEUE_PROJEKT_ID` genannt).

### 1.2 Abrechnung verknüpfen
Stellen Sie sicher, dass ein aktives Rechnungskonto mit dem neuen Projekt verknüpft ist, da viele der genutzten Dienste (wie Cloud Run und Vertex AI) dies erfordern.

### 1.3 Erforderliche APIs aktivieren
Führen Sie den folgenden Befehl aus, um alle notwendigen APIs im neuen Projekt zu aktivieren:

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
    eventarc.googleapis.com \
    artifactregistry.googleapis.com \
    logging.googleapis.com \
    monitoring.googleapis.com \
    cloudtrace.googleapis.com \
    firebase.googleapis.com \
    firebasestorage.googleapis.com \
    firebasehosting.googleapis.com
```

### 1.4 Firebase Initialisierung
Da das Dashboard Firebase Hosting nutzt:
1. Gehen Sie zur [Firebase Console](https://console.firebase.google.com/).
2. Klicken Sie auf "Projekt hinzufügen" und wählen Sie das bestehende GCP-Projekt (`NEUE_PROJEKT_ID`) aus.
3. Aktivieren Sie Firestore im **Native Mode** in der gewünschten Region (empfohlen: `europe-west1`).

---

## 2. Infrastruktur-Migration

### 2.1 Service Accounts erstellen
Das Projekt nutzt dedizierte Service Accounts für die verschiedenen Agenten. Erstellen Sie den Haupt-Service-Account (z.B. `bookflow-sa`):

```bash
gcloud iam service-accounts create bookflow-sa \
    --display-name="BookFlow Main Service Account"
```

Weisen Sie dem Service Account die notwendigen Rollen zu:
```bash
for ROLE in \
    roles/datastore.user \
    roles/pubsub.publisher \
    roles/pubsub.subscriber \
    roles/storage.objectAdmin \
    roles/aiplatform.user \
    roles/run.invoker \
    roles/secretmanager.secretAccessor \
    roles/eventarc.eventReceiver; \
do \
    gcloud projects add-iam-policy-binding NEUE_PROJEKT_ID \
        --member="serviceAccount:bookflow-sa@NEUE_PROJEKT_ID.iam.gserviceaccount.com" \
        --role="$ROLE"; \
done
```

### 2.2 Cloud Storage Buckets
Erstellen Sie den zentralen Bucket für Buchbilder:

```bash
gsutil mb -p NEUE_PROJEKT_ID -l europe-west1 gs://NEUE_PROJEKT_ID-book-images
```

### 2.3 Pub/Sub Topics einrichten
Erstellen Sie alle erforderlichen Topics für die Kommunikation zwischen den Agenten:

```bash
for TOPIC in \
    trigger-ingestion \
    book-identified \
    delist-book-everywhere \
    sale-notification-received \
    trigger-condition-assessment; \
do \
    gcloud pubsub topics create $TOPIC; \
done
```

### 2.4 Secret Manager konfigurieren
Das System benötigt Zugriff auf die Gemini API. Erstellen Sie das Secret:

```bash
echo -n "IHR_GEMINI_API_KEY" | gcloud secrets create GEMINI_API_KEY \
    --replication-policy="automatic" \
    --data-file=-
```

Gewähren Sie dem Service Account Zugriff:
```bash
gcloud secrets add-iam-policy-binding GEMINI_API_KEY \
    --member="serviceAccount:bookflow-sa@NEUE_PROJEKT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### 2.5 Eventarc Trigger
Eventarc wird benötigt, um Cloud Run Services basierend auf Pub/Sub-Events oder Storage-Änderungen zu triggern.

1. Erteilen Sie dem Eventarc Service Agent die notwendige Rolle:
```bash
PROJECT_NUMBER=$(gcloud projects describe NEUE_PROJEKT_ID --format='value(projectNumber)')

gcloud projects add-iam-policy-binding NEUE_PROJEKT_ID \
    --member="serviceAccount:service-$PROJECT_NUMBER@gcp-sa-eventarc.iam.gserviceaccount.com" \
    --role="roles/iam.serviceAccountUser"
```

2. (Trigger werden während des Deployments in Abschnitt 4 erstellt).

---

## 3. Daten-Migration

### 3.1 Cloud Storage Inhalte übertragen
Verwenden Sie `gsutil rsync`, um die Bilder vom alten in den neuen Bucket zu kopieren:

```bash
# Stellen Sie sicher, dass Sie Zugriff auf beide Projekte haben
gsutil -m rsync -r \
    gs://project-52b2fab8-15a1-4b66-9f3-book-images \
    gs://NEUE_PROJEKT_ID-book-images
```

### 3.2 Firestore-Daten exportieren und importieren
1. **Export im alten Projekt:**
   Erstellen Sie einen temporären Bucket im alten Projekt für den Export.
   ```bash
   gsutil mb -p project-52b2fab8-15a1-4b66-9f3 gs://project-52b2fab8-15a1-4b66-9f3-firestore-export
   gcloud firestore export gs://project-52b2fab8-15a1-4b66-9f3-firestore-export --project=project-52b2fab8-15a1-4b66-9f3
   ```

2. **Übertragung zum neuen Bucket:**
   Kopieren Sie den Export in das neue Projekt.
   ```bash
   gsutil -m rsync -r \
       gs://project-52b2fab8-15a1-4b66-9f3-firestore-export \
       gs://NEUE_PROJEKT_ID-firestore-import
   ```

3. **Import im neuen Projekt:**
   Geben Sie dem Firestore Service Agent des neuen Projekts Lesezugriff auf den Import-Bucket:
   ```bash
   NEW_PROJECT_NUMBER=$(gcloud projects describe NEUE_PROJEKT_ID --format='value(projectNumber)')
   gsutil iam ch \
       serviceAccount:service-$NEW_PROJECT_NUMBER@gcp-firestore-api.iam.gserviceaccount.com:objectViewer \
       gs://NEUE_PROJEKT_ID-firestore-import
   
   gcloud firestore import gs://NEUE_PROJEKT_ID-firestore-import/[PFAD_ZUM_EXPORT] --project=NEUE_PROJEKT_ID
   ```

---

## 4. Deployment

In diesem Schritt wird der Code auf die neue Infrastruktur ausgerollt.

### 4.1 Quellcode anpassen
Suchen und ersetzen Sie alle Vorkommen der alten Projekt-ID (`project-52b2fab8-15a1-4b66-9f3`) durch die `NEUE_PROJEKT_ID` in folgenden Dateien:

- **Root:** `cloudbuild.yaml`, `cloudbuild.backend.yaml`, `cloudbuild.condition-assessor.yaml`, `ingestion-agent-cloudbuild.yaml`, `setup_gcp.sh`, `scripts/deploy_all.sh`.
- **Backend:** `dashboard/backend/.env`.
- **Frontend:** `dashboard/frontend/.env`, `dashboard/frontend/.env.production`.
- **Firebase:** `firebase.json` (falls dort IDs hinterlegt sind).

### 4.2 Umgebungsvariablen in Skripten prüfen
Stellen Sie sicher, dass in `setup_gcp.sh` und `scripts/deploy_all.sh` die Variable `GCP_PROJECT_ID` auf die `NEUE_PROJEKT_ID` gesetzt ist.

### 4.3 Deployment ausführen
Führen Sie das zentrale Deployment-Skript aus:

```bash
# Zuerst authentifizieren
gcloud auth login
gcloud config set project NEUE_PROJEKT_ID

# Ressourcen-Setup (erstellt evtl. fehlende Pub/Sub Topics etc.)
chmod +x setup_gcp.sh
./setup_gcp.sh

# Vollständiges Deployment
chmod +x scripts/deploy_all.sh
./scripts/deploy_all.sh
```

### 4.4 Firebase Hosting Deployment
Das Dashboard muss separat deployt werden:

```bash
cd dashboard/frontend
npm install
npm run build
firebase deploy --only hosting --project NEUE_PROJEKT_ID
```

---

## 5. Validierung

Verwenden Sie diese Checkliste, um sicherzustellen, dass die Migration erfolgreich war.

- [ ] **Firestore:** Sind alle Dokumente in den Collections `books`, `processing_tasks` etc. vorhanden?
- [ ] **Cloud Storage:** Sind die Bilder im Bucket `gs://NEUE_PROJEKT_ID-book-images` zugänglich?
- [ ] **Cloud Run:** Sind alle Services (`ingestion-agent`, `dashboard-backend`, `condition-assessor`) im Status "Ready"?
- [ ] **Eventarc:** Sind die Trigger vorhanden und mit den korrekten Cloud Run Services verknüpft?
- [ ] **Dashboard:** Ist das Dashboard über die Firebase Hosting URL erreichbar?
- [ ] **End-to-End Test:** Führen Sie einen Test-Upload eines Buchbildes über das Dashboard durch und prüfen Sie, ob der Prozess (OCR -> KI-Analyse -> Firestore-Eintrag) durchläuft.
- [ ] **Logging:** Prüfen Sie die Cloud Logging Console auf Fehler der Agenten.

