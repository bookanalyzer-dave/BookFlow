#!/usr/bin/env python3
"""Helper script to create the deployment bash script."""

import os

script_content = r'''#!/bin/bash

# Complete Deployment Script for BookFlow System
# Date: 2025-12-21
# Project: project-52b2fab8-15a1-4b66-9f3

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR:${NC} $1"
}

warning() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING:${NC} $1"
}

# Project configuration
PROJECT_ID="project-52b2fab8-15a1-4b66-9f3"
PUBSUB_TOPIC="trigger-condition-assessment"
INGESTION_TOPIC="trigger-ingestion"
DLQ_TOPIC_INGESTION="trigger-ingestion-dlq"
DLQ_TOPIC_CONDITION="trigger-condition-assessment-dlq"
DEPLOYMENT_LOG="DEPLOYMENT_LOG_$(date +'%Y-%m-%d_%H%M%S').md"

# Initialize deployment log
init_log() {
    cat > "$DEPLOYMENT_LOG" << EOF
# Deployment Log - $(date +'%Y-%m-%d %H:%M:%S')

## Project Information
- **Project ID:** $PROJECT_ID
- **Deployment Date:** $(date +'%Y-%m-%d %H:%M:%S')
- **Executed By:** $(whoami)

## Deployment Steps

EOF
}

# Append to log
append_log() {
    echo -e "$1" >> "$DEPLOYMENT_LOG"
}

# Step 1: Create Pub/Sub Topics
deploy_pubsub() {
    log "Step 1: Creating Pub/Sub Topics..."
    append_log "### Step 1: Pub/Sub Topic Creation\n"
    
    # Topic 1: Condition Assessment
    append_log "**Topic 1:** $PUBSUB_TOPIC\n"
    if gcloud pubsub topics describe $PUBSUB_TOPIC --project=$PROJECT_ID &> /dev/null; then
        warning "Pub/Sub topic '$PUBSUB_TOPIC' already exists. Skipping creation."
    else
        if gcloud pubsub topics create $PUBSUB_TOPIC --project=$PROJECT_ID; then
            log "✓ Pub/Sub topic '$PUBSUB_TOPIC' created successfully"
        else
            error "Failed to create Pub/Sub topic '$PUBSUB_TOPIC'"
            return 1
        fi
    fi

    # Topic 2: Ingestion
    append_log "**Topic 2:** $INGESTION_TOPIC\n"
    if gcloud pubsub topics describe $INGESTION_TOPIC --project=$PROJECT_ID &> /dev/null; then
        warning "Pub/Sub topic '$INGESTION_TOPIC' already exists. Skipping creation."
    else
        if gcloud pubsub topics create $INGESTION_TOPIC --project=$PROJECT_ID; then
            log "✓ Pub/Sub topic '$INGESTION_TOPIC' created successfully"
        else
            error "Failed to create Pub/Sub topic '$INGESTION_TOPIC'"
            return 1
        fi
    fi
    
    append_log "**Status:** ✅ Success (Topics verified/created)\n"
    append_log "**Timestamp:** $(date +'%Y-%m-%d %H:%M:%S')\n\n"
}

# Step 2: Deploy Backend
deploy_backend() {
    log "Step 2: Deploying Backend..."
    append_log "### Step 2: Backend Deployment\n"
    append_log "**Command:** \`gcloud builds submit --config ops/cloudbuild/cloudbuild.backend.yaml\`\n"
    
    if gcloud builds submit --config ops/cloudbuild/cloudbuild.backend.yaml --project=$PROJECT_ID; then
        log "✓ Backend deployed successfully"
        append_log "**Status:** ✅ Success\n"
        append_log "**Timestamp:** $(date +'%Y-%m-%d %H:%M:%S')\n\n"
    else
        error "Failed to deploy backend"
        append_log "**Status:** ❌ Failed\n"
        append_log "**Error:** Backend deployment failed\n"
        append_log "**Timestamp:** $(date +'%Y-%m-%d %H:%M:%S')\n\n"
        return 1
    fi
}

# Step 3: Deploy Condition Assessor
deploy_condition_assessor() {
    log "Step 3: Deploying Condition Assessor..."
    append_log "### Step 3: Condition Assessor Deployment\n"
    append_log "**Command:** \`gcloud builds submit --config ops/cloudbuild/cloudbuild.condition-assessor.yaml\`\n"
    
    if gcloud builds submit --config ops/cloudbuild/cloudbuild.condition-assessor.yaml --project=$PROJECT_ID; then
        log "✓ Condition Assessor deployed successfully"
        append_log "**Status:** ✅ Success\n"
        append_log "**Timestamp:** $(date +'%Y-%m-%d %H:%M:%S')\n\n"
    else
        error "Failed to deploy Condition Assessor"
        append_log "**Status:** ❌ Failed\n"
        append_log "**Error:** Condition Assessor deployment failed\n"
        append_log "**Timestamp:** $(date +'%Y-%m-%d %H:%M:%S')\n\n"
        return 1
    fi
}

# Step 4: Deploy Ingestion Agent
deploy_ingestion_agent() {
    log "Step 4: Deploying Ingestion Agent..."
    append_log "### Step 4: Ingestion Agent Deployment\n"
    append_log "**Command:** \`gcloud builds submit --config ops/cloudbuild/cloudbuild.ingestion-agent.yaml\`\n"
    
    if gcloud builds submit --config ops/cloudbuild/cloudbuild.ingestion-agent.yaml --project=$PROJECT_ID; then
        log "✓ Ingestion Agent deployed successfully"
        append_log "**Status:** ✅ Success\n"
        append_log "**Timestamp:** $(date +'%Y-%m-%d %H:%M:%S')\n\n"
    else
        error "Failed to deploy Ingestion Agent"
        append_log "**Status:** ❌ Failed\n"
        append_log "**Error:** Ingestion Agent deployment failed\n"
        append_log "**Timestamp:** $(date +'%Y-%m-%d %H:%M:%S')\n\n"
        return 1
    fi
}

# Step 5: Deploy Frontend
deploy_frontend() {
    log "Step 5: Deploying Frontend..."
    append_log "### Step 5: Frontend Deployment\n"
    append_log "**Command:** \`firebase deploy --only hosting\`\n"
    
    if firebase deploy --only hosting --project=$PROJECT_ID; then
        log "✓ Frontend deployed successfully"
        append_log "**Status:** ✅ Success\n"
        append_log "**Timestamp:** $(date +'%Y-%m-%d %H:%M:%S')\n\n"
    else
        error "Failed to deploy Frontend"
        append_log "**Status:** ❌ Failed\n"
        append_log "**Error:** Frontend deployment failed\n"
        append_log "**Timestamp:** $(date +'%Y-%m-%d %H:%M:%S')\n\n"
        return 1
    fi
}

# Setup DLQ Infrastructure
setup_dlq_infrastructure() {
    log "Setting up DLQ infrastructure..."
    append_log "### DLQ Infrastructure Setup\n"

    # Get Project Number
    PROJECT_NUMBER=$(gcloud projects describe $PROJECT_ID --format="value(projectNumber)")
    PUBSUB_SERVICE_ACCOUNT="service-${PROJECT_NUMBER}@gcp-sa-pubsub.iam.gserviceaccount.com"
    log "Project Number: $PROJECT_NUMBER"
    log "Pub/Sub Service Account: $PUBSUB_SERVICE_ACCOUNT"

    # Create DLQ Topics
    for topic in "$DLQ_TOPIC_INGESTION" "$DLQ_TOPIC_CONDITION"; do
        if gcloud pubsub topics describe $topic --project=$PROJECT_ID &> /dev/null; then
            warning "DLQ topic '$topic' already exists."
        else
            if gcloud pubsub topics create $topic --project=$PROJECT_ID; then
                log "✓ DLQ topic '$topic' created"
            else
                error "Failed to create DLQ topic '$topic'"
                return 1
            fi
        fi

        # Grant Publisher role to Pub/Sub Service Account
        log "Granting Publisher role to Pub/Sub Service Account on '$topic'..."
        if gcloud pubsub topics add-iam-policy-binding $topic \
            --project=$PROJECT_ID \
            --member="serviceAccount:$PUBSUB_SERVICE_ACCOUNT" \
            --role="roles/pubsub.publisher" &> /dev/null; then
            log "✓ IAM role granted on '$topic'"
        else
            error "Failed to grant IAM role on '$topic'"
            return 1
        fi
    done
    
    append_log "**Status:** ✅ Success (DLQ Topics configured)\n"
    append_log "**Timestamp:** $(date +'%Y-%m-%d %H:%M:%S')\n\n"
}

# Configure DLQ for a specific trigger
configure_dlq_for_trigger() {
    local TRIGGER_NAME=$1
    local DLQ_TOPIC=$2
    local REGION="europe-west1"

    log "Configuring DLQ for trigger '$TRIGGER_NAME'..."
    append_log "Configuring DLQ for $TRIGGER_NAME...\n"
    
    # Find the subscription ID of the trigger
    SUBSCRIPTION_FULL_PATH=$(gcloud eventarc triggers describe $TRIGGER_NAME \
        --location=$REGION \
        --project=$PROJECT_ID \
        --format="value(transport.pubsub.subscription)")
        
    if [ -z "$SUBSCRIPTION_FULL_PATH" ]; then
        error "Could not find subscription for trigger '$TRIGGER_NAME'"
        return 1
    fi
    
    log "Found subscription: $SUBSCRIPTION_FULL_PATH"
    
    # Update subscription
    if gcloud pubsub subscriptions update "$SUBSCRIPTION_FULL_PATH" \
        --project=$PROJECT_ID \
        --dead-letter-topic=$DLQ_TOPIC \
        --max-delivery-attempts=2; then
        log "✓ DLQ configured for trigger '$TRIGGER_NAME'"
        append_log "✓ DLQ configured for $TRIGGER_NAME\n"
    else
        error "Failed to configure DLQ for trigger '$TRIGGER_NAME'"
        return 1
    fi
}

# Main deployment function
main() {
    log "Starting complete deployment process..."
    log "Project: $PROJECT_ID"
    echo ""
    
    # Initialize log file
    init_log
    
    # Track failures
    FAILED_STEPS=()
    
    # Step 1: Pub/Sub
    if ! deploy_pubsub; then
        FAILED_STEPS+=("Pub/Sub Topic")
    fi
    
    # Setup DLQ Infrastructure
    if ! setup_dlq_infrastructure; then
        FAILED_STEPS+=("DLQ Infrastructure")
    fi

    # Step 2: Backend
    if ! deploy_backend; then
        FAILED_STEPS+=("Backend")
    fi
    
    # Step 3: Condition Assessor
    if ! deploy_condition_assessor; then
        FAILED_STEPS+=("Condition Assessor")
    else
        # Configure DLQ for Condition Assessor
        if ! configure_dlq_for_trigger "condition-assessor-trigger" "$DLQ_TOPIC_CONDITION"; then
             FAILED_STEPS+=("Condition Assessor DLQ")
        fi
    fi
    
    # Step 4: Ingestion Agent
    if ! deploy_ingestion_agent; then
        FAILED_STEPS+=("Ingestion Agent")
    else
        # Configure DLQ for Ingestion Agent
        if ! configure_dlq_for_trigger "ingestion-agent-trigger" "$DLQ_TOPIC_INGESTION"; then
             FAILED_STEPS+=("Ingestion Agent DLQ")
        fi
    fi
    
    # Step 5: Frontend
    if ! deploy_frontend; then
        FAILED_STEPS+=("Frontend")
    fi
    
    # Final summary
    echo ""
    log "Deployment process completed!"
    
    if [ ${#FAILED_STEPS[@]} -eq 0 ]; then
        log "✓ All steps completed successfully!"
        append_log "## Deployment Summary\n\n"
        append_log "**Overall Status:** ✅ Success\n"
        append_log "**All 5 steps completed successfully**\n\n"
        append_log "## Deployed Components\n\n"
        append_log "1. ✅ Pub/Sub Topics: \`$PUBSUB_TOPIC\`, \`$INGESTION_TOPIC\`\n"
        append_log "2. ✅ Backend Service\n"
        append_log "3. ✅ Condition Assessor\n"
        append_log "4. ✅ Ingestion Agent\n"
        append_log "5. ✅ Frontend (Firebase Hosting)\n"
    else
        error "Some steps failed:"
        append_log "## Deployment Summary\n\n"
        append_log "**Overall Status:** ❌ Partial Failure\n\n"
        append_log "### Failed Steps:\n\n"
        for step in "${FAILED_STEPS[@]}"; do
            error "  - $step"
            append_log "- ❌ $step\n"
        done
        append_log "\n### Troubleshooting\n\n"
        append_log "Please check the error messages above and review:\n"
        append_log "- Cloud Build logs: https://console.cloud.google.com/cloud-build/builds?project=$PROJECT_ID\n"
        append_log "- Cloud Run services: https://console.cloud.google.com/run?project=$PROJECT_ID\n"
        append_log "- Firebase console: https://console.firebase.google.com/project/$PROJECT_ID\n"
    fi
    
    log "Deployment log saved to: $DEPLOYMENT_LOG"
    append_log "\n---\n*Generated at $(date +'%Y-%m-%d %H:%M:%S')*\n"
}

# Run main function
main
'''

# Ensure scripts directory exists
import shutil
if os.path.exists('scripts') and not os.path.isdir('scripts'):
    os.remove('scripts')
os.makedirs('scripts', exist_ok=True)

# Write the bash script with Unix line endings and UTF-8 encoding
with open('scripts/deploy_all.sh', 'w', newline='\n', encoding='utf-8') as f:
    f.write(script_content)

print("[OK] Deployment script created: scripts/deploy_all.sh")
print("  To use: bash scripts/deploy_all.sh")

