#!/bin/bash

# Production Deployment Script for News Extraction Service
# Usage: ./deploy.sh [project-id] [bucket-name]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=${1:-"news-extraction-$(date +%s)"}
BUCKET_NAME=${2:-"news-podcasts-${PROJECT_ID}"}
REGION=${3:-"us-central1"}
SERVICE_NAME="news-extraction"

echo -e "${GREEN}🚀 Starting News Extraction Service Deployment${NC}"
echo "Project ID: $PROJECT_ID"
echo "Bucket Name: $BUCKET_NAME" 
echo "Region: $REGION"
echo ""

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found. Please install: https://cloud.google.com/sdk/docs/install${NC}"
    exit 1
fi

# Check authentication
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1 > /dev/null; then
    echo -e "${RED}❌ Please authenticate with gcloud: gcloud auth login${NC}"
    exit 1
fi

# Create project (if it doesn't exist)
echo -e "${YELLOW}📋 Setting up Google Cloud project...${NC}"
if ! gcloud projects describe $PROJECT_ID &> /dev/null; then
    echo "Creating project: $PROJECT_ID"
    gcloud projects create $PROJECT_ID
    echo -e "${GREEN}✅ Project created${NC}"
else
    echo -e "${GREEN}✅ Project exists${NC}"
fi

# Set project
gcloud config set project $PROJECT_ID

# Enable billing (user needs to do this manually)
echo -e "${YELLOW}⚠️  Please ensure billing is enabled for project: $PROJECT_ID${NC}"
read -p "Press Enter when billing is enabled..."

# Enable APIs
echo -e "${YELLOW}🔌 Enabling required APIs...${NC}"
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    storage.googleapis.com \
    texttospeech.googleapis.com \
    secretmanager.googleapis.com \
    cloudscheduler.googleapis.com

echo -e "${GREEN}✅ APIs enabled${NC}"

# Create service account
echo -e "${YELLOW}👤 Creating service account...${NC}"
SERVICE_ACCOUNT="$SERVICE_NAME@$PROJECT_ID.iam.gserviceaccount.com"

if ! gcloud iam service-accounts describe $SERVICE_ACCOUNT &> /dev/null; then
    gcloud iam service-accounts create $SERVICE_NAME \
        --display-name="News Extraction Service" \
        --description="Service account for automated news processing"
    
    # Grant roles
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/storage.admin"
    
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/texttospeech.user"
    
    gcloud projects add-iam-policy-binding $PROJECT_ID \
        --member="serviceAccount:$SERVICE_ACCOUNT" \
        --role="roles/secretmanager.secretAccessor"
    
    echo -e "${GREEN}✅ Service account created and configured${NC}"
else
    echo -e "${GREEN}✅ Service account exists${NC}"
fi

# Create storage bucket
echo -e "${YELLOW}🗄️  Creating Cloud Storage bucket...${NC}"
if ! gsutil ls -b gs://$BUCKET_NAME &> /dev/null; then
    gsutil mb -l $REGION gs://$BUCKET_NAME
    gsutil iam ch allUsers:objectViewer gs://$BUCKET_NAME
    echo -e "${GREEN}✅ Bucket created and configured for public read${NC}"
else
    echo -e "${GREEN}✅ Bucket exists${NC}"
fi

# Prompt for API keys
echo -e "${YELLOW}🔑 Setting up API keys...${NC}"
echo "You'll need to provide the following API keys:"

# OpenRouter API Key (required)
read -p "OpenRouter API Key (required): " OPENROUTER_KEY
if [[ -z "$OPENROUTER_KEY" ]]; then
    echo -e "${RED}❌ OpenRouter API key is required${NC}"
    exit 1
fi

echo -n "$OPENROUTER_KEY" | gcloud secrets create openrouter-api-key --data-file=- || true

# Optional keys
read -p "Telegram Bot Token (optional, press Enter to skip): " TELEGRAM_TOKEN
if [[ ! -z "$TELEGRAM_TOKEN" ]]; then
    echo -n "$TELEGRAM_TOKEN" | gcloud secrets create telegram-bot-token --data-file=- || true
fi

read -p "Telegram Chat ID (optional, press Enter to skip): " TELEGRAM_CHAT
if [[ ! -z "$TELEGRAM_CHAT" ]]; then
    echo -n "$TELEGRAM_CHAT" | gcloud secrets create telegram-chat-id --data-file=- || true
fi

echo -e "${GREEN}✅ Secrets configured${NC}"

# Build and deploy to Cloud Run
echo -e "${YELLOW}🐳 Building and deploying to Cloud Run...${NC}"

SECRET_FLAGS=""
if gcloud secrets describe openrouter-api-key &> /dev/null; then
    SECRET_FLAGS="--set-secrets OPENROUTER_API_KEY=openrouter-api-key:latest"
fi

if gcloud secrets describe telegram-bot-token &> /dev/null; then
    SECRET_FLAGS="$SECRET_FLAGS,TELEGRAM_BOT_TOKEN=telegram-bot-token:latest"
fi

if gcloud secrets describe telegram-chat-id &> /dev/null; then
    SECRET_FLAGS="$SECRET_FLAGS,TELEGRAM_CHAT_ID=telegram-chat-id:latest"
fi

gcloud run deploy $SERVICE_NAME \
    --source . \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --service-account $SERVICE_ACCOUNT \
    --set-env-vars ENVIRONMENT=production \
    --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID \
    --set-env-vars CLOUD_STORAGE_BUCKET=$BUCKET_NAME \
    $SECRET_FLAGS \
    --memory 1Gi \
    --cpu 1 \
    --timeout 900 \
    --max-instances 3 \
    --min-instances 0

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --region $REGION --format 'value(status.url)')
echo -e "${GREEN}✅ Service deployed: $SERVICE_URL${NC}"

# Test deployment
echo -e "${YELLOW}🧪 Testing deployment...${NC}"
curl -f "$SERVICE_URL/health" && echo -e "${GREEN}✅ Health check passed${NC}" || echo -e "${RED}❌ Health check failed${NC}"

# Create Cloud Scheduler job
echo -e "${YELLOW}⏰ Setting up daily scheduler...${NC}"
if ! gcloud scheduler jobs describe daily-news-processing --location=$REGION &> /dev/null; then
    gcloud scheduler jobs create http daily-news-processing \
        --location=$REGION \
        --schedule="0 6 * * *" \
        --uri="$SERVICE_URL/process-news" \
        --http-method=POST \
        --headers="Content-Type=application/json" \
        --message-body='{"max_articles": 60, "generate_podcast": true}' \
        --time-zone="UTC" \
        --description="Daily automated news processing"
    
    echo -e "${GREEN}✅ Scheduler job created${NC}"
else
    echo -e "${GREEN}✅ Scheduler job exists${NC}"
fi

# Summary
echo ""
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo ""
echo "📊 Summary:"
echo "- Project: $PROJECT_ID"
echo "- Service URL: $SERVICE_URL"
echo "- Storage Bucket: gs://$BUCKET_NAME"
echo "- Daily processing: 6:00 AM UTC"
echo ""
echo "🔗 Useful URLs:"
echo "- Cloud Console: https://console.cloud.google.com/run/detail/$REGION/$SERVICE_NAME?project=$PROJECT_ID"
echo "- Storage Bucket: https://console.cloud.google.com/storage/browser/$BUCKET_NAME?project=$PROJECT_ID"
echo "- Scheduler: https://console.cloud.google.com/cloudscheduler?project=$PROJECT_ID"
echo ""
echo "🧪 Test manually:"
echo "curl -X POST -H 'Content-Type: application/json' -d '{\"max_articles\": 5, \"generate_podcast\": true}' $SERVICE_URL/process-news"
echo ""
echo -e "${YELLOW}💰 Remember to monitor costs and set up billing alerts!${NC}"