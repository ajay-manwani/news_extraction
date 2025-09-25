#!/usr/bin/env python3
"""
Test configuration loading and dependencies
"""

import sys
import os
sys.path.append('/home/ajay/projects/news_extraction/news_extraction_prod')

def test_configuration():
    print("🧪 Testing Configuration and Dependencies")
    print("=" * 50)
    
    # Test 1: Configuration loading
    try:
        print("\n1️⃣ Testing configuration loading...")
        from config.settings import get_config, Config
        
        config = get_config()
        print(f"   ✅ Config loaded successfully")
        print(f"   Environment: {os.getenv('ENVIRONMENT', 'development')}")
        print(f"   Project ID: {config.PROJECT_ID}")
        print(f"   Use Google TTS: {config.USE_GOOGLE_TTS}")
        
    except Exception as e:
        print(f"   ❌ Configuration ERROR: {e}")
        return False
    
    # Test 2: RSS Sources loading
    try:
        print("\n2️⃣ Testing RSS sources loading...")
        sources = config.load_rss_sources()
        print(f"   ✅ RSS sources loaded: {len(sources)} sources")
        for name, info in sources.items():
            print(f"   - {name}: {info.get('enabled', True)}")
            
    except Exception as e:
        print(f"   ❌ RSS sources ERROR: {e}")
    
    # Test 3: Required imports
    try:
        print("\n3️⃣ Testing core dependencies...")
        
        import feedparser
        print(f"   ✅ feedparser: {feedparser.__version__}")
        
        import pandas as pd
        print(f"   ✅ pandas: {pd.__version__}")
        
        import requests
        print(f"   ✅ requests: {requests.__version__}")
        
        import flask
        print(f"   ✅ flask: {flask.__version__}")
        
        try:
            import pydub
            print(f"   ✅ pydub: available")
        except:
            print(f"   ⚠️ pydub: not available (needs ffmpeg)")
        
        # Test eSpeak availability
        import subprocess
        try:
            result = subprocess.run(['espeak', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                print(f"   ✅ eSpeak: available")
            else:
                print(f"   ⚠️ eSpeak: command failed")
        except:
            print(f"   ⚠️ eSpeak: not found (needed for TTS)")
            
    except Exception as e:
        print(f"   ❌ Dependencies ERROR: {e}")
    
    # Test 4: Environment variables (safe check)
    print("\n4️⃣ Testing environment setup...")
    env_vars = [
        'OPENAI_API_KEY', 'GOOGLE_TTS_API_KEY', 
        'TELEGRAM_BOT_TOKEN', 'TELEGRAM_CHAT_ID'
    ]
    
    for var in env_vars:
        value = os.getenv(var)
        if value:
            print(f"   ✅ {var}: configured")
        else:
            print(f"   ⚠️ {var}: not set (needed for production)")
    
    print("\n🎉 Configuration Test Complete!")
    return True

if __name__ == "__main__":
    test_configuration()