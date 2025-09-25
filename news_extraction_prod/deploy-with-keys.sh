#!/bin/bash

# Deploy News Extraction Service with Existing API Keys
# This script uses your existing .env file for API keys

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🚀 News Extraction Service - Deployment with Existing Keys${NC}"
echo "============================================================="

# Check if .env file exists
if [[ ! -f "../.env" ]]; then
    echo -e "${RED}❌ .env file not found in parent directory${NC}"
    echo "Expected location: /home/ajay/projects/news_extraction/.env"
    exit 1
fi

echo -e "${GREEN}✅ Found .env file with existing API keys${NC}"

# Load environment variables from .env
source ../.env

# Verify key variables are set
if [[ -z "$OPENROUTER_API_KEY" ]]; then
    echo -e "${RED}❌ OPENROUTER_API_KEY not found in .env${NC}"
    exit 1
fi

echo -e "${GREEN}✅ OpenRouter API key loaded${NC}"

# Check optional keys
TELEGRAM_KEY=${TELEGRAM_HTTP_API_KEY:-""}
GOOGLE_TTS_KEY=${GOOGLE_API_KEY:-""}

if [[ -n "$TELEGRAM_KEY" ]]; then
    echo -e "${GREEN}✅ Telegram key available${NC}"
else
    echo -e "${YELLOW}⚠️  Telegram key not found - will use local storage fallback${NC}"
fi

if [[ -n "$GOOGLE_TTS_KEY" ]]; then
    echo -e "${GREEN}✅ Google TTS key available${NC}"
else
    echo -e "${YELLOW}⚠️  Google TTS key not found - will use eSpeak fallback${NC}"
fi

# Get project configuration
echo ""
read -p "Enter Google Cloud Project ID (or create new): " PROJECT_ID
read -p "Enter storage bucket name (globally unique): " BUCKET_NAME

if [[ -z "$PROJECT_ID" || -z "$BUCKET_NAME" ]]; then
    echo -e "${RED}❌ Project ID and bucket name are required${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}📋 Deployment Configuration:${NC}"
echo "  Project ID: $PROJECT_ID"
echo "  Bucket: $BUCKET_NAME"
echo "  OpenRouter Key: ${OPENROUTER_API_KEY:0:12}..."
echo "  Telegram: $([ -n "$TELEGRAM_KEY" ] && echo "✅ Available" || echo "❌ Not configured")"
echo "  Google TTS: $([ -n "$GOOGLE_TTS_KEY" ] && echo "✅ Available" || echo "❌ Not configured")"

echo ""
read -p "Continue with deployment? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Deployment cancelled."
    exit 0
fi

# Check if gcloud is installed and authenticated
echo -e "${YELLOW}🌥️  Checking Google Cloud CLI...${NC}"
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found${NC}"
    echo "Install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Check authentication
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1 > /dev/null; then
    echo -e "${RED}❌ Please authenticate with gcloud: gcloud auth login${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Google Cloud CLI ready${NC}"

# Set project
echo -e "${YELLOW}📋 Setting up project...${NC}"
gcloud config set project $PROJECT_ID

# Enable required APIs
echo -e "${YELLOW}🔌 Enabling required APIs...${NC}"
gcloud services enable \
    cloudbuild.googleapis.com \
    run.googleapis.com \
    storage.googleapis.com \
    secretmanager.googleapis.com \
    cloudscheduler.googleapis.com

echo -e "${GREEN}✅ APIs enabled${NC}"

# Create storage bucket
echo -e "${YELLOW}🗄️  Creating storage bucket...${NC}"
if gsutil mb gs://$BUCKET_NAME 2>/dev/null; then
    echo -e "${GREEN}✅ Bucket created: gs://$BUCKET_NAME${NC}"
else
    echo -e "${YELLOW}⚠️  Bucket may already exist${NC}"
fi

# Set public read access for podcast files
gsutil iam ch allUsers:objectViewer gs://$BUCKET_NAME

# Store secrets in Google Secret Manager
echo -e "${YELLOW}🔐 Storing API keys in Secret Manager...${NC}"

# Store OpenRouter key
echo -n "$OPENROUTER_API_KEY" | gcloud secrets create openrouter-api-key --data-file=- 2>/dev/null || \
echo -n "$OPENROUTER_API_KEY" | gcloud secrets versions add openrouter-api-key --data-file=-

# Store optional keys
if [[ -n "$TELEGRAM_KEY" ]]; then
    echo -n "$TELEGRAM_KEY" | gcloud secrets create telegram-bot-token --data-file=- 2>/dev/null || \
    echo -n "$TELEGRAM_KEY" | gcloud secrets versions add telegram-bot-token --data-file=-
fi

if [[ -n "$GOOGLE_TTS_KEY" ]]; then
    echo -n "$GOOGLE_TTS_KEY" | gcloud secrets create google-tts-api-key --data-file=- 2>/dev/null || \
    echo -n "$GOOGLE_TTS_KEY" | gcloud secrets versions add google-tts-api-key --data-file=-
fi

echo -e "${GREEN}✅ Secrets stored in Secret Manager${NC}"

# Build container using Google Cloud Build (no local Docker needed!)
echo -e "${YELLOW}🐳 Building container with Google Cloud Build...${NC}"
gcloud builds submit --tag gcr.io/$PROJECT_ID/news-extractor .

if [[ $? -ne 0 ]]; then
    echo -e "${RED}❌ Container build failed${NC}"
    echo "Check the build logs above for specific errors"
    exit 1
fi

echo -e "${GREEN}✅ Container built successfully${NC}"

# Build secret environment flags
SECRET_FLAGS=""
SECRET_FLAGS="$SECRET_FLAGS --set-secrets OPENROUTER_API_KEY=openrouter-api-key:latest"

if gcloud secrets describe telegram-bot-token &>/dev/null; then
    SECRET_FLAGS="$SECRET_FLAGS,TELEGRAM_BOT_TOKEN=telegram-bot-token:latest"
fi

if gcloud secrets describe telegram-chat-id &>/dev/null; then
    SECRET_FLAGS="$SECRET_FLAGS,TELEGRAM_CHAT_ID=telegram-chat-id:latest"
fi

if gcloud secrets describe google-tts-api-key &>/dev/null; then
    SECRET_FLAGS="$SECRET_FLAGS,GOOGLE_TTS_API_KEY=google-tts-api-key:latest"
fi

# Deploy to Cloud Run
echo -e "${YELLOW}☁️  Deploying to Cloud Run...${NC}"
gcloud run deploy news-extractor \
    --image gcr.io/$PROJECT_ID/news-extractor \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 1 \
    --timeout 900 \
    --max-instances 3 \
    --set-env-vars ENVIRONMENT=production \
    --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID \
    --set-env-vars CLOUD_STORAGE_BUCKET=$BUCKET_NAME \
    $SECRET_FLAGS

if [[ $? -ne 0 ]]; then
    echo -e "${RED}❌ Cloud Run deployment failed${NC}"
    exit 1
fi

# Get the service URL
SERVICE_URL=$(gcloud run services describe news-extractor --region=us-central1 --format="value(status.url)")
echo -e "${GREEN}✅ Service deployed: $SERVICE_URL${NC}"

# Test the deployment
echo -e "${YELLOW}🧪 Testing deployment...${NC}"
if curl -f "$SERVICE_URL/health" --connect-timeout 30; then
    echo -e "${GREEN}✅ Health check passed${NC}"
else
    echo -e "${RED}❌ Health check failed${NC}"
    echo "Check Cloud Run logs: gcloud run services logs tail news-extractor --region=us-central1"
fi

# Set up daily scheduler
echo -e "${YELLOW}⏰ Setting up daily scheduler...${NC}"
gcloud scheduler jobs create http daily-news-processing \
    --location=us-central1 \
    --schedule="0 6 * * *" \
    --uri="$SERVICE_URL/process-news" \
    --http-method=POST \
    --headers="Content-Type=application/json" \
    --message-body='{"max_articles": 60, "generate_podcast": true}' \
    --time-zone="UTC" \
    --description="Daily automated news processing" 2>/dev/null || \
echo -e "${YELLOW}⚠️  Scheduler job may already exist${NC}"

echo ""
echo -e "${GREEN}🎉 Deployment Complete!${NC}"
echo ""
echo -e "${YELLOW}📊 Summary:${NC}"
echo "  🌐 Service URL: $SERVICE_URL"
echo "  🗄️  Storage: gs://$BUCKET_NAME"
echo "  ⏰ Daily processing: 6:00 AM UTC"
echo "  💰 Estimated cost: $10-30/month"
echo ""
echo -e "${YELLOW}🧪 Test Commands:${NC}"
echo "  Health check: curl $SERVICE_URL/health"
echo "  Test pipeline: curl $SERVICE_URL/test-pipeline"
echo "  Manual trigger: curl -X POST -H 'Content-Type: application/json' -d '{\"max_articles\": 5, \"generate_podcast\": true}' $SERVICE_URL/process-news"
echo ""
echo -e "${YELLOW}🔗 Management URLs:${NC}"
echo "  Cloud Run: https://console.cloud.google.com/run/detail/us-central1/news-extractor?project=$PROJECT_ID"
echo "  Storage: https://console.cloud.google.com/storage/browser/$BUCKET_NAME?project=$PROJECT_ID"
echo "  Scheduler: https://console.cloud.google.com/cloudscheduler?project=$PROJECT_ID"
echo ""
echo -e "${GREEN}Your automated daily news podcast service is now live! 🎧${NC}"