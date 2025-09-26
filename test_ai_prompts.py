#!/usr/bin/env python3
"""
Test AI Summarizer Prompts Locally
Test the updated AI prompts with OpenRouter API if available
"""

import sys
import os
from datetime import datetime
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

def test_ai_summarizer():
    """Test the AI summarizer with sample content"""
    print("🤖 Testing AI Summarizer with Updated Prompts")
    print("=" * 60)
    
    try:
        from config.settings import get_config
        from src.ai_summarizer import AISummarizer
        import pandas as pd
        
        config = get_config()
        print(f"📋 Configuration loaded:")
        print(f"   - AI Model: {config.AI_MODEL}")
        print(f"   - Temperature: {config.TEMPERATURE}")
        print(f"   - Max Tokens: {config.MAX_TOKENS}")
        print()
        
        # Initialize summarizer
        summarizer = AISummarizer()
        print(f"🔗 AI API Available: {summarizer.api_available}")
        
        if not summarizer.api_available:
            print("❌ OpenRouter API not available - cannot test updated prompts")
            print("💡 To test AI prompts, set OPENROUTER_API_KEY environment variable")
            return False
        
        # Sample article content for testing
        sample_articles = [
            {
                'title': 'Tech Company Announces Major AI Breakthrough',
                'content': 'A leading technology company has announced a significant breakthrough in artificial intelligence research. The new system demonstrates unprecedented capabilities in natural language processing and reasoning. Industry experts believe this could revolutionize how we interact with AI systems.',
                'url': 'https://example.com/ai-breakthrough'
            },
            {
                'title': 'Global Climate Summit Reaches Historic Agreement',
                'content': 'World leaders have reached a historic agreement at the global climate summit, committing to aggressive carbon reduction targets. The agreement includes funding for developing nations and new technologies for clean energy transition.',
                'url': 'https://example.com/climate-summit'
            }
        ]
        
        print("📝 Testing individual article summarization...")
        print("-" * 40)
        
        for i, article in enumerate(sample_articles, 1):
            print(f"🔍 Article {i}: {article['title']}")
            
            # Test individual summary
            summary = summarizer.summarize_article(article['content'])
            print(f"📄 Original length: {len(article['content'])} characters")
            print(f"📝 Summary length: {len(summary)} characters")
            print(f"📋 Summary: {summary}")
            print()
        
        print("=" * 60)
        print("🧠 Testing meta-summary generation...")
        print("-" * 40)
        
        # Create DataFrame for meta-summary test
        df = pd.DataFrame([
            {
                'title': article['title'],
                'ai_summary': summarizer.summarize_article(article['content'])
            }
            for article in sample_articles
        ])
        
        # Test meta-summary
        meta_summary = summarizer.generate_meta_summary(df, 'ai_summary')
        print(f"📰 Meta-summary ({len(meta_summary)} characters):")
        print("-" * 30)
        print(meta_summary)
        print("-" * 30)
        
        return True
        
    except Exception as e:
        print(f"💥 Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test runner"""
    print(f"🕐 Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Check if OpenRouter API key is available
    api_key = os.getenv('OPENROUTER_API_KEY')
    if not api_key:
        print("⚠️ OPENROUTER_API_KEY not found in environment variables")
        print("   Your pipeline structure works, but AI prompts can't be tested locally")
        print("   without the API key.")
        print()
        print("💡 Options:")
        print("   1. Set OPENROUTER_API_KEY to test prompts locally")
        print("   2. Deploy to cloud where API key is available")
        print("   3. Continue with cloud deployment to test prompts there")
        print()
        return False
    
    success = test_ai_summarizer()
    
    print()
    print("=" * 60)
    print(f"🕐 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)