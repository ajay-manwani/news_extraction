#!/usr/bin/env python3
"""
Test Google TTS with Production-like Content
Test with long content similar to what production generates
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
sys.path.insert(0, '/home/ajay/projects/news_extraction/news_extraction_prod')

def test_with_long_content():
    """Test with content similar to production meta-summaries"""
    print("📰 Testing Google TTS with Production-like Content")
    print("=" * 60)
    
    try:
        from src.tts_generator import TTSGenerator
        
        # Force production environment
        os.environ['ENVIRONMENT'] = 'production'
        
        tts = TTSGenerator()
        
        # Simulate a long meta-summary like production generates
        long_content = """
        Welcome to today's news podcast for September 26th, 2025. Here are the top stories from around the world.

        In international news, tensions continue to rise in the Middle East as diplomatic talks have stalled. World leaders are calling for immediate ceasefire negotiations, while economic markets show volatility due to ongoing uncertainties.

        Technology sector updates include major announcements from several tech giants. Artificial intelligence developments are accelerating across multiple industries, with new applications in healthcare, finance, and transportation showing promising results.

        Climate and environmental news remains at the forefront, with new policies being implemented across European nations. Renewable energy investments have reached record highs this quarter, signaling a significant shift in global energy priorities.

        Economic indicators show mixed signals as inflation rates vary across different regions. Central banks are carefully monitoring market conditions while adjusting monetary policies to maintain economic stability.

        In sports, the autumn season brings exciting developments across major leagues. Championship races are heating up as teams prepare for the final stretch of their respective seasons.

        Cultural and entertainment highlights include several award-winning productions gaining international recognition. Film festivals and art exhibitions are showcasing diverse perspectives from emerging artists worldwide.

        Health and medical research continues to advance with breakthrough discoveries in cancer treatment and neurological disorders. Clinical trials are showing promising results for new therapeutic approaches.

        This concludes today's news summary. Thank you for listening, and we'll be back tomorrow with more updates from around the globe.
        """.strip()
        
        print(f"📄 Content length: {len(long_content)} characters")
        print(f"📝 Content preview: {long_content[:200]}...")
        print()
        
        # Test with various chunk sizes
        test_sizes = [
            ("Full content", long_content),
            ("First 1000 chars", long_content[:1000]),
            ("First 500 chars", long_content[:500]),
            ("First paragraph", long_content.split('\n\n')[1])  # Get first paragraph
        ]
        
        for test_name, content in test_sizes:
            print(f"🧪 Testing: {test_name} ({len(content)} chars)")
            
            try:
                result = tts.generate_speech(content, use_premium=True)
                
                if result:
                    file_size = os.path.getsize(result) if os.path.exists(result) else 0
                    print(f"   ✅ SUCCESS: {result}")
                    print(f"   📏 File size: {file_size / 1024:.1f} KB")
                else:
                    print(f"   ❌ FAILED: No result returned")
                    
            except Exception as e:
                print(f"   💥 ERROR: {str(e)}")
            
            print()
        
        # Test with special characters and formatting
        special_content = """
        Here's a test with special characters: "quotes", 'apostrophes', & symbols, 
        numbers like 2025, percentages 15%, and currency $100. 
        Also testing: em-dashes — en-dashes – and ellipses...
        Plus some unicode: café, naïve, résumé.
        """
        
        print("🔤 Testing with special characters:")
        print(f"   Content: {special_content.strip()}")
        
        try:
            result = tts.generate_speech(special_content, use_premium=True)
            if result:
                print(f"   ✅ SUCCESS with special chars: {result}")
            else:
                print("   ❌ FAILED with special characters")
        except Exception as e:
            print(f"   💥 ERROR with special chars: {str(e)}")
            
    except Exception as e:
        print(f"💥 Setup error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_with_long_content()