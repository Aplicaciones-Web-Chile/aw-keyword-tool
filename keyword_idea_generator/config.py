import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Base paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    KEYWORDS_DIR = os.path.join(DATA_DIR, "keywords")

    # Ensure directories exist
    os.makedirs(KEYWORDS_DIR, exist_ok=True)

    # Database configuration
    DATABASE_PATH = os.path.join(DATA_DIR, "existing_content.db")

    # Scraping parameters
    SIMILARITY_THRESHOLD = 0.7
    RATE_LIMIT_DELAY = 2  # seconds
    REQUEST_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    # Search parameters
    LANGUAGE = "es"
    COUNTRY = "CL"
    TIMEZONE = -180  # UTC-3 para Chile

    # Path configurations
    KEYWORD_PATHS = {
        "autocomplete": os.path.join(KEYWORDS_DIR, "autocomplete.csv"),
        "paa": os.path.join(KEYWORDS_DIR, "paa.csv"),
        "trends": os.path.join(KEYWORDS_DIR, "trends.csv"),
    }
