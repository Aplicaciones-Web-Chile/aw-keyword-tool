import requests
import pandas as pd
from urllib.parse import quote
import os
from ..config import Config
import logging

logger = logging.getLogger(__name__)

class GoogleAutocomplete:
    @staticmethod
    def get_autocomplete_keywords(keyword):
        """Get autocomplete suggestions from Google"""
        try:
            url = "http://suggestqueries.google.com/complete/search"
            params = {
                "client": "firefox",
                "hl": Config.LANGUAGE,
                "gl": Config.COUNTRY,
                "q": keyword
            }
            
            response = requests.get(url, params=params, headers=Config.REQUEST_HEADERS)
            response.raise_for_status()
            
            suggestions = response.json()[1]
            
            if suggestions:
                # Crear un nombre de archivo seguro
                safe_keyword = quote(keyword, safe='')
                output_file = os.path.join(Config.KEYWORDS_DIR, f"autocomplete_{safe_keyword}.csv")
                
                df = pd.DataFrame(suggestions, columns=["suggestion"])
                df.to_csv(output_file, index=False, encoding='utf-8-sig')
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error getting autocomplete suggestions: {str(e)}")
            return False
