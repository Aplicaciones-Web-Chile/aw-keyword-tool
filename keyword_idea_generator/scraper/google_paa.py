import requests
from bs4 import BeautifulSoup
import pandas as pd
from ..config import Config
import logging

logger = logging.getLogger(__name__)

class GooglePAA:
    @staticmethod
    def get_paa_keywords(keyword):
        """Get 'People Also Ask' questions from Google"""
        try:
            url = f"https://www.google.com/search?q={keyword}"
            response = requests.get(url, headers=Config.REQUEST_HEADERS)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            paa_questions = soup.find_all("div", {"class": "related-question-pair"})
            
            questions = []
            for question in paa_questions:
                questions.append(question.text.strip())
            
            if questions:
                df = pd.DataFrame(questions, columns=["question"])
                df.to_csv(f"{Config.KEYWORDS_DIR}/paa_{keyword}.csv", index=False)
                return True
            
            return False
        except Exception as e:
            logger.error(f"Error getting PAA questions: {str(e)}")
            return False
