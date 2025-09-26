#!/usr/bin/env python3
"""
Local Pipeline Test Runner
Run the complete news extraction pipeline locally to test AI prompt updates
"""

import sys
import os
import json
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

def main():
    """Run the complete news pipeline locally"""
    print("🚀 Starting Local News Pipeline Test")
    print("=" * 60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        # Import configuration and pipeline
        from config.settings import get_config
        from src.news_pipeline import run_daily_pipeline
        
        print("📋 Loading configuration...")
        config = get_config()
        print(f"✅ Configuration loaded successfully")
        print(f"   - RSS sources: {len(config.load_rss_sources())} configured")
        print(f"   - AI Model: {config.AI_MODEL}")
        print(f"   - Temperature: {config.TEMPERATURE}")
        print()
        
        print("🔄 Running complete pipeline...")
        print("-" * 40)
        
        # Run the pipeline
        result = run_daily_pipeline(config)
        
        print("-" * 40)
        print("📊 Pipeline Results:")
        print("=" * 60)
        
        if result['status'] == 'success':
            print("✅ Status: SUCCESS")
            print(f"📈 Processing time: {result['processing_duration_seconds']:.1f} seconds")
            print(f"📰 Articles processed: {result['articles_processed']}")
            
            # Show statistics
            stats = result['statistics']
            print()
            print("📊 Detailed Statistics:")
            print(f"   - Articles fetched: {stats.get('articles_fetched', 0)}")
            print(f"   - Articles with content: {stats.get('articles_with_content', 0)}")
            print(f"   - After deduplication: {stats.get('articles_after_deduplication', 0)}")
            print(f"   - AI summaries generated: {stats.get('ai_summaries_generated', 0)}")
            print(f"   - Duplicates removed: {stats.get('duplicates_removed', 0)}")
            print(f"   - Podcast created: {stats.get('podcast_created', False)}")
            print(f"   - Telegram sent: {stats.get('telegram_sent', False)}")
            
            # Show meta-summary preview
            meta_summary = result['meta_summary']
            print()
            print("📝 Generated Meta-Summary:")
            print("-" * 30)
            print(meta_summary[:500] + ("..." if len(meta_summary) > 500 else ""))
            print("-" * 30)
            
            # Show podcast info
            podcast_info = result.get('podcast', {})
            if podcast_info:
                print()
                print("🎙️ Podcast Information:")
                print(f"   - Local file: {podcast_info.get('local_file', 'N/A')}")
                print(f"   - Duration: {podcast_info.get('duration_minutes', 'N/A')} minutes")
                print(f"   - File size: {podcast_info.get('file_size_mb', 'N/A')} MB")
                if 'cloud_url' in podcast_info:
                    print(f"   - Cloud URL: {podcast_info['cloud_url']}")
            
            # Show telegram result
            telegram_result = result.get('telegram_result', {})
            print()
            print("📱 Telegram Delivery:")
            if telegram_result.get('podcast_sent'):
                print("   ✅ Podcast sent successfully")
            elif telegram_result.get('text_sent'):
                print("   ✅ Text summary sent successfully")
            else:
                print("   ⚠️ Delivery not completed or failed")
            
        else:
            print("❌ Status: ERROR")
            print(f"Error: {result.get('error', 'Unknown error')}")
            
            # Show any statistics collected before failure
            stats = result.get('statistics', {})
            if stats:
                print()
                print("📊 Statistics before failure:")
                for key, value in stats.items():
                    if key != 'errors':
                        print(f"   - {key}: {value}")
                
                # Show errors
                errors = stats.get('errors', [])
                if errors:
                    print()
                    print("🚨 Errors encountered:")
                    for i, error in enumerate(errors, 1):
                        print(f"   {i}. {error}")
        
        print()
        print("=" * 60)
        print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Save detailed results to file
        output_file = f"pipeline_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, default=str)
        print(f"📄 Detailed results saved to: {output_file}")
        
        return result['status'] == 'success'
        
    except Exception as e:
        print(f"💥 Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)