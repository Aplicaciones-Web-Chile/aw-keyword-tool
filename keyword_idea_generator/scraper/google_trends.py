from pytrends.request import TrendReq
import pandas as pd
from urllib.parse import quote
import os
from ..config import Config
import logging

logger = logging.getLogger(__name__)

class GoogleTrends:
    @staticmethod
    def get_trends_keywords(keyword):
        """Get related keywords from Google Trends"""
        try:
            pytrends = TrendReq(
                hl=f"{Config.LANGUAGE}-{Config.COUNTRY}",
                tz=Config.TIMEZONE
            )
            
            # Construir payload con la región correcta
            pytrends.build_payload(
                [keyword],
                cat=0,
                timeframe='today 12-m',
                geo=Config.COUNTRY
            )
            
            related_queries = pytrends.related_queries()
            
            if keyword in related_queries and related_queries[keyword]['top'] is not None:
                # Crear un nombre de archivo seguro
                safe_keyword = quote(keyword, safe='')
                output_file = os.path.join(Config.KEYWORDS_DIR, f"trends_{safe_keyword}.csv")
                
                top_queries = related_queries[keyword]['top']
                top_queries.to_csv(output_file, index=False, encoding='utf-8-sig')
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error getting trends keywords: {str(e)}")
            return False
