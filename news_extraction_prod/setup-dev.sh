#!/bin/bash

# Local Development Environment Setup
# This script helps you set up API keys and test the service locally

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}🔧 Local Development Environment Setup${NC}"
echo ""

# Create .env file if it doesn't exist
if [[ ! -f ".env" ]]; then
    echo -e "${YELLOW}📝 Creating .env file...${NC}"
    cat > .env << 'EOF'
# Development Environment Configuration
ENVIRONMENT=development

# Google Cloud (for local testing with service account)
# GOOGLE_CLOUD_PROJECT=your-project-id
# CLOUD_STORAGE_BUCKET=your-bucket-name
# GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json

# API Keys
# OPENROUTER_API_KEY=your-openrouter-key-here

# Optional: Telegram Integration
# TELEGRAM_BOT_TOKEN=your-bot-token
# TELEGRAM_CHAT_ID=your-chat-id

# TTS Configuration (development uses eSpeak by default)
USE_GOOGLE_TTS=false
EOF
    echo -e "${GREEN}✅ Created .env file${NC}"
    echo -e "${YELLOW}📝 Please edit .env and add your API keys${NC}"
else
    echo -e "${GREEN}✅ .env file exists${NC}"
fi

# Check if virtual environment exists
if [[ ! -d ".venv" ]]; then
    echo -e "${YELLOW}🐍 Creating Python virtual environment...${NC}"
    python3 -m venv .venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}🔄 Activating virtual environment...${NC}"
source .venv/bin/activate

# Install dependencies
echo -e "${YELLOW}📦 Installing dependencies...${NC}"
pip install --upgrade pip
pip install -r requirements.txt

# Install system dependencies (eSpeak for TTS)
if ! command -v espeak &> /dev/null; then
    echo -e "${YELLOW}🔊 eSpeak not found. Please install it:${NC}"
    echo "Ubuntu/Debian: sudo apt-get install espeak espeak-data libespeak-dev"
    echo "macOS: brew install espeak"
    echo "Other: Check your package manager"
fi

echo -e "${GREEN}✅ Dependencies installed${NC}"

# Run tests
echo -e "${YELLOW}🧪 Running basic tests...${NC}"
python3 -c "
import sys
sys.path.append('.')
from src.rss_fetcher import RSSFetcher
from src.ai_summarizer import AISummarizer
from config.settings import get_config

config = get_config()
print('✅ Configuration loaded')

# Test RSS fetching
rss = RSSFetcher(config)
print('✅ RSS Fetcher initialized')

# Test AI summarizer (mock mode)
ai = AISummarizer(config)
print('✅ AI Summarizer initialized')

print('✅ Basic component tests passed')
"

echo ""
echo -e "${GREEN}🎉 Local development environment ready!${NC}"
echo ""
echo "🚀 To start the development server:"
echo "  source .venv/bin/activate"
echo "  python3 main.py"
echo ""
echo "🧪 To test endpoints:"
echo "  curl http://localhost:8080/health"
echo "  curl http://localhost:8080/test-pipeline"
echo ""
echo -e "${YELLOW}📝 Don't forget to:${NC}"
echo "1. Edit .env file with your API keys"
echo "2. Install eSpeak for TTS testing"
echo "3. Set up Google Cloud credentials for storage testing"