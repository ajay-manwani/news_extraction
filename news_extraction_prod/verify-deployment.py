#!/usr/bin/env python3
"""
Pre-deployment verification script
Tests that all API keys work correctly before deploying
"""

import os
import sys
import json
import requests
from pathlib import Path

def load_env_file():
    """Load environment variables from .env file"""
    env_file = Path("../.env")
    if not env_file.exists():
        # Try current directory
        env_file = Path(".env")
        if not env_file.exists():
            # Try parent's parent directory
            env_file = Path("../../.env")
            if not env_file.exists():
                print("❌ .env file not found in parent directory, current directory, or grandparent directory")
                return False
    
    # Load environment variables
    with open(env_file) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key] = value
    
    print(f"✅ Environment variables loaded from {env_file}")
    return True

def verify_api_keys():
    """Verify all required API keys are present"""
    print("\n🔑 Verifying API Keys...")
    
    required_keys = {
        'OPENROUTER_API_KEY': 'AI Summarization',
        'GOOGLE_CLOUD_TTS_API_KEY': 'Text-to-Speech', 
        'TELEGRAM_HTTP_API_KEY': 'Telegram Bot',
        'TELEGRAM_CHAT_ID': 'Telegram Chat',
        'OPENAI_API_KEY': 'OpenAI (backup)'
    }
    
    missing = []
    for key, description in required_keys.items():
        value = os.getenv(key)
        if value:
            # Show first 8 chars for security
            print(f"✅ {key}: {value[:8]}... ({description})")
        else:
            print(f"❌ {key}: Missing ({description})")
            missing.append(key)
    
    if missing:
        print(f"\n❌ Missing API keys: {missing}")
        return False
    
    print("\n✅ All API keys present!")
    return True

def test_openrouter_api():
    """Test OpenRouter API connection"""
    print("\n🤖 Testing OpenRouter API...")
    
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found")
        return False
    
    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'HTTP-Referer': 'https://localhost',
            'X-Title': 'News Extraction Service'
        }
        
        # Test with a simple prompt
        data = {
            'model': 'google/gemma-2-9b-it:free',
            'messages': [
                {'role': 'user', 'content': 'Hello! This is a test. Reply with just "API working".'}
            ],
            'max_tokens': 10,
            'temperature': 0.1
        }
        
        response = requests.post(
            'https://openrouter.ai/api/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                print("✅ OpenRouter API working!")
                return True
            else:
                print("❌ OpenRouter API returned unexpected format")
                return False
        else:
            print(f"❌ OpenRouter API failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ OpenRouter API error: {e}")
        return False

def test_google_tts_key():
    """Test Google TTS API key format"""
    print("\n🗣️ Verifying Google TTS API key...")
    
    api_key = os.getenv('GOOGLE_CLOUD_TTS_API_KEY')
    if not api_key:
        print("❌ GOOGLE_CLOUD_TTS_API_KEY not found")
        return False
    
    # Verify key format
    if api_key.startswith('AIzaSy') and len(api_key) == 39:
        print("✅ Google TTS API key format valid")
        return True
    else:
        print("❌ Google TTS API key format invalid")
        return False

def test_telegram_config():
    """Test Telegram configuration"""
    print("\n📱 Verifying Telegram configuration...")
    
    bot_token = os.getenv('TELEGRAM_HTTP_API_KEY')
    chat_id = os.getenv('TELEGRAM_CHAT_ID')
    
    if not bot_token:
        print("❌ TELEGRAM_HTTP_API_KEY not found")
        return False
    
    if not chat_id:
        print("❌ TELEGRAM_CHAT_ID not found")
        return False
    
    # Verify bot token format
    if ':' in bot_token and bot_token.count(':') == 1:
        bot_id, token = bot_token.split(':')
        if bot_id.isdigit() and len(token) == 35:
            print("✅ Telegram bot token format valid")
        else:
            print("❌ Telegram bot token format invalid")
            return False
    else:
        print("❌ Telegram bot token format invalid")
        return False
    
    # Verify chat ID format
    if chat_id.isdigit():
        print("✅ Telegram chat ID format valid")
        return True
    else:
        print("❌ Telegram chat ID format invalid")
        return False

def test_flask_app():
    """Test if Flask app can start with current configuration"""
    print("\n🌐 Testing Flask application...")
    
    try:
        # Set up the path
        sys.path.insert(0, os.getcwd())
        
        # Import config first to load settings
        from config.settings import get_config
        config = get_config()
        print(f"✅ Configuration loaded: {type(config).__name__}")
        
        # Import and test Flask app
        from main import app
        
        # Test app can be created
        with app.app_context():
            print("✅ Flask app context working")
        
        print("✅ Flask application ready")
        return True
        
    except Exception as e:
        print(f"❌ Flask app test failed: {e}")
        return False

def main():
    print("🔍 Pre-Deployment API Key Verification")
    print("=" * 50)
    
    # Run all tests
    tests = [
        ("Load Environment", load_env_file),
        ("API Keys Present", verify_api_keys),
        ("OpenRouter API", test_openrouter_api),
        ("Google TTS Key", test_google_tts_key),
        ("Telegram Config", test_telegram_config),
        ("Flask Application", test_flask_app)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ {test_name} failed: {e}")
            results.append(False)
    
    print("\n" + "=" * 50)
    print("📊 Verification Summary:")
    
    for i, (test_name, _) in enumerate(tests):
        status = "✅ PASS" if results[i] else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    overall = all(results)
    print(f"\n🎯 Deployment Readiness: {'✅ READY TO DEPLOY' if overall else '❌ FIX ISSUES FIRST'}")
    
    if overall:
        print("\n🚀 All checks passed! Ready to run:")
        print("  ./deploy-with-keys.sh")
        print("\n💡 This will:")
        print("  - Create Google Cloud project")  
        print("  - Store your API keys in Secret Manager")
        print("  - Build and deploy container")
        print("  - Set up daily cron job")
    else:
        print("\n⚠️ Fix the issues above before deploying")
        print("Check your .env file and ensure all API keys are correct")

if __name__ == "__main__":
    main()