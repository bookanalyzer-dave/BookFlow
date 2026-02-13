#!/bin/bash
set -e

# Configuration
PROJECT_ID=$(gcloud config get-value project)
REGION="europe-west1"
SERVICE_NAME="ingestion-agent"
TRIGGER_NAME="ingestion-agent-trigger"
OLD_TOPIC="trigger-ingestion"
NEW_TOPIC="ingestion-requests"

echo "==================================================="
echo "   UPDATING INGESTION AGENT TRIGGER CONFIGURATION  "
echo "==================================================="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Service: $SERVICE_NAME"
echo "Target Topic: $NEW_TOPIC"
echo "==================================================="

# 1. Check existing trigger
echo "🔍 Checking existing trigger '$TRIGGER_NAME'..."
if gcloud eventarc triggers describe $TRIGGER_NAME --location=$REGION > /dev/null 2>&1; then
    echo "⚠️  Trigger '$TRIGGER_NAME' exists."
    
    CURRENT_TOPIC=$(gcloud eventarc triggers describe $TRIGGER_NAME --location=$REGION --format="value(transport.pubsub.topic)")
    echo "   Current Topic: $CURRENT_TOPIC"

    if [[ "$CURRENT_TOPIC" == *"$NEW_TOPIC"* ]]; then
        echo "✅ Trigger is already pointing to the correct topic ($NEW_TOPIC). No action needed."
        exit 0
    else
        echo "❌ Trigger points to OLD topic. Deleting to recreate..."
        gcloud eventarc triggers delete $TRIGGER_NAME --location=$REGION --quiet
        echo "🗑️  Old trigger deleted."
    fi
else
    echo "ℹ️  Trigger '$TRIGGER_NAME' does not exist. Will create new one."
fi

# 2. Create new trigger
echo "🚀 Creating new trigger '$TRIGGER_NAME' for topic '$NEW_TOPIC'..."

# Get Project Number for Service Account construction
PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
SERVICE_ACCOUNT="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

gcloud eventarc triggers create $TRIGGER_NAME \
    --location=$REGION \
    --destination-run-service=$SERVICE_NAME \
    --destination-run-region=$REGION \
    --event-filters="type=google.cloud.pubsub.topic.v1.messagePublished" \
    --transport-topic="projects/$PROJECT_ID/topics/$NEW_TOPIC" \
    --service-account=$SERVICE_ACCOUNT

echo "==================================================="
echo "✅ SUCCESS: Trigger updated to listen on '$NEW_TOPIC'"
echo "==================================================="
