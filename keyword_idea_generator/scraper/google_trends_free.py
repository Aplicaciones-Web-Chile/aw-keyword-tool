"""
Módulo para obtener datos de Google Trends sin usar SerpAPI.
"""
import logging
from typing import List, Dict, Optional
from pytrends.request import TrendReq
from ..utils.proxy_manager import ProxyManager
import time
import random

logger = logging.getLogger(__name__)

class GoogleTrendsFree:
    """Clase para obtener datos de Google Trends usando pytrends."""
    
    def __init__(self):
        self.proxy_manager = ProxyManager()
        self.pytrends = None
        self.last_request = 0
        self.min_delay = 2  # Mínimo delay entre requests
        
    def _init_pytrends(self) -> None:
        """Inicializar o reinicializar pytrends con un nuevo proxy."""
        proxy, headers = self.proxy_manager.get_proxy_and_headers()
        proxies = {}
        
        if proxy:
            proxies = {
                'https': proxy['https']
            }
        
        self.pytrends = TrendReq(
            hl='es',
            tz=360,
            timeout=(10,25),
            proxies=proxies,
            retries=2,
            backoff_factor=0.5
        )
    
    def _wait_between_requests(self) -> None:
        """Esperar un tiempo aleatorio entre requests para evitar bloqueos."""
        current_time = time.time()
        elapsed = current_time - self.last_request
        
        if elapsed < self.min_delay:
            wait_time = self.min_delay - elapsed + random.uniform(0.5, 1.5)
            time.sleep(wait_time)
        
        self.last_request = time.time()
    
    def get_related_queries(self, keyword: str, max_retries: int = 3) -> List[Dict[str, int]]:
        """
        Obtener consultas relacionadas desde Google Trends.
        
        Args:
            keyword: Palabra clave a buscar
            max_retries: Número máximo de reintentos
            
        Returns:
            Lista de diccionarios con las palabras clave relacionadas y sus puntajes
        """
        results = []
        
        for attempt in range(max_retries):
            try:
                # Inicializar/reinicializar pytrends
                self._init_pytrends()
                self._wait_between_requests()
                
                # Construir payload
                self.pytrends.build_payload(
                    kw_list=[keyword],
                    cat=0,
                    timeframe='today 12-m',
                    geo='ES'
                )
                
                # Obtener consultas relacionadas
                related_queries = self.pytrends.related_queries()
                
                if keyword in related_queries and 'top' in related_queries[keyword]:
                    df = related_queries[keyword]['top']
                    
                    if df is not None and not df.empty:
                        for _, row in df.iterrows():
                            results.append({
                                'keyword': row['query'],
                                'score': int(row['value'])
                            })
                        break
                    
            except Exception as e:
                logger.error(f"Error al obtener datos de Google Trends (intento {attempt + 1}): {str(e)}")
                
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Espera exponencial
                continue
        
        return results
    
    def get_trending_searches(self, max_retries: int = 3) -> List[str]:
        """
        Obtener búsquedas tendencia del día.
        
        Args:
            max_retries: Número máximo de reintentos
            
        Returns:
            Lista de palabras clave tendencia
        """
        results = []
        
        for attempt in range(max_retries):
            try:
                # Inicializar/reinicializar pytrends
                self._init_pytrends()
                self._wait_between_requests()
                
                # Obtener trending searches
                trending = self.pytrends.trending_searches(pn='spain')
                
                if not trending.empty:
                    results = trending[0].tolist()[:10]  # Top 10 trending searches
                    break
                    
            except Exception as e:
                logger.error(f"Error al obtener trending searches (intento {attempt + 1}): {str(e)}")
                
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Espera exponencial
                continue
        
        return results
