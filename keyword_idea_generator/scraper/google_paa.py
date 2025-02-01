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
        """Get 'People Also Ask' questions from Google"""
        try:
            params = {
                'q': keyword,
                'hl': Config.LANGUAGE,
                'gl': Config.COUNTRY,
                'ie': 'utf8',
                'oe': 'utf8'
            }
            url = f"https://www.google.com/search?{urlencode(params)}"
            
            response = requests.get(url, headers=Config.REQUEST_HEADERS)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            paa_questions = soup.find_all("div", {"class": "related-question-pair"})
            
            questions = []
            for question in paa_questions:
                questions.append(question.text.strip())
            
            if questions:
                # Crear un nombre de archivo seguro
                safe_keyword = quote(keyword, safe='')
                output_file = os.path.join(Config.KEYWORDS_DIR, f"paa_{safe_keyword}.csv")
                
                df = pd.DataFrame(questions, columns=["question"])
                df.to_csv(output_file, index=False, encoding='utf-8-sig')
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error getting PAA questions: {str(e)}")
            return False
