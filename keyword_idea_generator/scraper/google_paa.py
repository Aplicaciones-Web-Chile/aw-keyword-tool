import os
import sqlite3
import logging
from flask import current_app, g
from serpapi import GoogleSearch
import re

logger = logging.getLogger(__name__)

class GooglePAA:
    @staticmethod
    def get_paa_keywords(keyword):
        """Obtener preguntas relacionadas de Google PAA usando SerpApi"""
        try:
            current_app.logger.info(f"Iniciando búsqueda PAA para keyword: {keyword}")
            
            # Configurar SerpApi
            params = {
                "engine": "google",
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
            
            import json
            with open(os.path.join(debug_dir, 'last_paa_response.json'), 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            current_app.logger.info("Respuesta JSON guardada para debug")
            
            questions = []
            keywords = set(keyword.lower().split())
            
            # Extraer preguntas relacionadas
            if 'related_questions' in results:
                current_app.logger.info(f"Encontradas {len(results['related_questions'])} preguntas relacionadas")
                
                for question in results['related_questions']:
                    if 'question' in question:
                        q = question['question'].strip()
                        # Verificar que la pregunta tenga al menos una palabra clave
                        if len(q) > 15 and q not in questions and any(kw in q.lower() for kw in keywords):
                            questions.append(q)
                            current_app.logger.info(f"Pregunta encontrada: {q}")
            
            # Buscar preguntas en los snippets orgánicos
            if 'organic_results' in results:
                for result in results['organic_results']:
                    if 'snippet' in result:
                        text = result['snippet']
                        possible_questions = re.findall(r'[^.!?]*\?', text)
                        for q in possible_questions:
                            q = q.strip()
                            # Verificar que la pregunta tenga al menos una palabra clave
                            if len(q) > 15 and q not in questions and any(kw in q.lower() for kw in keywords):
                                questions.append(q)
                                current_app.logger.info(f"Pregunta encontrada en snippet: {q}")
            
            current_app.logger.info(f"Total de preguntas encontradas: {len(questions)}")
            
            # Guardar en base de datos
            if questions:
                current_app.logger.info("Guardando preguntas en la base de datos...")
                db = get_db()
                db.execute('DELETE FROM paa_results WHERE seed_keyword = ?', [keyword])
                
                for question in questions:
                    db.execute('''
                        INSERT INTO paa_results (keyword, seed_keyword)
                        VALUES (?, ?)
                    ''', [question, keyword])
                
                db.commit()
                current_app.logger.info("Preguntas guardadas exitosamente")
            else:
                current_app.logger.warning("No se encontraron preguntas para guardar")
            
            return questions
            
        except Exception as e:
            current_app.logger.error(f"Error en PAA para '{keyword}': {str(e)}")
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
