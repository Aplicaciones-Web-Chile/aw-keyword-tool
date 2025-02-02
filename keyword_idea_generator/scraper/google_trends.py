import os
import sqlite3
import logging
from flask import current_app, g
from serpapi import GoogleSearch
import json
import re

logger = logging.getLogger(__name__)

class GoogleTrends:
    @staticmethod
    def get_main_keywords(keyword, max_words=3):
        """Extraer las palabras clave principales de una frase"""
        # Convertir a minúsculas y dividir en palabras
        words = keyword.lower().split()
        
        # Palabras comunes que queremos ignorar
        stop_words = {'de', 'la', 'el', 'los', 'las', 'un', 'una', 'unos', 'unas', 'y', 'o', 'para', 'por', 'con', 'sin', 'sobre', 'entre', 'tras', 'hacia'}
        
        # Filtrar palabras comunes y ordenar por longitud (asumiendo que palabras más largas son más significativas)
        main_words = [w for w in words if w not in stop_words]
        main_words.sort(key=len, reverse=True)
        
        # Tomar las primeras max_words palabras
        return ' '.join(main_words[:max_words])

    @staticmethod
    def get_trends_keywords(keyword):
        """Obtener palabras clave relacionadas de Google Trends usando SerpApi"""
        try:
            current_app.logger.info(f"Iniciando búsqueda de tendencias para keyword: {keyword}")
            
            # Extraer palabras clave principales
            main_keyword = GoogleTrends.get_main_keywords(keyword)
            current_app.logger.info(f"Palabras clave principales extraídas: {main_keyword}")
            
            # Configurar SerpApi
            params = {
                "engine": "google_trends",
                "q": main_keyword,
                "location": "Chile",
                "google_domain": "google.cl",
                "data_type": "RELATED_QUERIES",
                "cat": "0",
                "geo": "CL",
                "date": "today 12-m",
                "api_key": current_app.config['SERPAPI_KEY']
            }
            
            current_app.logger.info("Realizando búsqueda con SerpApi...")
            search = GoogleSearch(params)
            results = search.get_dict()
            
            # Guardar respuesta completa para debug
            debug_dir = os.path.join(current_app.config['DATA_DIR'], 'debug')
            os.makedirs(debug_dir, exist_ok=True)
            
            with open(os.path.join(debug_dir, 'last_trends_response.json'), 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            current_app.logger.info("Respuesta JSON guardada para debug")
            
            trends = []
            
            # Extraer tendencias
            if 'related_queries' in results:
                data = results['related_queries']
                
                # Procesar consultas principales
                if 'top' in data:
                    current_app.logger.info(f"Encontradas {len(data['top'])} consultas principales")
                    for item in data['top']:
                        if 'query' in item and 'value' in item:
                            trends.append({
                                'keyword': item['query'],
                                'score': int(item['value'])
                            })
                            current_app.logger.info(f"Tendencia encontrada: {item['query']} (score: {item['value']})")
            
            current_app.logger.info(f"Total de tendencias encontradas: {len(trends)}")
            
            # Guardar en base de datos
            if trends:
                current_app.logger.info("Guardando tendencias en la base de datos...")
                db = get_db()
                db.execute('DELETE FROM trends_results WHERE seed_keyword = ?', [keyword])
                
                for trend in trends:
                    db.execute('''
                        INSERT INTO trends_results (keyword, seed_keyword, score)
                        VALUES (?, ?, ?)
                    ''', [trend['keyword'], keyword, trend['score']])
                
                db.commit()
                current_app.logger.info("Tendencias guardadas exitosamente")
            else:
                current_app.logger.warning("No se encontraron tendencias para guardar")
            
            return trends
            
        except Exception as e:
            current_app.logger.error(f"Error en tendencias para '{keyword}': {str(e)}")
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
