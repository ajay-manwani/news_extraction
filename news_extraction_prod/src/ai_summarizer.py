"""
AI Summarization Module
Handles AI-powered article summarization using OpenRouter/Grok
"""

import os
from typing import List, Dict, Optional
import logging
import time

import httpx

logger = logging.getLogger(__name__)

class AISummarizer:
    """AI Summarization service with fallback handling"""
    
    def __init__(self):
        self.client = None
        self.session: Optional[httpx.Client] = None
        self.api_available = False
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize OpenRouter client if API key is available"""
        api_key_raw = os.getenv("OPENROUTER_API_KEY", "")
        api_key = api_key_raw.strip()
        
        if api_key:
            try:
                self.client = {
                    "api_key": api_key,
                    "base_url": "https://openrouter.ai/api/v1",
                    "default_headers": {
                        "HTTP-Referer": "https://github.com/ajay-manwani/news_extraction",
                        "X-Title": "News Extraction Project",
                        "Content-Type": "application/json"
                    }
                }
                self.session = httpx.Client(
                    base_url=self.client["base_url"],
                    headers=self.client["default_headers"],
                    timeout=httpx.Timeout(30.0, connect=10.0, read=20.0),
                )
                self.api_available = True
                logger.info("OpenRouter AI client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize OpenRouter client: {str(e)}")
                self.api_available = False
        else:
            logger.warning("OPENROUTER_API_KEY not found - using mock summaries for development")
            self.api_available = False
    
    def summarize(self, text: str, max_tokens: int = 150) -> str:
        """Generate AI-powered summary using OpenRouter"""
        if not self.api_available:
            logger.warning("OpenRouter not available, using fallback summary")
            return self._fallback_summary(text)
        
        try:
            # Get model from config
            from config.settings import get_config
            config = get_config()
            
            prompt = (
                f"Summarize the following news article in 1-2 sentences. "
                f"Focus on the key facts and main points:\n\n{text}"
            )

            payload = {
                "model": config.AI_MODEL,  # Use Grok 4 Fast from config
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": config.TEMPERATURE
            }

            response = self.session.post(
                "/chat/completions",
                headers={
                    **self.client["default_headers"],
                    "Authorization": f"Bearer {self.client['api_key']}"
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            summary = data["choices"][0]["message"]["content"].strip()
            logger.debug(f"AI summary generated with {config.AI_MODEL}: {len(summary)} characters")
            return summary
            
        except Exception as e:
            logger.error(f"AI summarization failed: {str(e)}")
            return self._fallback_summary(text)
    
    def _ai_summarize(self, text: str, max_tokens: int) -> str:
        """Generate AI summary using OpenRouter/Grok"""
        try:
            prompt = (
                "Please provide a concise summary of the following article. "
                "Focus on the main points and key information:\n\n"
                f"{text}\n\nSummary:"
            )

            payload = {
                "model": "openai/gpt-3.5-turbo",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": max_tokens,
                "temperature": 0.7
            }

            response = self.session.post(
                "/chat/completions",
                headers={
                    **self.client["default_headers"],
                    "Authorization": f"Bearer {self.client['api_key']}"
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            summary = data["choices"][0]["message"]["content"].strip()
            logger.debug(f"AI summary generated: {len(summary)} characters")
            return summary
            
        except Exception as e:
            logger.error(f"AI summarization failed: {str(e)}", exc_info=True)
            return self._fallback_summary(text)
    
    def _fallback_summary(self, text: str) -> str:
        """Generate basic extractive summary as fallback"""
        try:
            # Simple extractive summary - first few sentences
            sentences = text.split('. ')
            
            # Take first 2-3 sentences up to ~200 characters
            summary_parts = []
            char_count = 0
            
            for sentence in sentences[:5]:  # Maximum 5 sentences
                if char_count + len(sentence) > 200:
                    break
                summary_parts.append(sentence.strip())
                char_count += len(sentence)
            
            fallback_summary = '. '.join(summary_parts)
            if not fallback_summary.endswith('.'):
                fallback_summary += '.'
            
            # Add fallback indicator
            fallback_summary += " [Extractive summary - AI summarization unavailable]"
            
            logger.debug(f"Fallback summary generated: {len(fallback_summary)} characters")
            return fallback_summary
            
        except Exception as e:
            logger.error(f"Fallback summarization failed: {str(e)}")
            return "Summary generation failed - content processing error"
    
    def generate_meta_summary(self, articles_df, summary_column: str = 'ai_summary') -> str:
        """
        Generate a meta-summary of all article summaries
        
        Args:
            articles_df: DataFrame containing articles with summaries
            summary_column (str): Name of the column containing summaries
            
        Returns:
            str: Meta-summary text
        """
        try:
            # Get all summaries
            summaries = []
            for _, row in articles_df.iterrows():
                summary = row.get(summary_column, '')
                if summary and not summary.startswith('Summary generation failed'):
                    summaries.append(summary)
            
            if not summaries:
                return "No valid summaries available for meta-summary generation"
            
            # Combine summaries
            all_summaries = "\\n\\n".join(summaries)
            
            if self.api_available and self.client and self.session:
                return self._ai_meta_summarize(all_summaries)
            else:
                return self._fallback_meta_summary(summaries)
                
        except Exception as e:
            logger.error(f"Meta-summary generation failed: {str(e)}")
            return "Meta-summary generation failed"
    
    def _ai_meta_summarize(self, all_summaries: str) -> str:
        """Generate AI meta-summary"""
        try:
            # Get model from config  
            from config.settings import get_config
            config = get_config()
            
            """prompt = (
                "Below are summaries of multiple news articles. "
                "Please create a comprehensive meta-summary that:\n"
                "1. Identifies major themes and trends\n"
                "2. Highlights key developments across articles\n"
                "3. Notes any contrasting viewpoints or developments\n"
                "4. Provides a high-level overview of the news landscape\n\n"
                f"Article Summaries:\n{all_summaries}\n\nMeta-Summary:"
            ) """

            prompt= (
                    """ You are a podcast scriptwriter. Your task is to take the following article summaries and transform them into a single, engaging 6-minute news podcast script.

                    Guidelines:
                    - Audience: general listeners who want a clear, concise, and engaging news update.
                    - Length: aim for ~700 words (enough for ~5 minutes of spoken audio).
                    - Style: conversational but professional, like a news podcast host. Avoid jargon.
                    - Structure:
                    1. Opening greeting and quick overview of what’s coming up.
                    2. Group related stories into segments (e.g., world news, business, tech, science, culture).
                    3. Within each segment, smoothly transition between stories.
                    4. Add short connective phrases (“Meanwhile…”, “In other news…”, “On a lighter note…”).
                    5. End with a brief wrap‑up and a sign‑off.

                    - Do NOT repeat the summaries verbatim. Rewrite them into natural spoken language.
                    - Keep sentences varied in length for a natural rhythm when read aloud.
                    - Avoid filler words like “um” or “you know.”
                    - Make sure the script flows logically and feels like one continuous show.

                    Here are the article summaries to use:
                    {all_summaries}

                    Now, write the complete podcast script following the above rules.
                """
            )
            system_prompt = "You are a podcast scriptwriter. Write engaging, natural spoken scripts for a 10 to 20‑minute news podcast."

            payload = {
                "model": config.AI_MODEL,  # Use Grok 4 Fast from config
                "messages": [   {"role": "system", "content": system_prompt},
                                {"role": "user", "content": prompt}
                             ],
                "max_tokens": 4000,
                "temperature": config.TEMPERATURE
            }

            response = self.session.post(
                "/chat/completions",
                headers={
                    **self.client["default_headers"],
                    "Authorization": f"Bearer {self.client['api_key']}"
                },
                json=payload,
            )
            response.raise_for_status()
            data = response.json()

            meta_summary = data["choices"][0]["message"]["content"].strip()
            logger.info(f"AI meta-summary generated with {config.AI_MODEL}: {len(meta_summary)} characters")
            return meta_summary
            
        except Exception as e:
            logger.error(f"AI meta-summarization failed: {str(e)}", exc_info=True)
            return self._fallback_meta_summary(all_summaries.split('\\n\\n'))
    
    def _fallback_meta_summary(self, summaries: List[str]) -> str:
        """Generate basic meta-summary as fallback"""
        try:
            # Count total articles
            article_count = len(summaries)
            
            # Extract key themes (simple keyword frequency)
            all_text = ' '.join(summaries).lower()
            
            # Common news keywords
            business_keywords = ['business', 'company', 'market', 'economic', 'financial', 'trade']
            tech_keywords = ['technology', 'tech', 'digital', 'ai', 'artificial', 'software', 'startup']
            politics_keywords = ['government', 'political', 'policy', 'election', 'minister', 'parliament']
            
            themes = []
            if any(keyword in all_text for keyword in business_keywords):
                themes.append('business and economics')
            if any(keyword in all_text for keyword in tech_keywords):
                themes.append('technology')
            if any(keyword in all_text for keyword in politics_keywords):
                themes.append('politics and governance')
            
            # Create basic meta-summary
            meta_summary = f"""Today's news covers {article_count} key stories"""
            
            if themes:
                meta_summary += f" focusing on {', '.join(themes)}"""
            
            meta_summary += """. Key developments include various updates across different sectors. """
            
            # Add first lines from summaries as highlights
            highlights = []
            for summary in summaries[:3]:  # Top 3 summaries
                first_sentence = summary.split('.')[0].strip()
                if first_sentence and len(first_sentence) > 10:
                    highlights.append(first_sentence)
            
            if highlights:
                meta_summary += f"Major highlights: {'; '.join(highlights)}. "
            
            meta_summary += "[Fallback meta-summary - AI summarization unavailable]"
            
            logger.info(f"Fallback meta-summary generated: {len(meta_summary)} characters")
            return meta_summary
            
        except Exception as e:
            logger.error(f"Fallback meta-summary failed: {str(e)}")
            return f"Meta-summary of {len(summaries)} articles - processing completed with basic aggregation"

def process_article_summaries(articles: List[Dict]) -> List[Dict]:
    """
    Generate summaries for all articles
    
    Args:
        articles (list): List of articles with 'full_text' field
        
    Returns:
        list: Articles with added 'ai_summary' field
    """
    summarizer = AISummarizer()
    
    logger.info(f"Generating summaries for {len(articles)} articles")
    
    for i, article in enumerate(articles, 1):
        logger.debug(f"Processing summary {i}/{len(articles)}: {article.get('title', 'Unknown')}")
        
        full_text = article.get('full_text', '')
        if full_text:
            summary = summarizer.summarize(full_text)
        else:
            # Fallback to RSS summary if full text not available
            summary = article.get('summary', 'No content available for summarization')
        
        article['ai_summary'] = summary
        
        # Add a small delay to respect rate limits
        time.sleep(0.5)
    
    logger.info("Article summarization completed")
    return articles