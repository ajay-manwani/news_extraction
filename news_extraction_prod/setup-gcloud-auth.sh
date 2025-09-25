#!/bin/bash

# Google Cloud Authentication Setup Guide
# Run this BEFORE deploying your news extraction service

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🌥️ Google Cloud Authentication Setup${NC}"
echo "=========================================="
echo ""

# Step 1: Check if gcloud is installed
echo -e "${YELLOW}Step 1: Checking Google Cloud CLI...${NC}"

if command -v gcloud &> /dev/null; then
    echo "✅ gcloud CLI already installed"
    gcloud version
else
    echo "❌ gcloud CLI not found. Installing..."
    
    # Install gcloud CLI
    echo "🔽 Downloading Google Cloud SDK..."
    curl https://sdk.cloud.google.com | bash
    
    echo -e "${YELLOW}⚠️ Please restart your terminal or run: source ~/.bashrc${NC}"
    echo "Then re-run this script."
    exit 0
fi

echo ""

# Step 2: Authenticate
echo -e "${YELLOW}Step 2: Authentication...${NC}"

# Check if already authenticated
if gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null | head -1 > /dev/null; then
    current_account=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1)
    echo "✅ Already authenticated as: $current_account"
    
    read -p "Continue with this account? (Y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        echo "Switching account..."
        gcloud auth login
    fi
else
    echo "🔐 Need to authenticate with Google Cloud..."
    echo "This will open your browser to sign in."
    gcloud auth login
fi

echo ""

# Step 3: Verify authentication
echo -e "${YELLOW}Step 3: Verifying authentication...${NC}"

if gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1 > /dev/null; then
    account=$(gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1)
    echo "✅ Successfully authenticated as: $account"
else
    echo -e "${RED}❌ Authentication failed. Please try again.${NC}"
    exit 1
fi

echo ""

# Step 4: Set up application default credentials (for local testing)
echo -e "${YELLOW}Step 4: Setting up application default credentials...${NC}"
echo "This allows applications to use your credentials."

gcloud auth application-default login

echo "✅ Application default credentials configured"

echo ""

# Summary
echo -e "${GREEN}🎉 Google Cloud Authentication Complete!${NC}"
echo "=========================================="
echo ""
echo "✅ Google Cloud CLI installed and configured"
echo "✅ Authenticated with your Google account"
echo "✅ Application default credentials set up"
echo ""
echo -e "${GREEN}🚀 You're ready to deploy!${NC}"
echo "Next step: ./deploy-with-keys.sh"
echo ""
echo -e "${YELLOW}💡 What this setup enables:${NC}"
echo "- gcloud commands work with your account"
echo "- Code can be uploaded to Google Cloud Build"
echo "- Services can be deployed to Cloud Run"
echo "- Secrets can be stored in Secret Manager"