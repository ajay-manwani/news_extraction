# News Extraction & Podcast Generation Service

An automated news processing service that extracts news from RSS feeds, generates AI summaries using Grok, converts to high-quality audio using Google TTS, and delivers via Telegram.

## 🚀 Current Status (September 25, 2025)

### ✅ Production Deployment
- **Cloud Service URL**: `https://news-extractor-1098617772781.us-central1.run.app`
- **Project ID**: `news-extraction-1758726977`
- **Current Revision**: `news-extractor-00018-nwp`
- **Status**: ✅ **FULLY OPERATIONAL**

### ✅ Key Components Working
- **AI Model**: Grok 4 Fast (xAI) - `x-ai/grok-4-fast:free`
- **TTS Engine**: Google Cloud Text-to-Speech (premium quality)
- **Delivery**: Telegram Bot integration
- **Storage**: Google Cloud Storage
- **Secrets**: Google Secret Manager

## 📁 Project Structure

```
news_extraction/
├── news_extraction_prod/     # Main production codebase
│   ├── src/
│   │   ├── ai_summarizer.py     # AI summarization with Grok
│   │   ├── tts_generator.py     # TTS with Google/eSpeak fallback
│   │   ├── telegram_sender.py   # Telegram delivery
│   │   ├── rss_processor.py     # RSS feed processing
│   │   └── config.py            # Configuration management
│   ├── main.py                  # Flask application entry point
│   ├── requirements.txt         # Local dependencies
│   └── .env                     # Local environment variables
├── cloud_build_temp/         # Clean build directory for deployments
└── README.md                 # This file
```

## 🔧 Local Development Setup

### Prerequisites
- Python 3.11+
- UV package manager (`pip install uv`)

### Quick Start
```bash
cd /home/ajay/projects/news_extraction/news_extraction_prod
uv sync
source .venv/bin/activate
python main.py  # Runs locally on port 8080
```

### Environment Variables (.env)
```bash
# AI Models
AI_MODEL=x-ai/grok-4-fast:free
OPENROUTER_API_KEY=sk-or-v1-[your-openrouter-key]

# Google Services  
GOOGLE_CLOUD_TTS_API_KEY=[your-google-tts-api-key]
USE_GOOGLE_TTS=true

# Telegram
TELEGRAM_BOT_TOKEN=[your-telegram-bot-token]
TELEGRAM_CHAT_ID=[your-telegram-chat-id]

# Environment
ENVIRONMENT=production
```

## ☁️ Cloud Deployment

### Current Cloud Configuration
- **Platform**: Google Cloud Run (us-central1)
- **Container**: `gcr.io/news-extraction-1758726977/news-extractor:grok-working`
- **Resources**: 2 CPU, 2Gi RAM, 1800s timeout
- **Service Account**: `1098617772781-compute@developer.gserviceaccount.com`

### Environment Variables (Cloud)
```bash
AI_MODEL=x-ai/grok-4-fast:free
ENVIRONMENT=production
USE_GOOGLE_TTS=true
```

### Secrets (Google Secret Manager)
- `openrouter-api-key` → OpenRouter API key for Grok
- `google-tts-api-key` → Google Cloud TTS API key
- `telegram-bot-token` → Telegram bot authentication
- `telegram-chat-id` → Target Telegram chat ID

### Deployment Commands
```bash
# Build and deploy new container
cd /home/ajay/projects/news_extraction/cloud_build_temp
gcloud builds submit --tag gcr.io/news-extraction-1758726977/news-extractor:latest
gcloud run deploy news-extractor \
  --image gcr.io/news-extraction-1758726977/news-extractor:latest \
  --region us-central1 \
  --project news-extraction-1758726977
```

## 🛠️ API Endpoints

### Health & Status
- `GET /health` - Service health check
- `GET /` - Service info and available endpoints
- `GET /test-pipeline` - Test all components

### Processing
- `POST /process-news` - Run full news processing pipeline
- `GET /storage-info` - Check storage usage
- `POST /cleanup-storage` - Clean old files

## 🔍 Recent Achievements

### Major Fixes Completed (Sept 25, 2025)
1. **✅ Grok Model Integration**: Fixed hardcoded GPT-3.5 references, now properly uses Grok
2. **✅ Google TTS Working**: Fixed corrupted API key secret (was "8" instead of full key)
3. **✅ Complete Cloud Parity**: Cloud service now matches local quality
4. **✅ Secret Management**: All credentials properly secured in Google Secret Manager

### Performance
- **Local**: 60 AI summaries in ~3-5 minutes
- **Cloud**: Full pipeline completes in ~5-7 minutes
- **Audio Quality**: Premium Google TTS (vs robotic eSpeak fallback)

## 🚦 Troubleshooting

### Common Issues & Solutions

#### 1. eSpeak Audio Instead of Google TTS
**Symptoms**: Robotic voice in Telegram
**Solution**: Check Google TTS API key in Secret Manager
```bash
gcloud secrets versions access latest --secret="google-tts-api-key" --project=news-extraction-1758726977
```

#### 2. GPT-3.5 Instead of Grok
**Symptoms**: OpenRouter shows GPT-3.5 usage
**Solution**: Verify AI_MODEL environment variable and redeploy
```bash
gcloud run services describe news-extractor --region=us-central1 --project=news-extraction-1758726977
```

#### 3. Build Failures
**Symptoms**: Container build timeouts/cancellations
**Solution**: Use clean build directory, check Cloud Build logs
```bash
cd cloud_build_temp  # Always build from clean directory
```

### Debugging Commands
```bash
# Check service status
curl -X GET https://news-extractor-1098617772781.us-central1.run.app/health

# Test pipeline components
curl -X GET https://news-extractor-1098617772781.us-central1.run.app/test-pipeline

# Check current deployment
gcloud run services describe news-extractor --region=us-central1 --project=news-extraction-1758726977
```

## 📈 Future Enhancement Ideas

### Near-term Improvements
- [ ] **Processing Speed**: Optimize pipeline to reduce 5-minute timeout
- [ ] **More News Sources**: Expand RSS feed list 
- [ ] **Better Error Handling**: More robust failure recovery
- [ ] **Monitoring**: Add logging and alerting

### Advanced Features
- [ ] **Multi-language Support**: International news processing
- [ ] **Custom Topics**: Filter news by user interests
- [ ] **Multiple Delivery Channels**: Email, Discord, Slack
- [ ] **Audio Customization**: Different voices, speeds, styles
- [ ] **Scheduled Processing**: Automated daily runs via Cloud Scheduler

## 🔒 Security Notes

- All API keys stored in Google Secret Manager (never in code)
- Service account follows least-privilege principle
- Container runs as non-root user
- No sensitive data in environment variables

## 📊 Cost Monitoring

### Services Usage
- **OpenRouter/Grok**: ~$0.001 per summary (very affordable)
- **Google TTS**: ~$0.016 per 1M characters
- **Cloud Run**: Pay-per-request (minimal when idle)
- **Storage**: Minimal usage with cleanup

## 🤝 Quick Continuation Guide

When reloading this project:
1. **Status Check**: `curl https://news-extractor-1098617772781.us-central1.run.app/health`
2. **Local Setup**: `cd news_extraction_prod && source .venv/bin/activate`
3. **Test Run**: `curl -X GET [service-url]/test-pipeline`

## 📝 Development Log

### 2025-09-25 - Major Milestone ✅
- Successfully deployed Grok + Google TTS to production cloud
- Fixed all major configuration issues
- Achieved feature parity between local and cloud environments
- Service generating high-quality news podcasts automatically

---

**Last Updated**: September 25, 2025  
**Service Status**: 🟢 OPERATIONAL  
**Next Planned**: Feature enhancements and optimization