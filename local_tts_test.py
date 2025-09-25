#!/usr/bin/env python3
"""
Local TTS Test Script
Debug Google TTS integration locally before deploying
"""

import os
import sys
sys.path.append('/home/ajay/projects/news_extraction/news_extraction_prod')

def test_tts_initialization():
    """Test TTS initialization locally"""
    print("🔧 Testing TTS Initialization Locally...")
    
    try:
        from src.tts_generator import TTSGenerator
        print("✅ TTSGenerator imported successfully")
        
        # Create instance
        tts = TTSGenerator()
        print(f"📊 Google TTS Available: {tts.google_tts_available}")
        print(f"📊 Has Google Client: {tts.google_client is not None}")
        
        # Check environment variables
        print("\n🔍 Environment Check:")
        print(f"   GOOGLE_APPLICATION_CREDENTIALS: {os.getenv('GOOGLE_APPLICATION_CREDENTIALS', 'Not set')}")
        print(f"   GOOGLE_CLOUD_PROJECT: {os.getenv('GOOGLE_CLOUD_PROJECT', 'Not set')}")
        
        # Check if Google TTS library is available
        try:
            from google.cloud import texttospeech
            print("✅ google-cloud-texttospeech library is available")
        except ImportError as e:
            print(f"❌ google-cloud-texttospeech library import failed: {e}")
        
        if tts.google_tts_available:
            print("\n🎤 Testing Google TTS synthesis...")
            test_text = "Hello, this is a local test of Google Text-to-Speech."
            result = tts.generate_speech(test_text, use_premium=True)
            if result:
                print(f"✅ Google TTS synthesis successful: {result}")
            else:
                print("❌ Google TTS synthesis failed")
        else:
            print("\n🎤 Testing eSpeak fallback...")
            test_text = "Hello, this is a test of eSpeak synthesis."
            result = tts.generate_speech(test_text, use_premium=False)
            if result:
                print(f"✅ eSpeak synthesis successful: {result}")
            else:
                print("❌ eSpeak synthesis failed")
                
    except Exception as e:
        print(f"❌ Error during TTS test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_tts_initialization()