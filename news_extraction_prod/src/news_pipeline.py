"""
News Processing Pipeline
Main orchestrator that combines all modules into a complete pipeline
"""

import logging
import pandas as pd
from datetime import datetime
from typing import Dict, List, Any, Optional

from .rss_fetcher import fetch_all_sources
from .content_extractor import extract_content_batch
from .ai_summarizer import AISummarizer, process_article_summaries
from .deduplicator import remove_duplicates
from .tts_generator import generate_podcast
from .telegram_sender import send_daily_podcast

logger = logging.getLogger(__name__)

class NewsProcessor:
    """Main news processing pipeline coordinator"""
    
    def __init__(self, config):
        self.config = config
        self.stats = {
            'start_time': None,
            'end_time': None,
            'processing_duration': 0,
            'articles_fetched': 0,
            'articles_with_content': 0,
            'articles_after_deduplication': 0,
            'duplicates_removed': 0,
            'ai_summaries_generated': 0,
            'podcast_created': False,
            'telegram_sent': False,
            'errors': []
        }
    
    def run_daily_pipeline(self) -> Dict[str, Any]:
        """
        Execute the complete daily news processing pipeline
        
        Returns:
            dict: Complete results and statistics
        """
        self.stats['start_time'] = datetime.utcnow()
        logger.info("🚀 Starting daily news processing pipeline")
        
        try:
            # Step 1: Fetch RSS feeds
            articles = self._fetch_articles()
            if not articles:
                return self._finish_with_error("No articles fetched from RSS feeds")
            
            # Step 2: Extract full content
            articles = self._extract_content(articles)
            
            # Step 3: Remove duplicates
            dedup_result = self._deduplicate_articles(articles)
            articles = dedup_result['articles']
            
            if not articles:
                return self._finish_with_error("No articles remaining after deduplication")
            
            # Step 4: Generate AI summaries
            articles = self._generate_summaries(articles)
            
            # Step 5: Create meta-summary
            meta_summary = self._create_meta_summary(articles)
            
            # Step 6: Generate podcast
            podcast_result = self._generate_podcast(meta_summary)
            
            # Step 7: Send via Telegram
            telegram_result = self._send_telegram(podcast_result, meta_summary)
            
            # Finalize results
            return self._finish_successfully(articles, meta_summary, podcast_result, telegram_result)
            
        except Exception as e:
            logger.error(f"Pipeline failed with exception: {str(e)}", exc_info=True)
            return self._finish_with_error(f"Pipeline exception: {str(e)}")
    
    def _fetch_articles(self) -> List[Dict]:
        """Fetch articles from all RSS sources"""
        try:
            logger.info("📡 Fetching RSS feeds...")
            sources = self.config.load_rss_sources()
            articles = fetch_all_sources(sources)
            
            self.stats['articles_fetched'] = len(articles)
            logger.info(f"✅ Fetched {len(articles)} articles from RSS feeds")
            
            return articles
            
        except Exception as e:
            error_msg = f"RSS fetching failed: {str(e)}"
            self.stats['errors'].append(error_msg)
            logger.error(error_msg)
            return []
    
    def _extract_content(self, articles: List[Dict]) -> List[Dict]:
        """Extract full content from article URLs"""
        try:
            logger.info("📖 Extracting article content...")
            articles_with_content = extract_content_batch(articles)
            
            # Count successful extractions
            successful = sum(1 for a in articles_with_content if a.get('extraction_successful', False))
            self.stats['articles_with_content'] = successful
            
            logger.info(f"✅ Content extracted: {successful}/{len(articles)} successful")
            
            return articles_with_content
            
        except Exception as e:
            error_msg = f"Content extraction failed: {str(e)}"
            self.stats['errors'].append(error_msg)
            logger.error(error_msg)
            return articles  # Return original articles if extraction fails
    
    def _deduplicate_articles(self, articles: List[Dict]) -> Dict:
        """Remove duplicate articles"""
        try:
            logger.info("🔍 Removing duplicate articles...")
            dedup_result = remove_duplicates(
                articles, 
                similarity_threshold=self.config.DUPLICATE_THRESHOLD
            )
            
            self.stats['articles_after_deduplication'] = len(dedup_result['articles'])
            self.stats['duplicates_removed'] = dedup_result['deduplication_stats']['duplicates_removed']
            
            logger.info(f"✅ Deduplication complete: {len(dedup_result['articles'])} articles remaining, "
                       f"{self.stats['duplicates_removed']} duplicates removed")
            
            return dedup_result
            
        except Exception as e:
            error_msg = f"Deduplication failed: {str(e)}"
            self.stats['errors'].append(error_msg)
            logger.error(error_msg)
            return {'articles': articles, 'deduplication_stats': {'duplicates_removed': 0}}
    
    def _generate_summaries(self, articles: List[Dict]) -> List[Dict]:
        """Generate AI summaries for all articles"""
        try:
            logger.info("🤖 Generating AI summaries...")
            articles_with_summaries = process_article_summaries(articles)
            
            # Count successful AI summaries (not fallback summaries)
            ai_summaries = sum(1 for a in articles_with_summaries 
                             if a.get('ai_summary', '').strip() and 
                             'AI summarization unavailable' not in a.get('ai_summary', ''))
            
            self.stats['ai_summaries_generated'] = ai_summaries
            
            logger.info(f"✅ Summaries generated: {ai_summaries} AI summaries, "
                       f"{len(articles_with_summaries) - ai_summaries} fallback summaries")
            
            return articles_with_summaries
            
        except Exception as e:
            error_msg = f"Summary generation failed: {str(e)}"
            self.stats['errors'].append(error_msg)
            logger.error(error_msg)
            return articles
    
    def _create_meta_summary(self, articles: List[Dict]) -> str:
        """Create meta-summary from all article summaries"""
        try:
            logger.info("📝 Creating meta-summary...")
            
            # Convert to DataFrame for the summarizer
            df = pd.DataFrame(articles)
            
            # Generate meta-summary
            summarizer = AISummarizer()
            meta_summary = summarizer.generate_meta_summary(df, 'ai_summary')
            
            logger.info(f"✅ Meta-summary created: {len(meta_summary)} characters")
            
            return meta_summary
            
        except Exception as e:
            error_msg = f"Meta-summary creation failed: {str(e)}"
            self.stats['errors'].append(error_msg)
            logger.error(error_msg)
            
            # Fallback meta-summary
            return f"Daily news summary for {datetime.now().strftime('%B %d, %Y')} - {len(articles)} articles processed."
    
    def _generate_podcast(self, meta_summary: str) -> Optional[Dict]:
        """Generate audio podcast from meta-summary"""
        try:
            logger.info("🎙️ Generating podcast...")
            
            podcast_filename = f"daily_news_{datetime.now().strftime('%Y%m%d')}.mp3"
            
            podcast_result = generate_podcast(
                content=meta_summary,
                output_file=podcast_filename,
                voice_preset="female_natural",
                use_premium=self.config.USE_GOOGLE_TTS,
                upload_to_cloud=True,  # Enable cloud storage
                config=self.config
            )
            
            if podcast_result and podcast_result.get('success'):
                self.stats['podcast_created'] = True
                logger.info(f"✅ Podcast created: {podcast_result['local_file']}")
                
                # Log cloud storage result if available
                cloud_result = podcast_result.get('cloud_storage')
                if cloud_result and cloud_result.get('success'):
                    logger.info(f"☁️ Uploaded to cloud: {cloud_result['public_url']}")
                elif cloud_result:
                    logger.warning(f"⚠️ Cloud upload failed: {cloud_result.get('error')}")
            else:
                logger.error("❌ Podcast generation failed")
                self.stats['errors'].append("Podcast generation failed")
            
            return podcast_result
            
        except Exception as e:
            error_msg = f"Podcast generation failed: {str(e)}"
            self.stats['errors'].append(error_msg)
            logger.error(error_msg)
            return None
    
    def _send_telegram(self, podcast_result: Optional[Dict], meta_summary: str) -> Dict[str, Any]:
        """Send podcast via Telegram"""
        try:
            logger.info("📱 Sending via Telegram...")
            
            if podcast_result and podcast_result.get('success'):
                # Use cloud URL if available, otherwise local file
                cloud_result = podcast_result.get('cloud_storage')
                if cloud_result and cloud_result.get('success'):
                    # Send cloud URL instead of file for better performance
                    podcast_url = cloud_result['public_url']
                    logger.info(f"Using cloud URL for Telegram: {podcast_url}")
                    
                    # For now, still send local file - could be enhanced to send URL
                    telegram_result = send_daily_podcast(
                        podcast_result['local_file'], 
                        meta_summary
                    )
                else:
                    telegram_result = send_daily_podcast(
                        podcast_result['local_file'], 
                        meta_summary
                    )
            else:
                # Send text-only if no podcast
                from .telegram_sender import TelegramSender
                sender = TelegramSender()
                telegram_result = sender.send_text_summary_sync(meta_summary)
                telegram_result = {
                    'podcast_sent': False,
                    'text_sent': telegram_result['success'],
                    'primary_method': 'text' if telegram_result['success'] else 'failed',
                    'details': telegram_result
                }
            
            if telegram_result.get('podcast_sent') or telegram_result.get('text_sent'):
                self.stats['telegram_sent'] = True
                logger.info("✅ Telegram delivery successful")
            else:
                logger.warning("⚠️ Telegram delivery failed or not configured")
            
            return telegram_result
            
        except Exception as e:
            error_msg = f"Telegram sending failed: {str(e)}"
            self.stats['errors'].append(error_msg)
            logger.error(error_msg)
            return {
                'podcast_sent': False,
                'text_sent': False,
                'primary_method': 'failed',
                'error': str(e)
            }
    
    def _finish_successfully(self, articles: List[Dict], meta_summary: str, 
                           podcast_result: Optional[Dict], telegram_result: Dict) -> Dict[str, Any]:
        """Finalize successful pipeline execution"""
        self.stats['end_time'] = datetime.utcnow()
        self.stats['processing_duration'] = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        # Extract podcast info
        podcast_info = {}
        if podcast_result and podcast_result.get('success'):
            podcast_info = {
                'local_file': podcast_result.get('local_file'),
                'duration_minutes': podcast_result.get('duration_minutes'),
                'file_size_mb': podcast_result.get('file_size_mb')
            }
            
            # Add cloud storage info if available
            cloud_result = podcast_result.get('cloud_storage')
            if cloud_result and cloud_result.get('success'):
                podcast_info['cloud_url'] = cloud_result.get('public_url')
                podcast_info['cloud_filename'] = cloud_result.get('cloud_filename')
        
        result = {
            'status': 'success',
            'timestamp': self.stats['end_time'].isoformat(),
            'processing_duration_seconds': self.stats['processing_duration'],
            'articles_processed': len(articles),
            'meta_summary': meta_summary,
            'podcast': podcast_info,
            'telegram_result': telegram_result,
            'statistics': self.stats
        }
        
        logger.info(f"🎉 Pipeline completed successfully in {self.stats['processing_duration']:.1f} seconds")
        logger.info(f"📊 Final stats: {self.stats['articles_fetched']} fetched → "
                   f"{self.stats['articles_after_deduplication']} after dedup → "
                   f"{self.stats['ai_summaries_generated']} AI summaries → "
                   f"{'✅' if self.stats['podcast_created'] else '❌'} podcast → "
                   f"{'✅' if self.stats['telegram_sent'] else '❌'} telegram")
        
        return result
    
    def _finish_with_error(self, error_message: str) -> Dict[str, Any]:
        """Finalize pipeline with error state"""
        self.stats['end_time'] = datetime.utcnow()
        if self.stats['start_time']:
            self.stats['processing_duration'] = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        
        self.stats['errors'].append(error_message)
        
        result = {
            'status': 'error',
            'timestamp': self.stats['end_time'].isoformat(),
            'error': error_message,
            'processing_duration_seconds': self.stats['processing_duration'],
            'statistics': self.stats
        }
        
        logger.error(f"❌ Pipeline failed: {error_message}")
        return result

def run_daily_pipeline(config) -> Dict[str, Any]:
    """
    Main entry point for running the complete daily news pipeline
    
    Args:
        config: Configuration object with all necessary settings
        
    Returns:
        dict: Complete pipeline results
    """
    processor = NewsProcessor(config)
    return processor.run_daily_pipeline()