#!/bin/bash
# =============================================================================
# Fix Script: Condition Assessment Deployment Issue
# =============================================================================
# Problem: Alte Ingestion Agent Version deployed (verwendet HTTP statt Pub/Sub)
# Solution: Deploy updated Ingestion Agent mit Pub/Sub + Setup Pub/Sub Topic
# =============================================================================

set -e  # Exit on error

PROJECT_ID="project-52b2fab8-15a1-4b66-9f3"
REGION="europe-west1"
TOPIC_NAME="trigger-condition-assessment"

echo "============================================================================="
echo "🔧 Fix: Condition Assessment Deployment"
echo "============================================================================="
echo ""

# Step 1: Check current deployment
echo "📋 Step 1/5: Checking current Ingestion Agent deployment..."
echo "-----------------------------------------------------------------------------"
gcloud run services describe ingestion-agent \
  --region=$REGION \
  --project=$PROJECT_ID \
  --format="table(metadata.name,status.url,metadata.creationTimestamp)" 2>/dev/null || echo "⚠️  Service not found or not deployed"
echo ""

# Step 2: Check if Pub/Sub topic exists
echo "📋 Step 2/5: Checking Pub/Sub topic..."
echo "-----------------------------------------------------------------------------"
if gcloud pubsub topics describe $TOPIC_NAME --project=$PROJECT_ID &>/dev/null; then
    echo "✅ Pub/Sub topic '$TOPIC_NAME' already exists"
else
    echo "❌ Pub/Sub topic '$TOPIC_NAME' does not exist"
    echo "📝 Creating Pub/Sub topic..."
    gcloud pubsub topics create $TOPIC_NAME --project=$PROJECT_ID
    echo "✅ Topic created successfully"
fi
echo ""

# Step 3: Check if Pub/Sub subscription exists
echo "📋 Step 3/5: Checking Pub/Sub subscription..."
echo "-----------------------------------------------------------------------------"
SUBSCRIPTION_NAME="condition-assessment-subscription"
CONDITION_ASSESSOR_URL="https://condition-assessor-wdx23mmzfq-ew.a.run.app"

if gcloud pubsub subscriptions describe $SUBSCRIPTION_NAME --project=$PROJECT_ID &>/dev/null; then
    echo "✅ Pub/Sub subscription '$SUBSCRIPTION_NAME' already exists"
else
    echo "❌ Subscription does not exist"
    echo "📝 Creating Pub/Sub push subscription to Condition Assessor..."
    gcloud pubsub subscriptions create $SUBSCRIPTION_NAME \
      --topic=$TOPIC_NAME \
      --push-endpoint=$CONDITION_ASSESSOR_URL \
      --push-auth-service-account=252725930721-compute@developer.gserviceaccount.com \
      --project=$PROJECT_ID
    echo "✅ Subscription created successfully"
fi
echo ""

# Step 4: Deploy updated Ingestion Agent
echo "📋 Step 4/5: Deploying updated Ingestion Agent..."
echo "-----------------------------------------------------------------------------"
echo "📦 Building and deploying from: ./agents/ingestion-agent"
echo "🎯 This version uses Pub/Sub instead of HTTP"
echo ""

gcloud run deploy ingestion-agent \
  --source=./agents/ingestion-agent \
  --region=$REGION \
  --project=$PROJECT_ID \
  --platform=managed \
  --allow-unauthenticated \
  --set-env-vars="GOOGLE_CLOUD_PROJECT=$PROJECT_ID" \
  --timeout=540 \
  --memory=1Gi \
  --cpu=1 \
  --max-instances=10 \
  --min-instances=0

echo "✅ Ingestion Agent deployed successfully"
echo ""

# Step 5: Verify deployment
echo "📋 Step 5/5: Verifying deployment..."
echo "-----------------------------------------------------------------------------"
echo ""
echo "✅ Checking Ingestion Agent service..."
gcloud run services describe ingestion-agent \
  --region=$REGION \
  --project=$PROJECT_ID \
  --format="value(status.url)"

echo ""
echo "✅ Checking Pub/Sub topic..."
gcloud pubsub topics describe $TOPIC_NAME \
  --project=$PROJECT_ID \
  --format="value(name)"

echo ""
echo "✅ Checking Pub/Sub subscription..."
gcloud pubsub subscriptions describe $SUBSCRIPTION_NAME \
  --project=$PROJECT_ID \
  --format="value(name,pushConfig.pushEndpoint)"

echo ""
echo "============================================================================="
echo "✅ Deployment Complete!"
echo "============================================================================="
echo ""
echo "📝 Next Steps:"
echo "   1. Test the upload workflow with new images"
echo "   2. Check logs with: gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=ingestion-agent' --limit=50"
echo "   3. Verify Condition Assessor receives CloudEvents"
echo "   4. Check Frontend for condition assessment results"
echo ""
echo "🔍 Expected Log Patterns:"
echo "   Ingestion Agent: '✅ Successfully published condition assessment job to Pub/Sub'"
echo "   Condition Assessor: '🎯 CONDITION ASSESSOR: New CloudEvent received'"
echo ""

