import requests
import json
from urllib.parse import quote
import os
from ..config import Config
import logging
from flask import current_app, g

logger = logging.getLogger(__name__)

class GoogleAutocomplete:
    @staticmethod
    def get_autocomplete_keywords(keyword):
        """Obtener sugerencias de autocompletado de Google para una keyword"""
        try:
            # Configurar la sesión
            session = requests.Session()
            session.headers.update(Config.REQUEST_HEADERS)

            # Construir la URL con los parámetros correctos
            params = {
                "client": "firefox",
                "hl": "es",
                "gl": "CL",  # Región Chile
                "q": keyword
            }
            
            response = session.get(Config.AUTOCOMPLETE_URL, params=params)
            response.raise_for_status()
            
            suggestions = json.loads(response.text)[1]
            
            # Guardar resultados en la base de datos
            db = g.get_db()
            
            # Limpiar resultados anteriores para esta keyword
            db.execute('DELETE FROM autocomplete_results WHERE seed_keyword = ?', [keyword])
            
            # Insertar nuevos resultados
            for suggestion in suggestions:
                db.execute('''
                    INSERT INTO autocomplete_results (keyword, seed_keyword)
                    VALUES (?, ?)
                ''', [suggestion, keyword])
            
            db.commit()
            
            return suggestions
            
        except Exception as e:
            current_app.logger.error(f"Error en Google Autocomplete para '{keyword}': {str(e)}")
            return []
