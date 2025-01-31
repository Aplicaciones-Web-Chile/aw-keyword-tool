from playwright.sync_api import sync_playwright
import logging
from config import Config
import time

logger = logging.getLogger(__name__)

def get_paa_keywords(seed_keyword):
    """Obtiene preguntas de 'People Also Ask' usando Playwright"""
    paa_items = []
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            
            page.goto(f"https://www.google.com/search?q={seed_keyword}")
            page.wait_for_selector('.related-question-pair', timeout=10000)
            
            questions = page.query_selector_all('.related-question-pair')
            for q in questions:
                question_text = q.inner_text().strip()
                if question_text:
                    paa_items.append(question_text)
            
            browser.close()
            
            time.sleep(Config.RATE_LIMIT_DELAY)
            
    except Exception as e:
        logger.error(f"Error en PAA para {seed_keyword}: {str(e)}")
    
    return paa_items
