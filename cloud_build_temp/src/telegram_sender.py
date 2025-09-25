"""
Telegram Integration Module
H        # Get credentials from environment
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_HTTP_API_KEY")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")dles sending podcast files via Telegram bot
"""

import os
import logging
from typing import Optional, Dict, Any

try:
    import telegram
    from telegram import Bot
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False

logger = logging.getLogger(__name__)

class TelegramSender:
    """Telegram bot for sending news podcasts"""
    
    def __init__(self):
        self.bot = None
        self.chat_id = None
        self.telegram_available = False
        self._initialize_bot()
    
    def _initialize_bot(self):
        """Initialize Telegram bot if credentials are available"""
        if not TELEGRAM_AVAILABLE:
            logger.warning("python-telegram-bot library not available")
            return
        
        # Try both environment variable names
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN") or os.getenv("TELEGRAM_HTTP_API_KEY")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        
        if bot_token and self.chat_id:
            try:
                # Remove any trailing whitespace (similar to OpenRouter fix)
                bot_token = bot_token.strip()
                self.chat_id = self.chat_id.strip()
                
                # Create bot with longer timeout for file uploads
                from telegram.request import HTTPXRequest
                request = HTTPXRequest(connection_pool_size=1, read_timeout=60, write_timeout=60)
                self.bot = Bot(token=bot_token, request=request)
                self.telegram_available = True
                logger.info(f"Telegram bot initialized successfully for chat: {self.chat_id}")
            except Exception as e:
                logger.error(f"Failed to initialize Telegram bot: {str(e)}")
                self.telegram_available = False
        else:
            logger.warning("TELEGRAM_BOT_TOKEN/TELEGRAM_HTTP_API_KEY or TELEGRAM_CHAT_ID not found - Telegram sending disabled")
            self.telegram_available = False
    
    async def send_podcast(self, podcast_file: str, caption: str = None) -> Dict[str, Any]:
        """
        Send podcast file via Telegram
        
        Args:
            podcast_file (str): Path to the podcast MP3 file
            caption (str): Optional caption for the audio message
            
        Returns:
            dict: Result of the send operation
        """
        if not self.telegram_available:
            return {
                'success': False,
                'error': 'Telegram not available - missing credentials or library',
                'fallback_used': True
            }
        
        if not os.path.exists(podcast_file):
            return {
                'success': False,
                'error': f'Podcast file not found: {podcast_file}',
                'fallback_used': False
            }
        
        try:
            logger.info(f"Sending podcast via Telegram: {podcast_file}")
            
            # Check file size (Telegram limit is ~50MB for bots)
            file_size = os.path.getsize(podcast_file) / (1024 * 1024)  # MB
            if file_size > 45:  # Leave some margin
                logger.warning(f"File size {file_size:.1f}MB may be too large for Telegram")
            
            # Prepare caption
            if caption is None:
                from datetime import datetime
                caption = f"🎙️ Daily News Podcast - {datetime.now().strftime('%B %d, %Y')}"
            
            # Send audio file
            with open(podcast_file, 'rb') as audio_file:
                message = await self.bot.send_audio(
                    chat_id=self.chat_id,
                    audio=audio_file,
                    caption=caption,
                    title="Daily News Podcast",
                    performer="AI News Assistant"
                )
            
            logger.info(f"Podcast sent successfully to Telegram chat {self.chat_id}")
            
            return {
                'success': True,
                'message_id': message.message_id,
                'chat_id': self.chat_id,
                'file_size_mb': file_size,
                'fallback_used': False
            }
            
        except Exception as e:
            logger.error(f"Failed to send podcast via Telegram: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'fallback_used': False
            }
    
    async def send_text_summary(self, summary: str) -> Dict[str, Any]:
        """
        Send text summary as fallback if audio sending fails
        
        Args:
            summary (str): Text summary to send
            
        Returns:
            dict: Result of the send operation
        """
        if not self.telegram_available:
            return {
                'success': False,
                'error': 'Telegram not available',
                'fallback_used': True
            }
        
        try:
            # Clean any URL characters that might be causing issues
            import re
            clean_summary = re.sub(r'[\r\n\t\x00-\x1f\x7f-\x9f]', '', str(summary)).strip()
            
            logger.info("Sending text summary via Telegram")
            
            # Prepare message
            from datetime import datetime
            message_text = f"""🗞️ Daily News Summary - {datetime.now().strftime('%B %d, %Y')}

{clean_summary}

📱 Audio podcast generation failed, here's the text version instead."""
            
            # Split long messages (Telegram limit is 4096 characters)
            if len(message_text) > 4000:
                # Send in chunks
                chunks = [message_text[i:i+4000] for i in range(0, len(message_text), 4000)]
                
                sent_messages = []
                for i, chunk in enumerate(chunks):
                    if i == 0:
                        chunk = f"🗞️ Daily News Summary - Part {i+1}/{len(chunks)}\\n\\n{chunk}"
                    else:
                        chunk = f"📄 Part {i+1}/{len(chunks)}\\n\\n{chunk}"
                    
                    message = await self.bot.send_message(
                        chat_id=self.chat_id,
                        text=chunk
                    )
                    sent_messages.append(message.message_id)
                
                return {
                    'success': True,
                    'message_ids': sent_messages,
                    'chat_id': self.chat_id,
                    'chunks_sent': len(chunks),
                    'fallback_used': True
                }
            else:
                message = await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=message_text
                )
                
                return {
                    'success': True,
                    'message_id': message.message_id,
                    'chat_id': self.chat_id,
                    'fallback_used': True
                }
                
        except Exception as e:
            logger.error(f"Failed to send text summary via Telegram: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'fallback_used': True
            }
    
    def send_podcast_sync(self, podcast_file: str, caption: str = None) -> Dict[str, Any]:
        """
        Synchronous wrapper for send_podcast
        
        Args:
            podcast_file (str): Path to the podcast MP3 file
            caption (str): Optional caption
            
        Returns:
            dict: Result of the send operation
        """
        if not self.telegram_available:
            logger.info("Telegram not available - saving podcast locally instead")
            return {
                'success': False,
                'error': 'Telegram not configured',
                'fallback_action': 'file_saved_locally',
                'file_path': podcast_file
            }
        
        import asyncio
        
        try:
            # Run async function in sync context with longer timeout
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                task = loop.create_task(self.send_podcast(podcast_file, caption))
                # Set a longer timeout for audio uploads (90 seconds)
                result = loop.run_until_complete(asyncio.wait_for(task, timeout=90))
                return result
            finally:
                loop.close()
        except asyncio.TimeoutError:
            logger.error("Telegram audio upload timed out after 90 seconds")
            return {
                'success': False,
                'error': 'Upload timed out after 90 seconds',
                'fallback_action': 'file_saved_locally',
                'file_path': podcast_file
            }
        except Exception as e:
            logger.error(f"Sync Telegram send failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'fallback_action': 'file_saved_locally',
                'file_path': podcast_file
            }
    
    def send_text_summary_sync(self, summary: str) -> Dict[str, Any]:
        """
        Synchronous wrapper for send_text_summary
        
        Args:
            summary (str): Text summary to send
            
        Returns:
            dict: Result of the send operation
        """
        if not self.telegram_available:
            logger.info("Telegram not available - summary not sent")
            return {
                'success': False,
                'error': 'Telegram not configured',
                'fallback_action': 'summary_logged'
            }
        
        import asyncio
        
        try:
            return asyncio.run(self.send_text_summary(summary))
        except Exception as e:
            logger.error(f"Sync Telegram text send failed: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'fallback_action': 'summary_logged'
            }

def send_daily_podcast(podcast_file: str, summary_text: str = None) -> Dict[str, Any]:
    """
    Convenient function to send daily podcast with fallback to text
    
    Args:
        podcast_file (str): Path to podcast file
        summary_text (str): Text summary as fallback
        
    Returns:
        dict: Combined results of send attempts
    """
    sender = TelegramSender()
    
    # Try to send podcast first
    podcast_result = sender.send_podcast_sync(podcast_file)
    
    if podcast_result['success']:
        return {
            'podcast_sent': True,
            'text_sent': False,
            'primary_method': 'audio',
            'details': podcast_result
        }
    
    # If podcast failed and we have summary text, try sending text
    if summary_text:
        logger.info("Podcast sending failed, trying text summary...")
        text_result = sender.send_text_summary_sync(summary_text)
        
        return {
            'podcast_sent': False,
            'text_sent': text_result['success'],
            'primary_method': 'text' if text_result['success'] else 'failed',
            'podcast_error': podcast_result,
            'text_result': text_result
        }
    
    # Both methods failed or unavailable
    return {
        'podcast_sent': False,
        'text_sent': False,
        'primary_method': 'failed',
        'error': 'All delivery methods failed or unavailable',
        'details': podcast_result
    }