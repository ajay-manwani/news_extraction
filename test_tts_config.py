#!/usr/bin/env python3
"""
Test TTS Configuration
Check why Google TTS is not being used locally
"""

import sys
import os
from pathlib import Path

# Load environment variables from .env file
def load_env():
    env_path = Path('/home/ajay/projects/news_extraction/.env')
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.strip().split('=', 1)
                    os.environ[key] = value

load_env()

# Add the production source to Python path
sys.path.insert(0, '/home/ajay/projects/news_extraction/news_extraction_prod')

def test_tts_config():
    """Test TTS configuration and see why Google TTS isn't working"""
    print("🔍 TTS Configuration Debug")
    print("=" * 50)
    
    # Check environment variables
    print("📋 Environment Variables:")
    google_tts_key = os.getenv("GOOGLE_CLOUD_TTS_API_KEY")
    google_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    
    print(f"   - GOOGLE_CLOUD_TTS_API_KEY: {'✅ Present' if google_tts_key else '❌ Missing'}")
    if google_tts_key:
        print(f"     Key preview: {google_tts_key[:20]}...")
    
    print(f"   - GOOGLE_APPLICATION_CREDENTIALS: {'✅ Present' if google_creds else '❌ Missing'}")
    if google_creds:
        print(f"     Path: {google_creds}")
        print(f"     File exists: {'✅ Yes' if os.path.exists(google_creds) else '❌ No'}")
    
    print()
    
    # Check configuration
    try:
        from config.settings import get_config
        config = get_config()
        print("⚙️ Configuration Settings:")
        print(f"   - USE_GOOGLE_TTS: {config.USE_GOOGLE_TTS}")
        print(f"   - GOOGLE_TTS_VOICE: {config.GOOGLE_TTS_VOICE}")
        print()
    except Exception as e:
        print(f"❌ Config load error: {e}")
        return
    
    # Test TTS initialization
    try:
        from src.tts_generator import TTSGenerator
        print("🎙️ TTS Generator Test:")
        
        tts = TTSGenerator()
        print(f"   - Google TTS Available: {tts.google_tts_available}")
        print(f"   - Using API Key: {getattr(tts, 'use_api_key', 'Unknown')}")
        
        if hasattr(tts, 'google_client'):
            print(f"   - Google Client: {'✅ Initialized' if tts.google_client else '❌ None'}")
        
        if hasattr(tts, 'api_key'):
            print(f"   - API Key Set: {'✅ Yes' if tts.api_key else '❌ No'}")
        
        print()
        
        # Test a small speech generation
        print("🧪 Testing Speech Generation:")
        test_text = "Hello, this is a test of the text to speech system."
        
        # Test with premium (should use Google TTS)
        print("   Testing with use_premium=True...")
        try:
            result_premium = tts.generate_speech(test_text, use_premium=True)
            print(f"   - Premium result: {'✅ Success' if result_premium else '❌ Failed'}")
            if result_premium:
                print(f"     File: {result_premium}")
        except Exception as e:
            print(f"   - Premium error: {e}")
        
        # Test without premium (should use eSpeak)
        print("   Testing with use_premium=False...")
        try:
            result_basic = tts.generate_speech(test_text, use_premium=False)
            print(f"   - Basic result: {'✅ Success' if result_basic else '❌ Failed'}")
            if result_basic:
                print(f"     File: {result_basic}")
        except Exception as e:
            print(f"   - Basic error: {e}")
            
    except Exception as e:
        print(f"❌ TTS test error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_tts_config()