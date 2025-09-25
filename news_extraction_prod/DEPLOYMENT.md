# News Extraction Service - Production Deployment Guide

## Overview
This guide walks through deploying the news extraction service to Google Cloud Run with automated daily processing.

## Prerequisites
- Google Cloud account with billing enabled
- `gcloud` CLI installed and authenticated
- Docker installed locally (for testing)

## Step 1: Environment Configuration

### 1.1 Create Production Environment File
Create `.env.production` with your actual API keys:

```bash
# Google Cloud Configuration
GOOGLE_CLOUD_PROJECT=your-project-id
CLOUD_STORAGE_BUCKET=your-bucket-name
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# API Keys
OPENROUTER_API_KEY=your-openrouter-key
GOOGLE_TTS_API_KEY=your-google-tts-key  # Optional, will use OpenAI TTS as fallback
TELEGRAM_BOT_TOKEN=your-bot-token       # Optional
TELEGRAM_CHAT_ID=your-chat-id          # Optional

# Environment
ENVIRONMENT=production
```

### 1.2 Required API Keys and Services

#### OpenRouter API (Required for AI Summarization)
- Sign up at: https://openrouter.ai/
- Get API key from dashboard
- Cost: ~$0.10 per 1000 requests with Gemma-2-9B model

#### Google Cloud Services (Required)
- Text-to-Speech API (for podcast generation)
- Cloud Storage (for file hosting)
- Cloud Run (for deployment)
- Secret Manager (for secure credential storage)

#### Optional Services
- Telegram Bot (for notifications)
- Alternative TTS services (if not using Google TTS)

## Step 2: Google Cloud Setup

### 2.1 Create Project and Enable APIs
```bash
# Create project
gcloud projects create your-project-id

# Set project
gcloud config set project your-project-id

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  cloudbuild.googleapis.com \
  storage.googleapis.com \
  texttospeech.googleapis.com \
  secretmanager.googleapis.com \
  cloudscheduler.googleapis.com
```

### 2.2 Create Service Account
```bash
# Create service account
gcloud iam service-accounts create news-extraction \
  --display-name="News Extraction Service" \
  --description="Service account for automated news processing"

# Grant necessary roles
gcloud projects add-iam-policy-binding your-project-id \
  --member="serviceAccount:news-extraction@your-project-id.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding your-project-id \
  --member="serviceAccount:news-extraction@your-project-id.iam.gserviceaccount.com" \
  --role="roles/texttospeech.user"

gcloud projects add-iam-policy-binding your-project-id \
  --member="serviceAccount:news-extraction@your-project-id.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

### 2.3 Create Cloud Storage Bucket
```bash
# Create bucket for podcasts (must be globally unique)
gsutil mb gs://your-unique-bucket-name

# Set public read access for podcast files
gsutil iam ch allUsers:objectViewer gs://your-unique-bucket-name
```

### 2.4 Store Secrets in Secret Manager
```bash
# Store OpenRouter API key
echo -n "your-openrouter-key" | gcloud secrets create openrouter-api-key --data-file=-

# Store Telegram credentials (optional)
echo -n "your-bot-token" | gcloud secrets create telegram-bot-token --data-file=-
echo -n "your-chat-id" | gcloud secrets create telegram-chat-id --data-file=-
```

## Step 3: Container Configuration

### 3.1 Dockerfile Optimization
The Dockerfile should be optimized for:
- Small image size
- Fast cold starts
- Proper dependency caching

### 3.2 Build and Test Locally
```bash
# Build container
docker build -t news-extraction .

# Test container locally
docker run -p 8080:8080 \
  -e GOOGLE_CLOUD_PROJECT=your-project-id \
  -e CLOUD_STORAGE_BUCKET=your-bucket-name \
  -e OPENROUTER_API_KEY=your-key \
  news-extraction
```

## Step 4: Cloud Run Deployment

### 4.1 Deploy to Cloud Run
```bash
# Build and deploy
gcloud run deploy news-extraction \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --service-account news-extraction@your-project-id.iam.gserviceaccount.com \
  --set-env-vars ENVIRONMENT=production \
  --set-env-vars GOOGLE_CLOUD_PROJECT=your-project-id \
  --set-env-vars CLOUD_STORAGE_BUCKET=your-bucket-name \
  --set-secrets OPENROUTER_API_KEY=openrouter-api-key:latest \
  --set-secrets TELEGRAM_BOT_TOKEN=telegram-bot-token:latest \
  --set-secrets TELEGRAM_CHAT_ID=telegram-chat-id:latest \
  --memory 1Gi \
  --cpu 1 \
  --timeout 900 \
  --max-instances 1
```

## Step 5: Automated Scheduling

### 5.1 Create Cloud Scheduler Job
```bash
# Create daily job at 6 AM UTC
gcloud scheduler jobs create http daily-news-processing \
  --schedule="0 6 * * *" \
  --uri="https://your-service-url/process-news" \
  --http-method=POST \
  --headers="Content-Type=application/json" \
  --message-body='{"max_articles": 60, "generate_podcast": true}' \
  --time-zone="UTC" \
  --description="Daily automated news processing"
```

## Step 6: Monitoring and Maintenance

### 6.1 Set up Monitoring
- Cloud Run service logs
- Error reporting
- Uptime monitoring for scheduler

### 6.2 Cost Management
- Monitor API usage costs
- Set up budget alerts
- Optimize processing frequency if needed

## Estimated Monthly Costs
- Cloud Run: $1-5 (minimal usage)
- Cloud Storage: $0.50-2 (few GB storage)
- Text-to-Speech: $2-10 (depending on volume)
- OpenRouter API: $3-15 (depending on article volume)
- **Total: ~$10-30/month** for daily processing

## Testing Checklist
- [ ] Local container runs successfully
- [ ] All environment variables configured
- [ ] API keys working in production
- [ ] Cloud Storage bucket accessible
- [ ] Cloud Run service responds to health checks
- [ ] Scheduler triggers successfully
- [ ] Podcasts generated and stored
- [ ] Cleanup job removes old files

## Support and Troubleshooting
- Check Cloud Run logs: `gcloud run services logs tail news-extraction`
- Monitor API quotas in Google Cloud Console
- Test individual endpoints via Cloud Run service URL