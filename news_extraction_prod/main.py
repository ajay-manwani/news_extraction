"""
Daily News Extraction and Podcast Generation Service
Cloud Run Entry Point for Google Cloud Scheduler

This service processes RSS feeds, generates AI summaries, creates audio podcasts,
and delivers them via Telegram on a daily schedule.
"""

import os
import logging
from datetime import datetime
from flask import Flask, request, jsonify

# Configure logging for Cloud Run
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize Flask app for Cloud Run HTTP triggers
app = Flask(__name__)

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for Cloud Run"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'news-extraction-service'
    }), 200

@app.route('/process-news', methods=['POST'])
def process_daily_news():
    """
    Main endpoint triggered by Cloud Scheduler
    
    Expected to be called daily to:
    1. Fetch RSS feeds
    2. Extract and summarize content
    3. Generate audio podcast
    4. Deliver via Telegram
    """
    try:
        logger.info("🚀 Starting daily news processing pipeline")
        
        # Import configuration and run the pipeline
        from config.settings import get_config
        from src.news_pipeline import run_daily_pipeline
        
        config = get_config()
        result = run_daily_pipeline(config)
        
        # Determine HTTP status code based on result
        if result['status'] == 'success':
            status_code = 200
            logger.info(f"✅ Daily news processing completed successfully")
        else:
            status_code = 500
            logger.error(f"❌ Daily news processing failed: {result.get('error', 'Unknown error')}")
        
        return jsonify(result), status_code
        
    except Exception as e:
        error_msg = f"❌ News processing failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        return jsonify({
            'status': 'error',
            'message': error_msg,
            'timestamp': datetime.utcnow().isoformat(),
            'articles_processed': 0,
            'podcast_generated': False,
            'telegram_sent': False
        }), 500

@app.route('/', methods=['GET', 'POST'])
def index():
    """Default route - provides service information"""
    return jsonify({
        'service': 'Daily News Extraction Service',
        'version': '1.0.0',
        'endpoints': {
            'health': '/health',
            'process': '/process-news',
            'test': '/test-pipeline',
            'storage': '/storage-info',
            'cleanup': '/cleanup-storage'
        },
        'description': 'Automated news processing and podcast generation service',
        'timestamp': datetime.utcnow().isoformat()
    })

@app.route('/test-pipeline', methods=['GET'])
def test_pipeline():
    """Test endpoint to validate pipeline components without full execution"""
    try:
        logger.info("🧪 Testing pipeline components")
        
        from config.settings import get_config
        config = get_config()
        
        # Test each component
        test_results = {
            'config_loaded': False,
            'rss_sources': 0,
            'ai_summarizer': False,
            'tts_generator': False,
            'telegram_sender': False,
            'errors': []
        }
        
        # Test 1: Configuration
        try:
            sources = config.load_rss_sources()
            test_results['config_loaded'] = True
            test_results['rss_sources'] = len(sources)
        except Exception as e:
            test_results['errors'].append(f"Config test failed: {str(e)}")
        
        # Test 2: AI Summarizer
        try:
            from src.ai_summarizer import AISummarizer
            summarizer = AISummarizer()
            test_results['ai_summarizer'] = summarizer.api_available
        except Exception as e:
            test_results['errors'].append(f"AI summarizer test failed: {str(e)}")
        
        # Test 3: TTS Generator
        try:
            from src.tts_generator import TTSGenerator
            tts = TTSGenerator()
            # Test eSpeak availability
            import subprocess
            result = subprocess.run(['espeak', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            test_results['tts_generator'] = result.returncode == 0
        except Exception as e:
            test_results['errors'].append(f"TTS generator test failed: {str(e)}")
        
        # Test 4: Telegram Sender
        try:
            from src.telegram_sender import TelegramSender
            telegram = TelegramSender()
            test_results['telegram_sender'] = telegram.telegram_available
        except Exception as e:
            test_results['errors'].append(f"Telegram sender test failed: {str(e)}")
        
        # Overall status
        critical_components = ['config_loaded', 'tts_generator']
        all_critical_working = all(test_results[comp] for comp in critical_components)
        
        return jsonify({
            'status': 'success' if all_critical_working else 'warning',
            'message': 'Pipeline component test completed',
            'test_results': test_results,
            'critical_components_working': all_critical_working,
            'timestamp': datetime.utcnow().isoformat()
        }), 200 if all_critical_working else 206
        
    except Exception as e:
        logger.error(f"Pipeline test failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Pipeline test failed: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.route('/storage-info', methods=['GET'])
def storage_info():
    """Get Cloud Storage information and statistics"""
    try:
        logger.info("📊 Getting storage information")
        
        from config.settings import get_config
        from src.cloud_storage import CloudStorageManager
        
        config = get_config()
        storage_manager = CloudStorageManager(config)
        
        if not storage_manager.storage_available:
            return jsonify({
                'status': 'unavailable',
                'message': 'Cloud Storage not available',
                'available': False,
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        
        # Get storage statistics
        stats = storage_manager.get_storage_stats()
        
        # Get recent podcasts list
        recent_podcasts = storage_manager.list_podcasts(limit=10)
        
        return jsonify({
            'status': 'success',
            'storage_stats': stats,
            'recent_podcasts': recent_podcasts,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Storage info failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Storage info failed: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.route('/cleanup-storage', methods=['POST'])
def cleanup_storage():
    """Clean up old podcasts from Cloud Storage"""
    try:
        logger.info("🧹 Starting storage cleanup")
        
        from config.settings import get_config
        from src.cloud_storage import CloudStorageManager
        
        config = get_config()
        storage_manager = CloudStorageManager(config)
        
        if not storage_manager.storage_available:
            return jsonify({
                'status': 'unavailable',
                'message': 'Cloud Storage not available',
                'timestamp': datetime.utcnow().isoformat()
            }), 200
        
        # Perform cleanup
        cleanup_result = storage_manager.cleanup_old_podcasts()
        
        return jsonify({
            'status': 'success',
            'cleanup_result': cleanup_result,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Storage cleanup failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Storage cleanup failed: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.route('/test-tts', methods=['GET'])
def test_tts():
    """Test Google TTS connectivity"""
    try:
        from src.tts_generator import TTSGenerator
        
        tts = TTSGenerator()
        
        return jsonify({
            'status': 'success',
            'google_tts_available': tts.google_tts_available,
            'has_client': tts.google_client is not None,
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"TTS test failed: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'TTS test failed: {str(e)}',
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@app.route('/test-ai', methods=['GET'])
def test_ai():
    """Test OpenRouter AI connectivity"""
    try:
        from src.ai_summarizer import AISummarizer
        import os
        
        # Check if API key is loaded
        api_key = os.getenv("OPENROUTER_API_KEY")
        key_available = bool(api_key)
        key_preview = api_key[:12] + "..." if api_key else "None"
        
        # Initialize summarizer
        summarizer = AISummarizer()
        
        # Test with simple text
        test_text = "This is a simple test article about technology and AI development."
        
        try:
            summary = summarizer.summarize_article(test_text)
            ai_working = not summary.endswith("[Extractive summary - AI summarization unavailable]")
            
            return jsonify({
                'status': 'success',
                'api_key_available': key_available,
                'api_key_preview': key_preview,
                'summarizer_initialized': summarizer.api_available,
                'ai_summary_working': ai_working,
                'test_summary': summary[:100] + "..." if len(summary) > 100 else summary,
                'summary_length': len(summary),
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as summary_error:
            return jsonify({
                'status': 'partial',
                'api_key_available': key_available,
                'api_key_preview': key_preview,
                'summarizer_initialized': summarizer.api_available,
                'ai_summary_working': False,
                'summary_error': str(summary_error),
                'timestamp': datetime.utcnow().isoformat()
            })
        
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

if __name__ == '__main__':
    # For local testing
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)