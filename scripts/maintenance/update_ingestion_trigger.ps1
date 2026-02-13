$ErrorActionPreference = "Stop"

# Configuration
$PROJECT_ID = gcloud config get-value project
$REGION = "europe-west1"
$SERVICE_NAME = "ingestion-agent"
$TRIGGER_NAME = "ingestion-agent-trigger"
$NEW_TOPIC = "ingestion-requests"

Write-Host "==================================================="
Write-Host "   UPDATING INGESTION AGENT TRIGGER (PowerShell)   "
Write-Host "==================================================="
Write-Host "Project: $PROJECT_ID"
Write-Host "Region: $REGION"
Write-Host "Service: $SERVICE_NAME"
Write-Host "Target Topic: $NEW_TOPIC"
Write-Host "==================================================="

# 1. Check existing trigger
Write-Host "Checking existing trigger '$TRIGGER_NAME'..."
$TRIGGER_EXISTS = $false
try {
    gcloud eventarc triggers describe $TRIGGER_NAME --location=$REGION 2>$null
    $TRIGGER_EXISTS = $true
} catch {
    $TRIGGER_EXISTS = $false
}

if ($TRIGGER_EXISTS) {
    Write-Host "Trigger '$TRIGGER_NAME' exists."
    
    # Get current topic details (needs parsing as gcloud output is text/json)
    $CURRENT_TOPIC = gcloud eventarc triggers describe $TRIGGER_NAME --location=$REGION --format="value(transport.pubsub.topic)"
    Write-Host "Current Topic: $CURRENT_TOPIC"

    if ($CURRENT_TOPIC -match $NEW_TOPIC) {
        Write-Host "Trigger is already pointing to the correct topic ($NEW_TOPIC). No action needed."
        exit 0
    } else {
        Write-Host "Trigger points to OLD topic. Deleting to recreate..."
        gcloud eventarc triggers delete $TRIGGER_NAME --location=$REGION --quiet
        Write-Host "Old trigger deleted."
    }
} else {
    Write-Host "Trigger '$TRIGGER_NAME' does not exist. Will create new one."
}

# 2. Create new trigger
Write-Host "Creating new trigger '$TRIGGER_NAME' for topic '$NEW_TOPIC'..."

# Get Project Number
$PROJECT_NUMBER = gcloud projects describe $PROJECT_ID --format="value(projectNumber)"
$SERVICE_ACCOUNT = "$PROJECT_NUMBER-compute@developer.gserviceaccount.com"

gcloud eventarc triggers create $TRIGGER_NAME `
    --location=$REGION `
    --destination-run-service=$SERVICE_NAME `
    --destination-run-region=$REGION `
    --event-filters="type=google.cloud.pubsub.topic.v1.messagePublished" `
    --transport-topic="projects/$PROJECT_ID/topics/$NEW_TOPIC" `
    --service-account=$SERVICE_ACCOUNT

Write-Host "==================================================="
Write-Host "SUCCESS: Trigger updated to listen on '$NEW_TOPIC'"
Write-Host "==================================================="
