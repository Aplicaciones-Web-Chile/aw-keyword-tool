from pytrends.request import TrendReq
import logging
from config import Config

def get_trends_keywords(seed_keyword):
    """Obtiene keywords relacionadas desde Google Trends"""
    try:
        pytrends = TrendReq()
        pytrends.build_payload([seed_keyword])
        
        related_queries = pytrends.related_queries()
        top_queries = related_queries[seed_keyword]['top']
        
        return top_queries['query'].tolist() if top_queries is not None else []
    
    except Exception as e:
        logging.error(f"Error en Google Trends para {seed_keyword}: {str(e)}")
        return []
