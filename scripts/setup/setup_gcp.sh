#!/bin/bash

# ==============================================================================
# GCP-Setup-Skript
#
# Dieses Skript richtet die notwendigen Google Cloud Platform-Ressourcen für
# das Projekt ein. Passen Sie die Konfigurationsvariablen unten an, bevor
# Sie das Skript ausführen.
#
# Verwendung:
# 1. Stellen Sie sicher, dass Sie mit dem richtigen GCP-Konto authentifiziert sind:
#    gcloud auth login
#    gcloud config set project [IHRE_PROJEKT_ID]
# 2. Führen Sie dieses Skript aus dem Stammverzeichnis des Projekts aus:
#    ./setup_gcp.sh
# ==============================================================================

# --- Konfigurationsvariablen ---
# Passen Sie diese Variablen für Ihr GCP-Projekt an.
GCP_PROJECT_ID="project-52b2fab8-15a1-4b66-9f3"
GCP_REGION="europe-west1" # Beispielregion, ändern Sie sie bei Bedarf

# --- Skript-Logik ---
# Beenden Sie das Skript sofort, wenn ein Befehl fehlschlägt
set -e

echo "GCP-Setup wird gestartet für Projekt: $GCP_PROJECT_ID"

# 1. Erforderliche APIs aktivieren
echo "Aktiviere erforderliche GCP-APIs..."
gcloud services enable run.googleapis.com \
    pubsub.googleapis.com \
    storage.googleapis.com \
    firestore.googleapis.com \
    vision.googleapis.com \
    aiplatform.googleapis.com \
    secretmanager.googleapis.com \
    cloudbuild.googleapis.com

echo "APIs erfolgreich aktiviert."

# 2. Cloud Storage Bucket für Buchbilder erstellen
# Der Bucket-Name muss global eindeutig sein. Wir verwenden die Projekt-ID, um
# die Eindeutigkeit zu gewährleisten.
BUCKET_NAME="${GCP_PROJECT_ID}-book-images"
echo "Erstelle Cloud Storage Bucket: gs://${BUCKET_NAME}"
gsutil mb -p $GCP_PROJECT_ID -l $GCP_REGION gs://${BUCKET_NAME}
echo "Bucket erfolgreich erstellt."

# 3. Pub/Sub-Themen erstellen
echo "Erstelle Pub/Sub-Themen..."
gcloud pubsub topics create trigger-ingestion
gcloud pubsub topics create book-identified
gcloud pubsub topics create delist-book-everywhere
gcloud pubsub topics create sale-notification-received
echo "Pub/Sub-Themen erfolgreich erstellt."

# 4. Firestore-Datenbank erstellen
echo "Erstelle Firestore-Datenbank im Native-Modus..."
gcloud firestore databases create --location=$GCP_REGION --type=firestore-native
echo "Firestore-Datenbank erfolgreich erstellt."

echo "==============================================="
echo "GCP-Ressourcen-Setup erfolgreich abgeschlossen!"
echo "==============================================="