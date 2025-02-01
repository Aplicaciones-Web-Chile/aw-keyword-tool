import requests
from bs4 import BeautifulSoup
import pandas as pd
from urllib.parse import quote, urlencode
import os
from ..config import Config
import logging

logger = logging.getLogger(__name__)

class GooglePAA:
    @staticmethod
    def get_paa_keywords(keyword):
        """Obtener preguntas relacionadas de Google PAA"""
        try:
            # Configurar la sesión
            session = requests.Session()
            session.headers.update(Config.REQUEST_HEADERS)

            # Construir la URL con los parámetros correctos
            params = {
                "hl": "es",
                "gl": "CL",  # Región Chile
                "q": keyword
            }
            
            response = session.get(Config.SEARCH_URL, params=params)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'lxml')
            questions = []
            
            # Buscar las preguntas en el HTML
            paa_divs = soup.find_all('div', {'class': 'related-question-pair'})
            for div in paa_divs:
                question = div.get_text().strip()
                if question:
                    questions.append(question)
            
            # Guardar resultados en la base de datos
            from flask import current_app, g
            db = g.get_db()
            
            # Limpiar resultados anteriores para esta keyword
            db.execute('DELETE FROM paa_results WHERE seed_keyword = ?', [keyword])
            
            # Insertar nuevos resultados
            for question in questions:
                db.execute('''
                    INSERT INTO paa_results (keyword, seed_keyword)
                    VALUES (?, ?)
                ''', [question, keyword])
            
            db.commit()
            
            return questions
            
        except Exception as e:
            current_app.logger.error(f"Error en Google PAA para '{keyword}': {str(e)}")
            return []
