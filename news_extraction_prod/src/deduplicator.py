"""
Deduplication Module
Handles finding and removing duplicate articles using TF-IDF and cosine similarity
"""

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import pandas as pd
from typing import List, Dict, Set
import logging

logger = logging.getLogger(__name__)

def find_duplicates(articles: List[Dict], similarity_threshold: float = 0.85) -> Dict:
    """
    Find duplicate articles using TF-IDF and cosine similarity
    
    Args:
        articles (list): List of article dictionaries
        similarity_threshold (float): Threshold for considering articles as duplicates
        
    Returns:
        dict: Results containing duplicates info and indices to remove
    """
    if len(articles) < 2:
        logger.info("Less than 2 articles, no duplicates possible")
        return {
            'duplicate_pairs': [],
            'articles_to_remove': set(),
            'stats': {
                'total_articles': len(articles),
                'duplicate_pairs_found': 0,
                'articles_to_remove': 0
            }
        }
    
    try:
        logger.info(f"Checking for duplicates among {len(articles)} articles")
        
        # Prepare text for comparison
        comparison_texts = []
        for article in articles:
            # Combine title (weighted) and text for better comparison
            title = article.get('title', '')
            full_text = article.get('full_text', '')
            summary = article.get('ai_summary', article.get('summary', ''))
            
            # Use full text if available, otherwise use summary
            text_content = full_text if full_text else summary
            
            # Weight title more heavily in comparison
            combined_text = f"{title} {title} {text_content}".lower()
            comparison_texts.append(combined_text)
        
        # Create TF-IDF vectors
        tfidf = TfidfVectorizer(
            stop_words='english', 
            max_features=5000,
            ngram_range=(1, 2)  # Include bigrams for better similarity detection
        )
        
        tfidf_matrix = tfidf.fit_transform(comparison_texts)
        
        # Calculate cosine similarity
        cosine_sim = cosine_similarity(tfidf_matrix)
        
        # Find duplicates
        duplicate_pairs = []
        articles_to_remove = set()
        
        for i in range(len(articles)):
            for j in range(i + 1, len(articles)):
                similarity_score = cosine_sim[i][j]
                
                if similarity_score > similarity_threshold:
                    duplicate_pairs.append({
                        'article1_idx': i,
                        'article2_idx': j,
                        'similarity_score': float(similarity_score),
                        'article1_title': articles[i].get('title', 'Unknown'),
                        'article2_title': articles[j].get('title', 'Unknown'),
                        'article1_source': articles[i].get('source', 'Unknown'),
                        'article2_source': articles[j].get('source', 'Unknown')
                    })
                    
                    # Decide which article to remove (keep the one from more reliable source or longer content)
                    article1 = articles[i]
                    article2 = articles[j]
                    
                    # Prefer articles with more content
                    content1_length = len(article1.get('full_text', ''))
                    content2_length = len(article2.get('full_text', ''))
                    
                    if content1_length >= content2_length:
                        articles_to_remove.add(j)  # Remove second article
                    else:
                        articles_to_remove.add(i)  # Remove first article
        
        results = {
            'duplicate_pairs': duplicate_pairs,
            'articles_to_remove': articles_to_remove,
            'stats': {
                'total_articles': len(articles),
                'duplicate_pairs_found': len(duplicate_pairs),
                'articles_to_remove': len(articles_to_remove)
            }
        }
        
        logger.info(f"Deduplication complete: {len(duplicate_pairs)} duplicate pairs found, "
                   f"{len(articles_to_remove)} articles marked for removal")
        
        return results
        
    except Exception as e:
        logger.error(f"Error in duplicate detection: {str(e)}")
        return {
            'duplicate_pairs': [],
            'articles_to_remove': set(),
            'stats': {
                'total_articles': len(articles),
                'duplicate_pairs_found': 0,
                'articles_to_remove': 0,
                'error': str(e)
            }
        }

def remove_duplicates(articles: List[Dict], similarity_threshold: float = 0.85) -> Dict:
    """
    Remove duplicate articles from the list
    
    Args:
        articles (list): List of article dictionaries
        similarity_threshold (float): Threshold for considering articles as duplicates
        
    Returns:
        dict: Results containing deduplicated articles and statistics
    """
    if not articles:
        return {
            'articles': [],
            'removed_articles': [],
            'deduplication_stats': {
                'original_count': 0,
                'final_count': 0,
                'duplicates_removed': 0
            }
        }
    
    original_count = len(articles)
    logger.info(f"Starting deduplication process for {original_count} articles")
    
    # Find duplicates
    duplicate_info = find_duplicates(articles, similarity_threshold)
    articles_to_remove = duplicate_info['articles_to_remove']
    
    # Create deduplicated list
    deduplicated_articles = []
    removed_articles = []
    
    for i, article in enumerate(articles):
        if i in articles_to_remove:
            removed_articles.append({
                **article,
                'removal_reason': 'duplicate_content',
                'original_index': i
            })
        else:
            deduplicated_articles.append(article)
    
    final_count = len(deduplicated_articles)
    duplicates_removed = original_count - final_count
    
    results = {
        'articles': deduplicated_articles,
        'removed_articles': removed_articles,
        'deduplication_stats': {
            'original_count': original_count,
            'final_count': final_count,
            'duplicates_removed': duplicates_removed,
            'duplicate_pairs_found': len(duplicate_info['duplicate_pairs'])
        },
        'duplicate_pairs': duplicate_info['duplicate_pairs']
    }
    
    logger.info(f"Deduplication complete: {original_count} → {final_count} articles "
               f"({duplicates_removed} duplicates removed)")
    
    return results