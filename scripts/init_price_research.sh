#!/bin/bash

# Configuration
PROJECT_ID=$(gcloud config get-value project)
REGION="europe-west1"

echo "🚀 Initializing GCP resources for Price Research System in project: $PROJECT_ID"

# 1. Create Pub/Sub Topics
echo "📬 Creating Pub/Sub topics..."
gcloud pubsub topics create price-research-requests --project=$PROJECT_ID 2>/dev/null || echo "Topic price-research-requests already exists."

# 2. Create Cloud Run Service Account (if not exists)
echo "👤 Creating service accounts..."
gcloud iam service-accounts create price-research-agent \
    --display-name="Price Research Agent Service Account" \
    --project=$PROJECT_ID 2>/dev/null || echo "Service account price-research-agent already exists."

# 3. Grant Permissions
echo "🔐 Granting permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:price-research-agent@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/datastore.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:price-research-agent@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:price-research-agent@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/pubsub.publisher"

# 4. Configure Firestore TTL (Experimental/Manual step)
echo "⏳ Note: To enable TTL on 'expires_at' in Firestore, run:"
echo "gcloud firestore fields ttls update expires_at --collection-group=market_data --enable-ttl --project=$PROJECT_ID"

echo "✅ Initialization complete. You can now deploy the agents using Cloud Build."
