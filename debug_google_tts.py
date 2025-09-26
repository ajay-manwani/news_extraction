#!/usr/bin/env python3
"""
Local Google TTS Debug Test
Test the exact same Google TTS call that's failing in production
"""

import sys
import os
import requests
import json
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

def test_google_tts_api():
    """Test the exact Google TTS API call that's failing"""
    print("🧪 Testing Google TTS API Call")
    print("=" * 50)
    
    api_key = os.getenv("GOOGLE_CLOUD_TTS_API_KEY")
    if not api_key:
        print("❌ GOOGLE_CLOUD_TTS_API_KEY not found")
        return False
    
    print(f"✅ API Key found: {api_key[:20]}...")
    print()
    
    # Test with a short sample text first
    test_text = "Hello, this is a test of Google Text to Speech API."
    
    print("🎯 Testing with sample text:")
    print(f"   Text: {test_text}")
    print()
    
    # Prepare the request exactly like the production code
    url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={api_key}"
    
    headers = {
        'Content-Type': 'application/json',
    }
    
    # Test different payloads to identify the issue
    test_payloads = [
        {
            "input": {"text": test_text},
            "voice": {
                "languageCode": "en-US",
                "name": "en-US-Standard-F",
                "ssmlGender": "FEMALE"
            },
            "audioConfig": {
                "audioEncoding": "LINEAR16",
                "sampleRateHertz": 24000
            }
        },
        {
            "input": {"text": test_text},
            "voice": {
                "languageCode": "en-US",
                "ssmlGender": "FEMALE"
            },
            "audioConfig": {
                "audioEncoding": "MP3"
            }
        }
    ]
    
    for i, payload in enumerate(test_payloads, 1):
        print(f"🧪 Test {i}: {payload['voice'].get('name', 'Default voice')}")
        print(f"   Audio format: {payload['audioConfig']['audioEncoding']}")
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print("   ✅ SUCCESS!")
                audio_data = response.json().get('audioContent')
                if audio_data:
                    print(f"   📦 Audio data received: {len(audio_data)} characters (base64)")
                    
                    # Save a test file
                    import base64
                    audio_bytes = base64.b64decode(audio_data)
                    test_file = f"google_tts_test_{i}.{'wav' if payload['audioConfig']['audioEncoding'] == 'LINEAR16' else 'mp3'}"
                    with open(test_file, 'wb') as f:
                        f.write(audio_bytes)
                    print(f"   💾 Saved test file: {test_file}")
                return True
                
            else:
                print(f"   ❌ FAILED: {response.status_code}")
                print(f"   Error: {response.text}")
                
        except Exception as e:
            print(f"   💥 Exception: {str(e)}")
        
        print()
    
    return False

def test_production_tts_code():
    """Test using the actual production TTS code"""
    print("🔧 Testing Production TTS Code")
    print("=" * 50)
    
    try:
        from src.tts_generator import TTSGenerator
        from config.settings import get_config
        
        # Force production environment
        os.environ['ENVIRONMENT'] = 'production'
        config = get_config()
        
        print(f"📋 Environment: production")
        print(f"   USE_GOOGLE_TTS: {config.USE_GOOGLE_TTS}")
        print()
        
        tts = TTSGenerator()
        print(f"🎙️ TTS Generator initialized:")
        print(f"   Google TTS available: {tts.google_tts_available}")
        print(f"   Using API key: {getattr(tts, 'use_api_key', 'Unknown')}")
        print()
        
        if tts.google_tts_available:
            test_text = "Testing production TTS generator with short text."
            print(f"🧪 Testing with: {test_text}")
            
            # Test the exact method that's failing
            result = tts.generate_speech(test_text, use_premium=True)
            
            if result:
                print(f"   ✅ SUCCESS: {result}")
                print(f"   📁 File exists: {os.path.exists(result) if result else 'N/A'}")
            else:
                print("   ❌ FAILED: No result returned")
        else:
            print("   ❌ Google TTS not available")
            
    except Exception as e:
        print(f"💥 Error testing production code: {str(e)}")
        import traceback
        traceback.print_exc()

def main():
    print("🚀 Google TTS Debugging Session")
    print("=" * 60)
    print()
    
    # Test 1: Direct API call
    api_success = test_google_tts_api()
    print()
    
    # Test 2: Production TTS code
    test_production_tts_code()
    
    print("=" * 60)
    print("🏁 Debug session complete")

if __name__ == "__main__":
    main()