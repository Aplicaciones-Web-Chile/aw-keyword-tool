from pytrends.request import TrendReq
import pandas as pd
from ..config import Config
import logging

logger = logging.getLogger(__name__)

class GoogleTrends:
    @staticmethod
    def get_trends_keywords(keyword):
        """Get related keywords from Google Trends"""
        try:
            pytrends = TrendReq(hl='es-ES', tz=360)
            pytrends.build_payload([keyword], cat=0, timeframe='today 12-m', geo='ES')
            related_queries = pytrends.related_queries()
            
            if keyword in related_queries and related_queries[keyword]['top'] is not None:
                top_queries = related_queries[keyword]['top']
                top_queries.to_csv(f"{Config.KEYWORDS_DIR}/trends_{keyword}.csv", index=False)
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error getting trends keywords: {str(e)}")
            return False
