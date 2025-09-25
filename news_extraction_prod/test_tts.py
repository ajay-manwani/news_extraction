#!/usr/bin/env python3
"""
Quick test to verify Google TTS is working
"""
import os
import sys
sys.path.append('/app')

try:
    from src.tts_generator import TTSGenerator
    
    # Create TTS instance
    tts = TTSGenerator()
    
    print(f"Google TTS Available: {tts.google_tts_available}")
    print(f"Google Client: {tts.google_client}")
    
    if tts.google_tts_available:
        print("✅ Google TTS is working!")
        # Try a quick synthesis test
        test_text = "Hello, this is a test of Google Text-to-Speech."
        result = tts.generate_speech(test_text, use_premium=True)
        print(f"Test synthesis result: {result}")
    else:
        print("❌ Google TTS not available - will use eSpeak")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()