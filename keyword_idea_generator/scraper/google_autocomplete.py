import requests
import pandas as pd
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
                "hl": "es",
                "q": keyword
            }
            
            response = requests.get(url, params=params, headers=Config.REQUEST_HEADERS)
            response.raise_for_status()
            
            suggestions = response.json()[1]
            
            if suggestions:
                df = pd.DataFrame(suggestions, columns=["suggestion"])
                df.to_csv(f"{Config.KEYWORDS_DIR}/autocomplete_{keyword}.csv", index=False)
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error getting autocomplete suggestions: {str(e)}")
            return False
