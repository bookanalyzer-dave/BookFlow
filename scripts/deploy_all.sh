#!/bin/bash

# Complete Deployment Script for BookFlow System
# Date: 2026-02-04
# Project: BookFlow

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
PROJECT_ID=$(gcloud config get-value project)
if [ -z "$PROJECT_ID" ] || [ "$PROJECT_ID" == "(unset)" ]; then
    error "No Google Cloud project set. Please run 'gcloud config set project [PROJECT_ID]'"
    exit 1
fi

# Topics
PUBSUB_TOPIC="trigger-condition-assessment"
INGESTION_TOPIC="trigger-ingestion"
CONDITION_COMPLETED_TOPIC="condition-assessment-completed"
STRATEGIST_COMPLETED_TOPIC="strategist-completed"

# DLQ Topics
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
    
    local topics=("$PUBSUB_TOPIC" "$INGESTION_TOPIC" "$CONDITION_COMPLETED_TOPIC" "$STRATEGIST_COMPLETED_TOPIC")
    
    for topic in "${topics[@]}"; do
        append_log "**Topic:** $topic\n"
        if gcloud pubsub topics describe $topic --project=$PROJECT_ID &> /dev/null; then
            warning "Pub/Sub topic '$topic' already exists. Skipping creation."
        else
            if gcloud pubsub topics create $topic --project=$PROJECT_ID; then
                log "✓ Pub/Sub topic '$topic' created successfully"
            else
                error "Failed to create Pub/Sub topic '$topic'"
                return 1
            fi
        fi
    done
    
    append_log "**Status:** ✅ Success (Topics verified/created)\n"
    append_log "**Timestamp:** $(date +'%Y-%m-%d %H:%M:%S')\n\n"
}

# Generic Build/Deploy function
deploy_component() {
    local NAME=$1
    local CONFIG=$2
    local STEP_NUM=$3

    log "Step $STEP_NUM: Deploying $NAME..."
    append_log "### Step $STEP_NUM: $NAME Deployment\n"
    append_log "**Command:** \`gcloud builds submit --config $CONFIG\`\n"
    
    if gcloud builds submit --config $CONFIG --project=$PROJECT_ID; then
        log "✓ $NAME deployed successfully"
        append_log "**Status:** ✅ Success\n"
        append_log "**Timestamp:** $(date +'%Y-%m-%d %H:%M:%S')\n\n"
        return 0
    else
        error "Failed to deploy $NAME"
        append_log "**Status:** ❌ Failed\n"
        append_log "**Error:** $NAME deployment failed\n"
        append_log "**Timestamp:** $(date +'%Y-%m-%d %H:%M:%S')\n\n"
        return 1
    fi
}

# Step 5: Deploy Frontend
deploy_frontend() {
    log "Deploying Frontend..."
    append_log "### Frontend Deployment\n"
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
    if ! deploy_pubsub; then FAILED_STEPS+=("Pub/Sub Topics"); fi
    
    # Setup DLQ Infrastructure
    if ! setup_dlq_infrastructure; then FAILED_STEPS+=("DLQ Infrastructure"); fi

    # Deploy Components
    deploy_component "Backend" "ops/cloudbuild/cloudbuild.backend.yaml" "2" || FAILED_STEPS+=("Backend")
    
    deploy_component "Ingestion Agent" "ops/cloudbuild/cloudbuild.ingestion-agent.yaml" "3" || FAILED_STEPS+=("Ingestion Agent")
    if [[ ! " ${FAILED_STEPS[@]} " =~ " Ingestion Agent " ]]; then
        configure_dlq_for_trigger "ingestion-agent-trigger" "$DLQ_TOPIC_INGESTION" || FAILED_STEPS+=("Ingestion Agent DLQ")
    fi

    deploy_component "Condition Assessor" "ops/cloudbuild/cloudbuild.condition-assessor.yaml" "4" || FAILED_STEPS+=("Condition Assessor")
    if [[ ! " ${FAILED_STEPS[@]} " =~ " Condition Assessor " ]]; then
        configure_dlq_for_trigger "condition-assessor-trigger" "$DLQ_TOPIC_CONDITION" || FAILED_STEPS+=("Condition Assessor DLQ")
    fi

    deploy_component "Strategist Agent" "ops/cloudbuild/cloudbuild.strategist-agent.yaml" "5" || FAILED_STEPS+=("Strategist Agent")
    deploy_component "Price Research" "ops/cloudbuild/cloudbuild.price-research.yaml" "6" || FAILED_STEPS+=("Price Research")
    deploy_component "Ambassador Agent" "ops/cloudbuild/cloudbuild.ambassador-agent.yaml" "7" || FAILED_STEPS+=("Ambassador Agent")

    # Final Step: Frontend
    if ! deploy_frontend; then FAILED_STEPS+=("Frontend"); fi
    
    # Final summary
    echo ""
    log "Deployment process completed!"
    
    if [ ${#FAILED_STEPS[@]} -eq 0 ]; then
        log "✓ All steps completed successfully!"
        append_log "## Deployment Summary\n\n"
        append_log "**Overall Status:** ✅ Success\n"
        append_log "**All steps completed successfully**\n\n"
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
        append_log "Please check the error messages above and review Cloud Build / Cloud Run logs.\n"
    fi
    
    log "Deployment log saved to: $DEPLOYMENT_LOG"
    append_log "\n---\n*Generated at $(date +'%Y-%m-%d %H:%M:%S')*\n"
}

# Run main function
main
