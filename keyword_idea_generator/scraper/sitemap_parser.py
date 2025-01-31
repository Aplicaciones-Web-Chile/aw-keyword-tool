import requests
from bs4 import BeautifulSoup
import sqlite3
from config import Config
import logging
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def parse_sitemap(sitemap_url):
    """Parse sitemap.xml and extract URLs with optional metadata"""
    try:
        response = requests.get(sitemap_url, headers=Config.REQUEST_HEADERS)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        urls = [loc.text for loc in soup.find_all('loc')]
        
        with sqlite3.connect(Config.DATABASE_PATH) as conn:
            cursor = conn.cursor()
            cursor.execute('''CREATE TABLE IF NOT EXISTS content
                            (url TEXT PRIMARY KEY,
                             title TEXT,
                             description TEXT)''')
            
            for url in urls:
                try:
                    cursor.execute('INSERT INTO content (url) VALUES (?)', (url,))
                    conn.commit()
                    
                    page_response = requests.get(url, headers=Config.REQUEST_HEADERS)
                    if page_response.ok:
                        page_soup = BeautifulSoup(page_response.text, 'html.parser')
                        title = page_soup.title.string.strip() if page_soup.title else ''
                        description = page_soup.find('meta', attrs={'name': 'description'})
                        description = description['content'].strip() if description else ''
                        
                        cursor.execute('''UPDATE content 
                                        SET title = ?, description = ?
                                        WHERE url = ?''', 
                                     (title, description, url))
                        conn.commit()
                        
                except sqlite3.IntegrityError:
                    conn.rollback()
                    continue
                except Exception as e:
                    logger.error(f"Error processing {url}: {str(e)}")
                    continue
                    
        return True
    except Exception as e:
        logger.error(f"Sitemap parsing failed: {str(e)}")
        return False
