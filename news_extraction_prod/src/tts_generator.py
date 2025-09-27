"""
TTS (Text-to-Speech) Generator Module
Handles audio podcast generation with dual TTS support:
- eSpeak (free, always available)
- Google Cloud TTS (premium, high quality)
"""

import os
import tempfile
import subprocess
from datetime import datetime
from typing import Optional, Dict, Any
import logging

# Audio processing
try:
    from pydub import AudioSegment
    from pydub.generators import Sine
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    logging.warning("pydub not available - audio processing will be limited")

# Google Cloud TTS (optional)
try:
    from google.cloud import texttospeech
    GOOGLE_TTS_AVAILABLE = True
except ImportError:
    GOOGLE_TTS_AVAILABLE = False

logger = logging.getLogger(__name__)

class TTSGenerator:
    """Text-to-Speech generator with multiple engine support"""
    
    def __init__(self):
        self.google_client = None
        self.google_tts_available = False
        self.use_api_key = False
        self.api_key = None
        self._initialize_google_tts()
    
    def _initialize_google_tts(self):
        """Initialize Google Cloud TTS client if available"""
        if not GOOGLE_TTS_AVAILABLE:
            logger.info("Google Cloud TTS library not available")
            return
        
        try:
            # Check for API key first
            api_key = os.getenv("GOOGLE_CLOUD_TTS_API_KEY")
            if api_key:
                # For API key authentication, we'll use REST API calls
                logger.info("Google TTS API key found - will use REST API")
                self.google_tts_available = True
                self.use_api_key = True
                self.api_key = api_key.strip()
                logger.info("Google Cloud TTS configured with API key")
                return
            
            # Try service account authentication
            credentials_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
            
            if credentials_path and os.path.exists(credentials_path):
                # Use service account file if available
                logger.info(f"Using service account credentials from: {credentials_path}")
            else:
                # Use default credentials (works on Cloud Run with default service account)
                logger.info("Using default Google Cloud credentials (service account)")
            
            self.google_client = texttospeech.TextToSpeechClient()
            self.google_tts_available = True
            self.use_api_key = False
            logger.info("Google Cloud TTS client initialized successfully")
            
        except Exception as e:
            logger.warning(f"Google Cloud TTS initialization failed: {str(e)}")
            self.google_tts_available = False
            self.use_api_key = False
    
    def create_podcast_intro(self, title: str = "Daily News Summary", date: str = None) -> str:
        """Create an introduction for the podcast"""
        if date is None:
            date = datetime.now().strftime("%B %d, %Y")
        
        intro = f"""
        Welcome to {title} for {date}.
        
        I'm your AI host"""
        
        #, and today I'll be sharing the key highlights from multiple news sources, 
        #including insights from technology, business, and general news.
        
        #Let's dive into today's stories.
        #"""
        
        return intro.strip()
    
    def create_podcast_outro(self) -> str:
        """Create an outro for the podcast"""
        outro = """
        
        That concludes today's news summary. """
        
        #Thank you for listening to our daily news roundup. 
        #Stay informed, and we'll see you in the next episode.
        #"""
        
        return outro.strip()
    
    def text_to_speech_espeak(self, text: str, output_file: str = None, 
                             voice: str = "en+f3", rate: int = 165, 
                             pitch: int = 45, amplitude: int = 110) -> Optional[str]:
        """
        Generate speech using eSpeak (always available fallback)
        
        Args:
            text (str): Text to convert
            output_file (str): Output WAV file path
            voice (str): eSpeak voice (en+f3=female, en+m3=male)
            rate (int): Speech rate (words per minute)
            pitch (int): Voice pitch (0-99, 50=normal)
            amplitude (int): Volume (0-200, 100=normal)
            
        Returns:
            str: Path to generated audio file
        """
        try:
            if output_file is None:
                temp_dir = tempfile.gettempdir()
                output_file = os.path.join(temp_dir, 
                    f"espeak_audio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav")
            
            # Create temporary text file for eSpeak input
            temp_text_file = os.path.join(tempfile.gettempdir(), 
                f"temp_text_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            
            with open(temp_text_file, 'w', encoding='utf-8') as f:
                f.write(text)
            
            # Enhanced eSpeak command
            espeak_cmd = [
                'espeak',
                '-f', temp_text_file,
                '-v', voice,
                '-s', str(rate),
                '-p', str(pitch), 
                '-a', str(amplitude),
                '-g', '10',  # 10ms gap between words
                '-w', output_file
            ]
            
            result = subprocess.run(espeak_cmd, capture_output=True, text=True)
            
            # Clean up temp text file
            if os.path.exists(temp_text_file):
                os.remove(temp_text_file)
            
            if result.returncode == 0 and os.path.exists(output_file):
                logger.debug(f"eSpeak audio generated: {output_file}")
                return output_file
            else:
                raise Exception(f"eSpeak failed: {result.stderr}")
                
        except Exception as e:
            logger.error(f"eSpeak TTS error: {str(e)}")
            return None
    
    def text_to_speech_google(self, text: str, output_file: str = None,
                             voice_name: str = "en-US-Standard-F",
                             language_code: str = "en-US") -> Optional[str]:
        """
        Generate speech using Google Cloud TTS (premium option)
        
        Args:
            text (str): Text to convert
            output_file (str): Output file path
            voice_name (str): Google TTS voice name
            language_code (str): Language code
            
        Returns:
            str: Path to generated audio file
        """
        if not self.google_tts_available:
            logger.warning("Google TTS not available, falling back to eSpeak")
            return self.text_to_speech_espeak(text, output_file)
        
        try:
            if output_file is None:
                temp_dir = tempfile.gettempdir()
                output_file = os.path.join(temp_dir,
                    f"google_tts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.wav")
            
            if self.use_api_key:
                # Use REST API with API key
                return self._synthesize_with_api_key(text, output_file, voice_name, language_code)
            else:
                # Use client library with service account
                return self._synthesize_with_client(text, output_file, voice_name, language_code)
                
        except Exception as e:
            logger.error(f"Google TTS synthesis failed: {str(e)}")
            logger.warning("Falling back to eSpeak")
            return self.text_to_speech_espeak(text, output_file)
    
    def _synthesize_with_client(self, text: str, output_file: str, voice_name: str, language_code: str) -> str:
        """Synthesize using Google Cloud client library"""
        # Prepare the text input
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        # Build the voice request
        voice = texttospeech.VoiceSelectionParams(
            language_code=language_code,
            name=voice_name
        )
        
        # Select the type of audio file
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.LINEAR16,
            speaking_rate=1.0,
            pitch=0.0
        )
        
        # Perform the text-to-speech request
        response = self.google_client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # Write the response to the output file
        with open(output_file, "wb") as out:
            out.write(response.audio_content)
        
        logger.debug(f"Google TTS audio generated: {output_file}")
        return output_file
    
    def _synthesize_with_api_key(self, text: str, output_file: str, voice_name: str, language_code: str) -> str:
        """Synthesize using Google TTS REST API with API key"""
        import requests
        
        url = f"https://texttospeech.googleapis.com/v1/text:synthesize?key={self.api_key}"
        
        payload = {
            "input": {"text": text},
            "voice": {"languageCode": language_code, "name": voice_name},
            "audioConfig": {"audioEncoding": "LINEAR16", "speakingRate": 1.0, "pitch": 0.0}
        }
        
        headers = {"Content-Type": "application/json"}
        
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        # Get the audio content
        audio_content = response.json()["audioContent"]
        import base64
        audio_data = base64.b64decode(audio_content)
        
        # Write to file
        with open(output_file, "wb") as out:
            out.write(audio_data)
        
        logger.debug(f"Google TTS API audio generated: {output_file}")
        return output_file

    def generate_speech(self, text: str, use_premium: bool = False, **kwargs) -> Optional[str]:
        """
        Generate speech using the best available TTS engine
        
        Args:
            text (str): Text to convert
            use_premium (bool): Whether to use premium Google TTS
            **kwargs: Additional parameters for TTS engines
            
        Returns:
            str: Path to generated audio file
        """
        if use_premium and self.google_tts_available:
            logger.info("Using Google Cloud TTS (premium)")
            return self.text_to_speech_google(text, **kwargs)
        else:
            logger.info("Using eSpeak TTS (free)")
            return self.text_to_speech_espeak(text, **kwargs)
    
    def create_podcast_episode(self, content: str, output_file: str = "news_podcast.mp3",
                              use_premium: bool = False, add_intro: bool = True,
                              add_outro: bool = True, voice_settings: Dict = None,
                              upload_to_cloud: bool = False, config = None) -> Optional[Dict]:
        """
        Create a complete podcast episode from content
        
        Args:
            content (str): Main content for the podcast
            output_file (str): Output MP3 file path
            use_premium (bool): Whether to use Google TTS
            add_intro (bool): Add podcast intro
            add_outro (bool): Add podcast outro
            voice_settings (dict): Voice configuration
            upload_to_cloud (bool): Upload to Google Cloud Storage
            config: Configuration object for cloud storage
            
        Returns:
            dict: Podcast creation result with local path and optionally cloud URL
        """
        if not PYDUB_AVAILABLE:
            logger.error("pydub not available - cannot create enhanced podcast")
            return None
        
        try:
            logger.info(f"Creating podcast episode: {output_file}")
            
            # Prepare full script
            full_script = ""
            
            if add_intro:
                intro = self.create_podcast_intro()
                full_script += intro + "\\n\\n"
            
            # Add main content with better pacing
            formatted_content = content.replace('. ', '. ... ')  # Add pauses
            formatted_content = formatted_content.replace('!', '! ... ')
            formatted_content = formatted_content.replace('?', '? ... ')
            full_script += formatted_content
            
            if add_outro:
                outro = self.create_podcast_outro()
                full_script += "\\n\\n" + outro
            
            # Generate speech
            wav_file = self.generate_speech(
                full_script, 
                use_premium=use_premium,
                **(voice_settings or {})
            )
            
            if not wav_file:
                logger.error("Failed to generate speech audio")
                return None
            
            logger.info("Processing audio with enhancements...")
            
            # Load and enhance audio
            audio = AudioSegment.from_wav(wav_file)
            
            # Apply audio enhancements
            audio = audio.normalize()
            audio = audio.compress_dynamic_range(threshold=-20.0, ratio=4.0)
            audio = audio.fade_in(1500).fade_out(1500)
            audio = audio.high_pass_filter(80)
            
            # Add intro/outro chimes
            if add_intro or add_outro:
                tone1 = Sine(880).to_audio_segment(duration=300).fade_in(50).fade_out(50)
                tone2 = Sine(1047).to_audio_segment(duration=300).fade_in(50).fade_out(50)
                chime = tone1.overlay(tone2) - 25
                
                if add_intro:
                    audio = chime + AudioSegment.silent(duration=800) + audio
                
                if add_outro:
                    audio = audio + AudioSegment.silent(duration=800) + chime
            
            # Final volume adjustment
            audio = audio - 3
            
            # Export as high-quality MP3
            logger.info(f"Exporting podcast to {output_file}")
            audio.export(output_file, format="mp3", bitrate="192k", tags={
                'title': 'Daily News Podcast',
                'artist': 'AI News Assistant',
                'genre': 'News'
            })
            
            # Clean up temporary WAV file
            if os.path.exists(wav_file):
                os.remove(wav_file)
            
            duration_mins = len(audio) / 1000 / 60
            file_size = os.path.getsize(output_file) / (1024 * 1024)
            
            logger.info(f"Podcast created successfully!")
            logger.info(f"  File: {output_file}")
            logger.info(f"  Duration: {duration_mins:.1f} minutes")
            logger.info(f"  Size: {file_size:.2f} MB")
            
            result = {
                'success': True,
                'local_file': output_file,
                'duration_minutes': duration_mins,
                'file_size_mb': file_size,
                'cloud_storage': None
            }
            
            # Upload to cloud storage if requested
            if upload_to_cloud and config:
                try:
                    from .cloud_storage import upload_podcast_to_cloud
                    
                    cloud_result = upload_podcast_to_cloud(
                        local_file_path=output_file,
                        config=config,
                        metadata={
                            'duration_minutes': duration_mins,
                            'file_size_mb': file_size,
                            'voice_engine': 'google_tts' if use_premium else 'espeak',
                            'content_length': len(content)
                        }
                    )
                    
                    result['cloud_storage'] = cloud_result
                    
                    if cloud_result['success']:
                        logger.info(f"  Cloud URL: {cloud_result['public_url']}")
                    else:
                        logger.warning(f"Cloud upload failed: {cloud_result.get('error')}")
                        
                except Exception as e:
                    logger.error(f"Cloud storage integration failed: {str(e)}")
                    result['cloud_storage'] = {'success': False, 'error': str(e)}
            
            return result
            
        except Exception as e:
            logger.error(f"Error creating podcast: {str(e)}")
            return None

# Voice preset configurations
VOICE_PRESETS = {
    "female_natural": {"voice": "en+f3", "rate": 165, "pitch": 45},
    "male_natural": {"voice": "en+m3", "rate": 160, "pitch": 40},
    "female_smooth": {"voice": "en+f4", "rate": 170, "pitch": 55},
    "male_deep": {"voice": "en+m3", "rate": 155, "pitch": 35},
    "robotic": {"voice": "en", "rate": 150, "pitch": 50}
}

def generate_podcast(content: str, output_file: str = "news_podcast.mp3",
                    voice_preset: str = "female_natural", use_premium: bool = False,
                    upload_to_cloud: bool = False, config = None) -> Optional[Dict]:
    """
    Convenient function to generate podcast with preset configurations
    
    Args:
        content (str): Podcast content
        output_file (str): Output file path
        voice_preset (str): Voice preset from VOICE_PRESETS
        use_premium (bool): Use Google TTS if available
        upload_to_cloud (bool): Upload to Google Cloud Storage
        config: Configuration object for cloud storage
        
    Returns:
        dict: Podcast generation result with paths and URLs
    """
    tts_generator = TTSGenerator()
    
    # Get voice settings
    voice_settings = VOICE_PRESETS.get(voice_preset, VOICE_PRESETS["female_natural"])
    
    return tts_generator.create_podcast_episode(
        content=content,
        output_file=output_file,
        use_premium=use_premium,
        voice_settings=voice_settings if not use_premium else None,
        upload_to_cloud=upload_to_cloud,
        config=config
    )