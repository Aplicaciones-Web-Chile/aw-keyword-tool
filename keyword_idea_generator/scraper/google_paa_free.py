"""
Módulo para obtener preguntas relacionadas de Google (People Also Ask) sin usar SerpAPI.
"""
import logging
from typing import List
from urllib.parse import quote
from bs4 import BeautifulSoup
from ..utils.proxy_manager import ProxyManager

logger = logging.getLogger(__name__)

class GooglePAAFree:
    """Clase para obtener preguntas relacionadas de Google."""
    
    def __init__(self):
        self.proxy_manager = ProxyManager()
        self.base_url = 'https://www.google.com/search'
    
    def get_related_questions(self, keyword: str) -> List[str]:
        """
        Obtener preguntas relacionadas para una palabra clave.
        
        Args:
            keyword: Palabra clave a buscar
            
        Returns:
            Lista de preguntas relacionadas
        """
        results = []
        encoded_keyword = quote(keyword)
        
        # Parámetros de la petición
        params = {
            'q': keyword,
            'hl': 'es',  # Idioma español
            'gl': 'es',  # País España
            'ie': 'UTF-8',
        }
        
        # Hacer la petición
        response = self.proxy_manager.make_request(
            url=self.base_url,
            params=params,
            timeout=10
        )
        
        if response and response.status_code == 200:
            try:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Buscar el div que contiene las preguntas relacionadas
                paa_divs = soup.find_all('div', {'class': 'related-question-pair'})
                
                # Si no encontramos con esa clase, intentar con otras clases comunes
                if not paa_divs:
                    paa_divs = soup.find_all('div', {'jsname': 'N760b'})
                
                # Extraer el texto de las preguntas
                for div in paa_divs:
                    question = div.get_text().strip()
                    if question and len(question) > 10:  # Filtrar texto muy corto
                        results.append(question)
                
            except Exception as e:
                logger.error(f"Error al procesar respuesta de Google PAA: {str(e)}")
        
        return results
    
    def get_questions_from_serp(self, keyword: str) -> List[str]:
        """
        Obtener preguntas relacionadas analizando los resultados de búsqueda.
        
        Args:
            keyword: Palabra clave a buscar
            
        Returns:
            Lista de preguntas relacionadas
        """
        results = set()
        
        # Palabras clave interrogativas en español
        question_words = [
            'qué', 'cuál', 'cuáles', 'quién', 'quiénes',
            'dónde', 'cuándo', 'cuánto', 'cuántos', 'cuántas',
            'cómo', 'por qué', 'para qué'
        ]
        
        # Hacer la petición
        params = {
            'q': keyword,
            'hl': 'es',
            'gl': 'es',
            'num': 100,  # Intentar obtener 100 resultados
        }
        
        response = self.proxy_manager.make_request(
            url=self.base_url,
            params=params,
            timeout=10
        )
        
        if response and response.status_code == 200:
            try:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Buscar en títulos y snippets
                for element in soup.find_all(['h3', 'div'], {'class': ['r', 'st']}):
                    text = element.get_text().strip().lower()
                    
                    # Buscar frases que empiecen con palabras interrogativas
                    for word in question_words:
                        if text.startswith(word):
                            # Limpiar y normalizar la pregunta
                            question = text.capitalize()
                            if not question.endswith('?'):
                                question += '?'
                            
                            if len(question) > 10:  # Filtrar preguntas muy cortas
                                results.add(question)
                
            except Exception as e:
                logger.error(f"Error al procesar resultados de búsqueda: {str(e)}")
        
        return list(results)
