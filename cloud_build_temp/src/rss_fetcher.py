"""
RSS Feed Processing Module
Handles fetching and parsing RSS feeds from multiple news sources
"""

import feedparser
import time
from typing import Dict, List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

def fetch_rss_feed(source_name: str, source_info: Dict) -> List[Dict]:
    """
    Fetch and parse RSS feed from a given source
    
    Args:
        source_name (str): Name of the source
        source_info (dict): Dictionary containing RSS feed URL and categories
        
    Returns:
        list: List of dictionaries containing parsed news items
    """
    try:
        logger.info(f"Fetching RSS feed from {source_name}: {source_info.get('rss')}")
        
        feed = feedparser.parse(source_info['rss'])
        
        if hasattr(feed, 'status') and feed.status >= 400:
            logger.warning(f"RSS feed returned status {feed.status} for {source_name}")
        
        news_items = []
        max_articles = source_info.get('max_articles', 50)
        
        for entry in feed.entries[:max_articles]:
            news_item = {
                'source': source_name,
                'title': entry.get('title', ''),
                'link': entry.get('link', ''),
                'published': entry.get('published', ''),
                'summary': entry.get('summary', ''),
                'categories': source_info.get('categories', [])
            }
            news_items.append(news_item)
        
        logger.info(f"Fetched {len(news_items)} articles from {source_name}")
        return news_items
        
    except Exception as e:
        logger.error(f"Error fetching RSS feed from {source_name}: {str(e)}")
        return []

def fetch_all_sources(sources_config: Dict) -> List[Dict]:
    """
    Fetch articles from all configured RSS sources
    
    Args:
        sources_config (dict): Dictionary of all RSS sources
        
    Returns:
        list: Combined list of all news items
    """
    all_articles = []
    
    for source_name, source_info in sources_config.items():
        if not source_info.get('enabled', True):
            logger.info(f"Skipping disabled source: {source_name}")
            continue
            
        logger.info(f"Processing source: {source_name}")
        articles = fetch_rss_feed(source_name, source_info)
        all_articles.extend(articles)
        
        # Be respectful to servers - add delay between requests
        time.sleep(1)
    
    logger.info(f"Total articles fetched: {len(all_articles)}")
    return all_articles