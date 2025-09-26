#!/usr/bin/env python3
"""
Local Google TTS Test
Test Google Cloud TTS API with your API key to see if it works locally
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

def test_google_tts():
    """Test Google TTS API locally"""
    print("🎙️ Testing Google Cloud TTS Locally")
    print("=" * 50)
    
    # Check API key
    api_key = os.getenv('GOOGLE_CLOUD_TTS_API_KEY')
    print(f"📋 API Key Found: {'✅ Yes' if api_key else '❌ No'}")
    if api_key:
        print(f"   Key Preview: {api_key[:20]}...")
    print()
    
    try:
        from src.tts_generator import TTSGenerator
        
        print("🔧 Initializing TTS Generator...")
        tts = TTSGenerator()
        
        print(f"   - Google TTS Available: {'✅ Yes' if tts.google_tts_available else '❌ No'}")
        print(f"   - Using API Key Method: {'✅ Yes' if getattr(tts, 'use_api_key', False) else '❌ No'}")
        print(f"   - API Key Set: {'✅ Yes' if getattr(tts, 'api_key', None) else '❌ No'}")
        print()
        
        if not tts.google_tts_available:
            print("❌ Google TTS not available - cannot test")
            return False
        
        # Test short text
        test_text = "Hello, this is a test of Google Cloud Text to Speech. The quality should be much better than eSpeak."
        
        print("🧪 Testing Google TTS with sample text...")
        print(f"📝 Test Text: {test_text}")
        print()
        
        try:
            print("⏳ Generating speech with Google TTS...")
            result_file = tts.generate_speech(test_text, use_premium=True)
            
            if result_file and os.path.exists(result_file):
                file_size = os.path.getsize(result_file)
                print(f"✅ SUCCESS: Google TTS generated audio file")
                print(f"   📁 File: {result_file}")
                print(f"   📊 Size: {file_size} bytes")
                
                # Try to get additional info
                import subprocess
                try:
                    result = subprocess.run(['file', result_file], capture_output=True, text=True)
                    print(f"   🔍 File Type: {result.stdout.strip()}")
                except:
                    pass
                
                return True
            else:
                print("❌ Google TTS failed - no file generated")
                return False
                
        except Exception as e:
            print(f"❌ Google TTS Error: {str(e)}")
            print()
            
            # Try to get more details
            import traceback
            print("🔍 Detailed Error:")
            traceback.print_exc()
            return False
            
    except Exception as e:
        print(f"❌ TTS Generator initialization failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("🕐 Google TTS Local Test Started")
    print()
    
    success = test_google_tts()
    
    print()
    print("=" * 50)
    if success:
        print("🎉 Google TTS is working locally!")
        print("   The issue is likely in the Cloud Run environment setup.")
    else:
        print("❌ Google TTS failed locally too.")
        print("   This suggests an issue with the API key or configuration.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)