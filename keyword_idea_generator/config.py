import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database configuration
    DATABASE_PATH = os.path.join(os.path.dirname(__file__), 'data/existing_content.db')
    
    # Scraping parameters
    SIMILARITY_THRESHOLD = 0.7
    RATE_LIMIT_DELAY = 2  # seconds
    REQUEST_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    
    # Path configurations
    KEYWORD_PATHS = {
        'autocomplete': 'data/keywords/autocomplete.csv',
        'paa': 'data/keywords/paa.csv',
        'trends': 'data/keywords/trends.csv'
    }
