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
        """Obtener keywords relacionadas de Google Trends"""
        try:
            pytrends = TrendReq(hl='es', tz=Config.TIMEZONE)
            
            # Construir payload con configuración regional
            pytrends.build_payload(
                [keyword],
                cat=0,
                timeframe='today 12-m',
                geo='CL'  # Chile
            )
            
            # Obtener sugerencias relacionadas
            related = pytrends.related_queries()
            suggestions = []
            
            if keyword in related and 'top' in related[keyword]:
                df = related[keyword]['top']
                if not df.empty:
                    suggestions = df['query'].tolist()
            
            # Guardar resultados en la base de datos
            from flask import current_app, g
            db = g.get_db()
            
            # Limpiar resultados anteriores para esta keyword
            db.execute('DELETE FROM trends_results WHERE seed_keyword = ?', [keyword])
            
            # Insertar nuevos resultados
            for suggestion in suggestions:
                db.execute('''
                    INSERT INTO trends_results (keyword, seed_keyword)
                    VALUES (?, ?)
                ''', [suggestion, keyword])
            
            db.commit()
            
            return suggestions
            
        except Exception as e:
            current_app.logger.error(f"Error en Google Trends para '{keyword}': {str(e)}")
            return []
