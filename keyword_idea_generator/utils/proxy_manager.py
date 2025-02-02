"""
Módulo para manejar la rotación de proxies y User-Agents.
"""
import random
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
import logging
import time
from fake_useragent import UserAgent

logger = logging.getLogger(__name__)

class ProxyManager:
    """Clase para manejar la rotación de proxies y User-Agents."""
    
    def __init__(self):
        self.proxies: List[Dict[str, str]] = []
        self.user_agent = UserAgent()
        self.last_update = 0
        self.update_interval = 3600  # Actualizar proxies cada hora
        
    def _fetch_free_proxies(self) -> List[Dict[str, str]]:
        """Obtener lista de proxies gratuitos desde múltiples fuentes."""
        proxies = []
        
        # Fuente 1: sslproxies.org
        try:
            response = requests.get('https://www.sslproxies.org/')
            soup = BeautifulSoup(response.text, 'html.parser')
            proxy_table = soup.find('table', class_='table table-striped table-bordered')
            
            for row in proxy_table.tbody.find_all('tr'):
                columns = row.find_all('td')
                if len(columns) >= 2:
                    ip = columns[0].text.strip()
                    port = columns[1].text.strip()
                    proxies.append({
                        'http': f'http://{ip}:{port}',
                        'https': f'http://{ip}:{port}'
                    })
        except Exception as e:
            logger.error(f"Error al obtener proxies de sslproxies.org: {str(e)}")
        
        # Fuente 2: free-proxy-list.net
        try:
            response = requests.get('https://free-proxy-list.net/')
            soup = BeautifulSoup(response.text, 'html.parser')
            proxy_table = soup.find('table', class_='table table-striped table-bordered')
            
            for row in proxy_table.tbody.find_all('tr'):
                columns = row.find_all('td')
                if len(columns) >= 7 and columns[6].text.strip() == 'yes':  # Solo HTTPS
                    ip = columns[0].text.strip()
                    port = columns[1].text.strip()
                    proxies.append({
                        'http': f'http://{ip}:{port}',
                        'https': f'http://{ip}:{port}'
                    })
        except Exception as e:
            logger.error(f"Error al obtener proxies de free-proxy-list.net: {str(e)}")
        
        return proxies
    
    def _test_proxy(self, proxy: Dict[str, str], timeout: int = 5) -> bool:
        """Probar si un proxy funciona."""
        try:
            test_url = 'https://www.google.com'
            headers = {'User-Agent': self.user_agent.random}
            response = requests.get(
                test_url,
                proxies=proxy,
                headers=headers,
                timeout=timeout
            )
            return response.status_code == 200
        except:
            return False
    
    def update_proxies(self) -> None:
        """Actualizar la lista de proxies si es necesario."""
        current_time = time.time()
        
        if current_time - self.last_update < self.update_interval:
            return
            
        logger.info("Actualizando lista de proxies...")
        new_proxies = self._fetch_free_proxies()
        working_proxies = []
        
        for proxy in new_proxies:
            if self._test_proxy(proxy):
                working_proxies.append(proxy)
                if len(working_proxies) >= 10:  # Mantener solo 10 proxies funcionales
                    break
        
        if working_proxies:
            self.proxies = working_proxies
            self.last_update = current_time
            logger.info(f"Se encontraron {len(working_proxies)} proxies funcionales")
        else:
            logger.warning("No se encontraron proxies funcionales")
    
    def get_proxy_and_headers(self) -> tuple[Optional[Dict[str, str]], Dict[str, str]]:
        """Obtener un proxy aleatorio y headers con User-Agent aleatorio."""
        self.update_proxies()
        
        headers = {
            'User-Agent': self.user_agent.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        if self.proxies:
            return random.choice(self.proxies), headers
        else:
            return None, headers
    
    def make_request(self, url: str, method: str = 'GET', **kwargs) -> Optional[requests.Response]:
        """
        Realizar una petición HTTP con reintentos y rotación de proxies.
        
        Args:
            url: URL a la que hacer la petición
            method: Método HTTP ('GET' o 'POST')
            **kwargs: Argumentos adicionales para requests
            
        Returns:
            Response object o None si fallan todos los intentos
        """
        max_retries = 3
        retry_delay = 2
        
        for attempt in range(max_retries):
            proxy, headers = self.get_proxy_and_headers()
            
            try:
                # Agregar headers a los existentes
                if 'headers' in kwargs:
                    kwargs['headers'].update(headers)
                else:
                    kwargs['headers'] = headers
                
                # Agregar proxy si está disponible
                if proxy:
                    kwargs['proxies'] = proxy
                
                # Realizar la petición
                if method.upper() == 'POST':
                    response = requests.post(url, **kwargs)
                else:
                    response = requests.get(url, **kwargs)
                
                if response.status_code == 200:
                    return response
                    
            except Exception as e:
                logger.error(f"Error en intento {attempt + 1}: {str(e)}")
            
            # Esperar antes de reintentar
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
        
        return None
