import os
import sqlite3
import logging
from flask import current_app, g
from serpapi import GoogleSearch
import json

logger = logging.getLogger(__name__)

class GoogleAutocomplete:
    @staticmethod
    def get_autocomplete_keywords(keyword):
        """Obtener sugerencias de autocompletado de Google para una keyword usando SerpApi"""
        try:
            current_app.logger.info(f"Iniciando búsqueda de autocompletado para keyword: {keyword}")
            
            # Configurar SerpApi
            params = {
                "engine": "google_autocomplete",
                "q": keyword,
                "location": "Chile",
                "google_domain": "google.cl",
                "gl": "cl",
                "hl": "es",
                "api_key": current_app.config['SERPAPI_KEY']
            }
            
            current_app.logger.info("Realizando búsqueda con SerpApi...")
            search = GoogleSearch(params)
            results = search.get_dict()
            
            # Guardar respuesta completa para debug
            debug_dir = os.path.join(current_app.config['DATA_DIR'], 'debug')
            os.makedirs(debug_dir, exist_ok=True)
            
            with open(os.path.join(debug_dir, 'last_autocomplete_response.json'), 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            current_app.logger.info("Respuesta JSON guardada para debug")
            
            suggestions = []
            
            # Extraer sugerencias
            if 'suggestions' in results:
                current_app.logger.info(f"Encontradas {len(results['suggestions'])} sugerencias")
                
                for suggestion in results['suggestions']:
                    if 'value' in suggestion:
                        suggestions.append(suggestion['value'])
                        current_app.logger.info(f"Sugerencia encontrada: {suggestion['value']}")
            
            current_app.logger.info(f"Total de sugerencias encontradas: {len(suggestions)}")
            
            # Guardar en base de datos
            if suggestions:
                current_app.logger.info("Guardando sugerencias en la base de datos...")
                db = get_db()
                db.execute('DELETE FROM autocomplete_results WHERE seed_keyword = ?', [keyword])
                
                for suggestion in suggestions:
                    db.execute('''
                        INSERT INTO autocomplete_results (keyword, seed_keyword)
                        VALUES (?, ?)
                    ''', [suggestion, keyword])
                
                db.commit()
                current_app.logger.info("Sugerencias guardadas exitosamente")
            else:
                current_app.logger.warning("No se encontraron sugerencias para guardar")
            
            return suggestions
            
        except Exception as e:
            current_app.logger.error(f"Error en autocompletado para '{keyword}': {str(e)}")
            return []

def get_db():
    """Obtener conexión a la base de datos"""
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE_PATH'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    return g.db
