import os
from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

class Config:
    # Base paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    KEYWORDS_DIR = os.path.join(DATA_DIR, "keywords")

    # Ensure all directories exist
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(KEYWORDS_DIR, exist_ok=True)

    # Configuración de la aplicación
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev')
    DATABASE_PATH = os.path.join(DATA_DIR, "existing_content.db")

    # Configuración regional
    LANGUAGE = "es"
    COUNTRY = "CL"
    TIMEZONE = -180  # UTC-3 para Chile

    # URLs de servicios
    AUTOCOMPLETE_URL = 'https://suggestqueries.google.com/complete/search'
    PAA_URL = 'https://www.google.com/search'
    TRENDS_URL = 'https://trends.google.com/trends/api/explore'

    # Configuración de requests
    REQUEST_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    REQUEST_TIMEOUT = 10
    MAX_RETRIES = 3

    # Configuración de resultados
    MAX_RESULTS = 10
    MIN_KEYWORD_LENGTH = 3

    # Scraping parameters
    SIMILARITY_THRESHOLD = 0.7
    RATE_LIMIT_DELAY = 2  # seconds

    # Path configurations
    KEYWORD_PATHS = {
        "autocomplete": os.path.join(KEYWORDS_DIR, "autocomplete.csv"),
        "paa": os.path.join(KEYWORDS_DIR, "paa.csv"),
        "trends": os.path.join(KEYWORDS_DIR, "trends.csv"),
    }

    # Configuración de la base de datos
    BASE_DIR_SerpApi = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    DATA_DIR_SerpApi = os.path.join(BASE_DIR_SerpApi, 'keyword_idea_generator', 'data')
    DATABASE_PATH_SerpApi = os.path.join(DATA_DIR_SerpApi, 'keywords.db')
    
    # Configuración de SerpApi
    SERPAPI_KEY = os.environ.get('SERPAPI_KEY', '')  # Obtener la clave de la variable de entorno
    
    # URLs base
    GOOGLE_SEARCH_URL = 'https://www.google.cl/search'
    GOOGLE_TRENDS_URL = 'https://trends.google.com/trends/api/widgetdata/multiline'
