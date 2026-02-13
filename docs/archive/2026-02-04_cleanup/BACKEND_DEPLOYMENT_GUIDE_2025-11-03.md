# Backend Deployment Guide

Die Bereitstellung des Backends ist ein zweistufiger Prozess. Zuerst wird das Docker-Image mit Cloud Build erstellt und in die Google Container Registry (GCR) hochgeladen. Anschließend wird dieses Image auf Cloud Run bereitgestellt.

## Schritt 1: Docker-Image erstellen und hochladen

Dieser Schritt wird durch die dedizierte Build-Konfigurationsdatei `cloudbuild.backend.yaml` gesteuert. Führen Sie den folgenden Befehl vom Stammverzeichnis des Projekts aus, um den Build-Prozess zu starten:

```bash
gcloud builds submit --config cloudbuild.backend.yaml .
```

## Schritt 2: Image auf Cloud Run bereitstellen

Nachdem der Build erfolgreich abgeschlossen wurde, stellen Sie das neu erstellte Image auf Ihrem Cloud Run-Dienst bereit.

```bash
gcloud run deploy dashboard-backend --image gcr.io/true-campus-475614-p4/dashboard-backend:latest --region europe-west1 --allow-unauthenticated
```

---

## Kritische Dateien für den Build

Der folgende Satz von Dateien ist für einen erfolgreichen Build unerlässlich:

- `cloudbuild.backend.yaml`
- `dashboard/backend/Dockerfile`
- `dashboard/backend/main.py`
- `dashboard/backend/requirements.txt`

## Benötigte Umgebungsvariablen für den Cloud Run Service

Stellen Sie sicher, dass die folgenden Umgebungsvariablen in Ihrem Cloud Run-Dienst konfiguriert sind:

- `GOOGLE_CLOUD_PROJECT`
- `FIREBASE_API_KEY`
- `FIREBASE_AUTH_DOMAIN`
- `FIREBASE_PROJECT_ID`
- `FIREBASE_STORAGE_BUCKET`
- `FIREBASE_MESSAGING_SENDER_ID`
- `FIREBASE_APP_ID`
- `FIREBASE_MEASUREMENT_ID`