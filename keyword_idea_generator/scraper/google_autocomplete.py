import requests
import csv
import time
import os
from config import Config
import logging
from urllib.parse import quote_plus

logger = logging.getLogger(__name__)

def get_autocomplete_keywords(seed_keyword):
    """Get keyword suggestions from Google Autocomplete"""
    base_url = "http://suggestqueries.google.com/complete/search"
    keywords = []
    
    try:
        query = quote_plus(seed_keyword)
        url = f"{base_url}?client=firefox&q={query}"
        
        response = requests.get(url, headers=Config.REQUEST_HEADERS)
        response.raise_for_status()
        
        suggestions = response.json()[1]
        keywords.extend(suggestions)
        
        time.sleep(Config.RATE_LIMIT_DELAY)
        
    except Exception as e:
        logger.error(f"Autocomplete failed for {seed_keyword}: {str(e)}")
    
    if keywords:
        file_path = Config.KEYWORD_PATHS['autocomplete']
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for kw in keywords:
                writer.writerow([kw, seed_keyword, 'autocomplete', time.strftime('%Y-%m-%d %H:%M:%S')])
    
    return keywords
