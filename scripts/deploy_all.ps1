# Deployment Script for BookFlow System (PowerShell)
# Project: BookFlow
# Date: 2026-02-04

$ErrorActionPreference = "Stop"

# Project configuration
$PROJECT_ID = gcloud config get-value project
if (-not $PROJECT_ID -or $PROJECT_ID -eq "(unset)") {
    Write-Host "ERROR: No Google Cloud project set. Please run 'gcloud config set project [PROJECT_ID]'" -ForegroundColor Red
    exit 1
}

# Topics
$PUBSUB_TOPIC = "trigger-condition-assessment"
$INGESTION_TOPIC = "trigger-ingestion"
$CONDITION_COMPLETED_TOPIC = "condition-assessment-completed"
$STRATEGIST_COMPLETED_TOPIC = "strategist-completed"

# DLQ Topics
$DLQ_TOPIC_INGESTION = "trigger-ingestion-dlq"
$DLQ_TOPIC_CONDITION = "trigger-condition-assessment-dlq"

$DEPLOYMENT_LOG = "DEPLOYMENT_LOG_$(Get-Date -Format 'yyyy-MM-dd_HHmmss').md"

function Log-Message {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] $Message" -ForegroundColor Green
}

function Log-Error {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Write-Host "[$timestamp] ERROR: $Message" -ForegroundColor Red
}

function Append-Log {
    param([string]$Content)
    Add-Content -Path $DEPLOYMENT_LOG -Value $Content
}

# Initialize Log
"#" + " Deployment Log - $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Out-File -FilePath $DEPLOYMENT_LOG -Encoding utf8
"## Project Information" | Append-Log
"- **Project ID:** $PROJECT_ID" | Append-Log
"- **Deployment Date:** $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" | Append-Log
"" | Append-Log
"## Deployment Steps" | Append-Log
"" | Append-Log

try {
    # Step 1: Pub/Sub
    Log-Message "Step 1: Creating Pub/Sub Topics..."
    "### Step 1: Pub/Sub Topic Creation" | Append-Log
    
    $topics = @($PUBSUB_TOPIC, $INGESTION_TOPIC, $CONDITION_COMPLETED_TOPIC, $STRATEGIST_COMPLETED_TOPIC)
    foreach ($topic in $topics) {
        $topicFullName = "projects/$PROJECT_ID/topics/$topic"
        $topicList = gcloud pubsub topics list --filter="name:$topicFullName" --project=$PROJECT_ID --format="value(name)"
        
        if ($topicList) {
            Log-Message "Pub/Sub topic '$topic' already exists. Skipped."
            "- Topic '$topic': ⚠️ Already exists (skipped)" | Append-Log
        } else {
            gcloud pubsub topics create $topic --project=$PROJECT_ID
            Log-Message "Pub/Sub topic '$topic' created successfully."
            "- Topic '$topic': ✅ Success" | Append-Log
        }
    }

    # DLQ Topics
    $dlqTopics = @($DLQ_TOPIC_INGESTION, $DLQ_TOPIC_CONDITION)
    foreach ($dlq in $dlqTopics) {
        $dlqFullName = "projects/$PROJECT_ID/topics/$dlq"
        $dlqList = gcloud pubsub topics list --filter="name:$dlqFullName" --project=$PROJECT_ID --format="value(name)"
        
        if ($dlqList) {
            Log-Message "DLQ Topic '$dlq' already exists. Skipped."
            "- DLQ '$dlq': ⚠️ Already exists" | Append-Log
        } else {
            gcloud pubsub topics create $dlq --project=$PROJECT_ID
            Log-Message "DLQ Topic '$dlq' created successfully."
            "- DLQ '$dlq': ✅ Success" | Append-Log
        }
    }

    # IAM Permissions for DLQ
    Log-Message "Setting IAM permissions for DLQs..."
    $PROJECT_NUMBER = (gcloud projects describe $PROJECT_ID --format="value(projectNumber)").Trim()
    $PUBSUB_SA = "service-$PROJECT_NUMBER@gcp-sa-pubsub.iam.gserviceaccount.com"
    
    foreach ($dlq in $dlqTopics) {
        gcloud pubsub topics add-iam-policy-binding $dlq --project=$PROJECT_ID --member="serviceAccount:$PUBSUB_SA" --role="roles/pubsub.publisher"
        Log-Message "Added publisher role to $PUBSUB_SA for $dlq"
    }

    "" | Append-Log

    # Generic function for Cloud Build components
    function Deploy-Component {
        param($Name, $Config)
        Log-Message "Deploying $Name..."
        "### $Name Deployment" | Append-Log
        gcloud builds submit --config $Config --project=$PROJECT_ID
        "**Status:** ✅ Success" | Append-Log
        "" | Append-Log
    }

    # Deployment steps
    Deploy-Component "Backend" "ops/cloudbuild/cloudbuild.backend.yaml"
    Deploy-Component "Ingestion Agent" "ops/cloudbuild/cloudbuild.ingestion-agent.yaml"
    Deploy-Component "Condition Assessor" "ops/cloudbuild/cloudbuild.condition-assessor.yaml"
    Deploy-Component "Strategist Agent" "ops/cloudbuild/cloudbuild.strategist-agent.yaml"
    Deploy-Component "Price Research Agent" "ops/cloudbuild/cloudbuild.price-research.yaml"
    # Ambassador Agent excluded per user request (legacy code, missing credentials)
    # Deploy-Component "Ambassador Agent" "ops/cloudbuild/cloudbuild.ambassador-agent.yaml"

    # Step: Frontend
    Log-Message "Deploying Frontend..."
    "### Frontend Deployment" | Append-Log
    firebase deploy --only hosting --project=$PROJECT_ID
    "**Status:** ✅ Success" | Append-Log
    "" | Append-Log

    # Step: Configure Dead Letter Queues
    Log-Message "Configuring Dead Letter Queues..."
    "### DLQ Configuration" | Append-Log

    # 1. Ingestion Agent DLQ
    try {
        $ingestionSub = gcloud eventarc triggers describe ingestion-agent-trigger --location=europe-west1 --project=$PROJECT_ID --format="value(transport.pubsub.subscription)" 2>$null
        if ($LASTEXITCODE -eq 0 -and $ingestionSub) {
            gcloud pubsub subscriptions update $ingestionSub --dead-letter-topic=$DLQ_TOPIC_INGESTION --max-delivery-attempts=5 --project=$PROJECT_ID
            Log-Message "Updated Ingestion Agent subscription with DLQ."
            "- Ingestion Agent DLQ: ✅ Configured" | Append-Log
        } else {
            Log-Message "Trigger 'ingestion-agent-trigger' not found. Skipping DLQ config for this trigger."
            "- Ingestion Agent DLQ: ⚠️ Trigger not found (skipped)" | Append-Log
        }
    } catch {
        Log-Message "Error checking 'ingestion-agent-trigger': $_"
    }

    # 2. Condition Assessor DLQ
    try {
        $conditionSub = gcloud eventarc triggers describe condition-assessor-trigger --location=europe-west1 --project=$PROJECT_ID --format="value(transport.pubsub.subscription)" 2>$null
        if ($LASTEXITCODE -eq 0 -and $conditionSub) {
            gcloud pubsub subscriptions update $conditionSub --dead-letter-topic=$DLQ_TOPIC_CONDITION --max-delivery-attempts=5 --project=$PROJECT_ID
            Log-Message "Updated Condition Assessor subscription with DLQ."
            "- Condition Assessor DLQ: ✅ Configured" | Append-Log
        } else {
             Log-Message "Trigger 'condition-assessor-trigger' not found. Skipping DLQ config for this trigger."
             "- Condition Assessor DLQ: ⚠️ Trigger not found (skipped)" | Append-Log
        }
    } catch {
         Log-Message "Error checking 'condition-assessor-trigger': $_"
    }
    "" | Append-Log

    Log-Message "Deployment process completed successfully!"
    Log-Message "Log saved to $DEPLOYMENT_LOG"

} catch {
    Log-Error "Deployment failed: $_"
    "**Status:** ❌ Failed" | Append-Log
    "**Error:** $_" | Append-Log
    exit 1
}
