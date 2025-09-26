"""
Configuration management for News Extraction Service
"""

import os
import yaml
from pathlib import Path

# Base configuration
class Config:
    """Base configuration class"""
    
    # Google Cloud settings
    PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT', 'news-extraction-project')
    CLOUD_STORAGE_BUCKET = os.getenv('CLOUD_STORAGE_BUCKET', 'news-podcasts-bucket')
    
    # API Keys (to be retrieved from Secret Manager in production)
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')  # Added for OpenRouter
    GOOGLE_CLOUD_TTS_API_KEY = os.getenv('GOOGLE_CLOUD_TTS_API_KEY')  # Updated key name
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_HTTP_API_KEY')  # Map to your key name
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    # OpenAI/OpenRouter settings
    OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
    AI_MODEL = "x-ai/grok-4-fast:free"  # Same model as tested in notebook
    MAX_TOKENS = 1000
    TEMPERATURE = 0.7
    
    # TTS settings
    USE_GOOGLE_TTS = True  # Default to Google TTS for quality
    GOOGLE_TTS_VOICE = "en-US-Standard-F"  # Standard voice (cheaper than Neural)
    ESPEAK_VOICE = "en+f3"  # Fallback voice
    SPEAKING_RATE = 1.0
    PITCH = -1.0
    
    # Processing settings
    MAX_ARTICLES_PER_SOURCE = 50
    CONTENT_EXTRACTION_TIMEOUT = 30
    AI_REQUEST_TIMEOUT = 60
    DUPLICATE_THRESHOLD = 0.8
    
    # Storage settings
    PODCAST_RETENTION_DAYS = 1  # Keep only 1 day to save storage and memory
    MAX_PODCAST_SIZE_MB = 25  # Telegram file size limit
    
    @classmethod
    def load_rss_sources(cls):
        """Load RSS sources from configuration file"""
        config_path = Path(__file__).parent / 'sources.yaml'
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        else:
            # Default sources if config file doesn't exist
            return {
                'economic_times': {
                    'rss': 'https://economictimes.indiatimes.com/rssfeedsdefault.cms',
                    'categories': ['business', 'economy', 'india']
                },
                'times_of_india': {
                    'rss': 'https://timesofindia.indiatimes.com/rssfeedstopstories.cms',
                    'categories': ['general', 'india', 'politics']
                },
                'techcrunch': {
                    'rss': 'http://feeds.feedburner.com/TechCrunch/',
                    'categories': ['technology', 'startups', 'global']
                }
            }

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    USE_GOOGLE_TTS = False  # Use eSpeak for development to save costs

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    USE_GOOGLE_TTS = True

# Configuration selector
def get_config():
    """Get configuration based on environment"""
    env = os.getenv('ENVIRONMENT', 'development').lower()
    
    if env == 'production':
        return ProductionConfig()
    else:
        return DevelopmentConfig()