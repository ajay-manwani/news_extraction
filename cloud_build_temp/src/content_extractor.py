"""
Content Extraction Module
Handles extracting full article content from web pages using newspaper3k
"""

from newspaper import Article
import time
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

def extract_article_content(url: str, timeout: int = 30) -> Dict:
    """
    Extract article content using newspaper3k
    
    Args:
        url (str): URL of the article
        timeout (int): Timeout for content extraction
        
    Returns:
        dict: Dictionary containing article details
    """
    try:
        logger.debug(f"Extracting content from: {url}")
        
        # Add a delay to be respectful to servers
        time.sleep(1)
        
        article = Article(url)
        article.download()
        article.parse()
        
        content_data = {
            'full_text': article.text,
            'authors': article.authors,
            'top_image': article.top_image,
            'article_date': article.publish_date,
            'extraction_successful': True
        }
        
        logger.debug(f"Successfully extracted {len(article.text)} characters from {url}")
        return content_data
        
    except Exception as e:
        logger.warning(f"Error extracting content from {url}: {str(e)}")
        return {
            'full_text': '',
            'authors': [],
            'top_image': '',
            'article_date': None,
            'extraction_successful': False
        }

def extract_content_batch(articles: List[Dict]) -> List[Dict]:
    """
    Extract content for a batch of articles
    
    Args:
        articles (list): List of article dictionaries with 'link' field
        
    Returns:
        list: Articles with added content extraction fields
    """
    logger.info(f"Extracting content for {len(articles)} articles")
    
    enriched_articles = []
    successful_extractions = 0
    
    for i, article in enumerate(articles, 1):
        logger.debug(f"Processing article {i}/{len(articles)}: {article.get('title', 'Unknown')}")
        
        # Extract content
        content_data = extract_article_content(article['link'])
        
        # Merge with original article data
        enriched_article = {**article, **content_data}
        enriched_articles.append(enriched_article)
        
        if content_data['extraction_successful']:
            successful_extractions += 1
    
    logger.info(f"Content extraction completed: {successful_extractions}/{len(articles)} successful")
    return enriched_articles