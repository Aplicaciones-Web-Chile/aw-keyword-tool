import requests
from bs4 import BeautifulSoup
import sqlite3
from urllib.parse import urlparse
from ..config import Config
import logging

logger = logging.getLogger(__name__)

class SitemapParser:
    @staticmethod
    def parse_sitemap(sitemap_url):
        """Parse sitemap.xml and extract URLs with optional metadata"""
        try:
            response = requests.get(sitemap_url, headers=Config.REQUEST_HEADERS)
            response.raise_for_status()

            soup = BeautifulSoup(response.content, "xml")
            urls = soup.find_all("url")

            with sqlite3.connect(Config.DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    """CREATE TABLE IF NOT EXISTS content
                            (url TEXT PRIMARY KEY,
                             title TEXT,
                             description TEXT)"""
                )

                for url in urls:
                    loc = url.find("loc").text
                    title = url.find("title").text if url.find("title") else ""
                    description = url.find("description").text if url.find("description") else ""

                    cursor.execute(
                        """INSERT OR REPLACE INTO content (url, title, description)
                                     VALUES (?, ?, ?)""",
                        (loc, title, description),
                    )

                conn.commit()

            return True
        except Exception as e:
            logger.error(f"Error parsing sitemap: {str(e)}")
            return False
