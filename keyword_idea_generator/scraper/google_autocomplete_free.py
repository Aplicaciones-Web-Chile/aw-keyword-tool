"""
Módulo para obtener sugerencias de autocompletado de Google sin usar SerpAPI.
"""
import logging
from typing import List, Optional
from urllib.parse import quote
import json
from ..utils.proxy_manager import ProxyManager

logger = logging.getLogger(__name__)

class GoogleAutocompleteFree:
    """Clase para obtener sugerencias de autocompletado de Google."""
    
    def __init__(self):
        self.proxy_manager = ProxyManager()
        self.base_url = 'https://suggestqueries.google.com/complete/search'
    
    def get_suggestions(self, keyword: str) -> List[str]:
        """
        Obtener sugerencias de autocompletado para una palabra clave.
        
        Args:
            keyword: Palabra clave a buscar
            
        Returns:
            Lista de sugerencias de autocompletado
        """
        results = []
        encoded_keyword = quote(keyword)
        
        # Parámetros de la petición
        params = {
            'client': 'chrome',  # Simular Chrome
            'q': keyword,
            'hl': 'es',  # Idioma español
            'gl': 'es',  # País España
            'callback': 'callback'  # JSONP callback
        }
        
        # Hacer la petición
        response = self.proxy_manager.make_request(
            url=self.base_url,
            params=params,
            timeout=10
        )
        
        if response and response.status_code == 200:
            try:
                # Extraer JSON del JSONP
                text = response.text
                json_str = text[text.index('(') + 1:text.rindex(')')]
                data = json.loads(json_str)
                
                # Las sugerencias están en el segundo elemento
                if len(data) > 1 and isinstance(data[1], list):
                    results = data[1]
                    
            except Exception as e:
                logger.error(f"Error al procesar respuesta de Google Autocomplete: {str(e)}")
        
        return results
    
    def get_suggestions_with_prefixes(self, keyword: str) -> List[str]:
        """
        Obtener sugerencias usando diferentes prefijos y sufijos.
        
        Args:
            keyword: Palabra clave base
            
        Returns:
            Lista combinada de sugerencias
        """
        all_suggestions = set()
        
        # Prefijos comunes en español
        prefixes = [
            'como', 'que', 'cuando', 'donde', 'quien',
            'por que', 'para que', 'cual', 'cuanto',
            'mejor', 'peor', 'vs', 'versus',
        ]
        
        # Obtener sugerencias para la keyword base
        base_suggestions = self.get_suggestions(keyword)
        all_suggestions.update(base_suggestions)
        
        # Obtener sugerencias con cada prefijo
        for prefix in prefixes:
            prefixed_keyword = f"{prefix} {keyword}"
            suggestions = self.get_suggestions(prefixed_keyword)
            all_suggestions.update(suggestions)
        
        # Obtener sugerencias con la keyword como prefijo
        suffixed_suggestions = self.get_suggestions(f"{keyword} ")
        all_suggestions.update(suffixed_suggestions)
        
        return list(all_suggestions)
