#!/usr/bin/env python3
"""
Test OpenRouter AI Summarization
Quick test to verify API connectivity and response
"""

import os
import sys
sys.path.append('/home/ajay/projects/news_extraction/news_extraction_prod')

from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/home/ajay/projects/news_extraction/.env')

def test_openrouter():
    """Test OpenRouter API connectivity"""
    api_key = os.getenv("OPENROUTER_API_KEY")
    print(f"API Key found: {'Yes' if api_key else 'No'}")
    
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found in environment")
        return False
    
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://github.com/ajay-manwani/news_extraction",
                "X-Title": "News Extraction Project"
            }
        )
        
        print("🔗 Testing connection to OpenRouter...")
        
        # Test with a simple prompt
        test_text = """
        Breaking News: Technology stocks surged today as investors showed renewed confidence 
        in the sector. Major companies reported strong quarterly earnings, with several 
        exceeding analyst expectations. The market rally was led by semiconductor and 
        software companies, reflecting optimism about future growth prospects.
        """
        
        response = client.chat.completions.create(
            model="openai/gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": f"Summarize this news article in 2-3 sentences: {test_text}"}
            ],
            max_tokens=150,
            temperature=0.7
        )
        
        summary = response.choices[0].message.content.strip()
        print(f"✅ API call successful!")
        print(f"📝 Summary received: {summary}")
        print(f"📊 Summary length: {len(summary)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ API call failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🧪 Testing OpenRouter AI Summarization...")
    success = test_openrouter()
    print(f"\n{'✅ Test PASSED' if success else '❌ Test FAILED'}")