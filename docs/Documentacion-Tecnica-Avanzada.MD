 Documentación Técnica Avanzada

Documentación Técnica Avanzada: Generador de Ideas para Contenido Web
=====================================================================

**Versión:** 2.1 (Revisada)  
**Fecha:** 2025-01-31  
**Autor:** \[Tu Nombre o Equipo\]  
**Objetivo:** Automatizar la generación de ideas de contenido web basadas en análisis de un _sitemap_ y fuentes como Google Autocomplete, People Also Ask (PAA) y Google Trends.

* * *

Tabla de Contenidos
-------------------

1.  [Visión General](#visión-general)
2.  [Objetivos y Alcance](#objetivos-y-alcance)
3.  [Requerimientos Técnicos](#requerimientos-técnicos)
4.  [Arquitectura del Proyecto](#arquitectura-del-proyecto)
    *   [Estructura de Directorios](#estructura-de-directorios)
    *   [Diagrama de Componentes (Conceptual)](#diagrama-de-componentes-conceptual)
5.  [Flujo de Datos](#flujo-de-datos)
6.  [Diseño e Implementación](#diseño-e-implementación)
    *   [Módulo de Configuración (config.py)](#61-módulo-de-configuración-configpy)
    *   [Scrapers y Procesamiento](#62-scrapers-y-procesamiento)
    *   [Interfaz Web con Flask](#63-interfaz-web-con-flask)
    *   [Persistencia y Cache](#64-persistencia-y-cache)
7.  [Manejo de Errores y Seguridad](#manejo-de-errores-y-seguridad)
8.  [Pruebas y Validación](#pruebas-y-validación)
9.  [Despliegue y Operación](#despliegue-y-operación)
10.  [Mejoras Futuras y Roadmap](#mejoras-futuras-y-roadmap)
11.  [Instrucciones para el "Developer IA"](#instrucciones-para-el-developer-ia)
12.  [Referencias y Recursos](#referencias-y-recursos)

* * *

1\. Visión General
------------------

El **Generador de Ideas para Contenido Web** es una aplicación escrita en **Python** que:

1.  **Analiza** el contenido de un sitio leyendo su `sitemap.xml`.
2.  **Obtiene** nuevas palabras clave desde _Google Autocomplete_, _People Also Ask_ (con Playwright) y _Google Trends_ (con Pytrends).
3.  **Compara** las nuevas palabras clave con el contenido existente (usando un mecanismo de coincidencia parcial).
4.  **Presenta** resultados (nuevas oportunidades de contenido) mediante una **interfaz web** en Flask.
5.  **Permite** añadir manualmente nuevas ideas de contenido.

* * *

2\. Objetivos y Alcance
-----------------------

### Objetivos Principales

*   **Extracción de Contenido Existente**: Parsear el sitemap y, opcionalmente, scrapear cada URL para obtener títulos y descripciones.
*   **Generación de Keywords**: A partir de palabras semilla, usar Google Autocomplete, PAA y Trends para descubrir términos relevantes.
*   **Comparación (Fuzzy Matching)**: Determinar si una keyword ya está cubierta por el contenido del sitio.
*   **Interfaz Simple**: Mostrar todo en una aplicación web local con posibilidades de filtrar, añadir manualmente, etc.

### Alcance

*   **Scraping Responsable** (con rate limiting y, si es necesario, rotación de user-agents).
*   **Persistencia Ligera** con SQLite para el contenido y archivos CSV (o JSON) para almacenar las nuevas keywords.
*   **Modularidad**: Posibilidad de agregar más fuentes de datos en el futuro.

* * *

3\. Requerimientos Técnicos
---------------------------

*   **Python 3.10+**
*   **Librerías Clave**:
    *   `requests`, `beautifulsoup4`, `playwright`, `pytrends`, `flask`, `python-dotenv`, `difflib`, `logging`
*   **Base de Datos**: _SQLite_ (nativo de Python).
*   **Framework Web**: _Flask_.
*   **Despliegue**: Local o en un servicio que soporte aplicaciones Flask (Railway, Render, Docker, etc.).

* * *

4\. Arquitectura del Proyecto
-----------------------------

### 4.1. Estructura de Directorios

    keyword_idea_generator/
    ├── app.py                   # Punto de entrada (Flask + rutas).
    ├── config.py                # Configuración global.
    ├── scraper/                 # Módulos de scraping.
    │   ├── sitemap_parser.py        # Extrae URLs, títulos y descripciones del sitemap.
    │   ├── google_autocomplete.py   # Sugerencias de Google Autocomplete.
    │   ├── google_paa.py            # "People Also Ask" vía Playwright.
    │   └── google_trends.py         # Datos de Google Trends con Pytrends.
    ├── data/                    # Almacenamiento de datos.
    │   ├── existing_content.db      # SQLite (contenido actual).
    │   └── keywords/               # Carpeta con resultados CSV o JSON.
    │       ├── autocomplete.csv
    │       ├── paa.csv
    │       └── trends.csv
    ├── templates/               # Plantillas HTML (Flask).
    │   ├── base.html
    │   ├── index.html
    │   ├── results.html
    │   └── add_keyword.html
    ├── static/                  # Archivos estáticos (CSS, JS, imágenes).
    │   ├── css/
    │   │   └── style.css
    │   └── js/
    │       └── main.js
    ├── requirements.txt         # Dependencias del proyecto.
    └── README.md                # Documentación de uso.
    

### 4.2. Diagrama de Componentes (Conceptual)

    
    flowchart LR
        A[Sitemap.xml] --> B[sitemap_parser.py]
        B --> C[SQLite: existing_content.db]
    
        D[Seed Keywords] --> E[google_autocomplete.py]
        D --> F[google_paa.py]
        D --> G[google_trends.py]
    
        E --> E1[(autocomplete.csv)]
        F --> F1[(paa.csv)]
        G --> G1[(trends.csv)]
    
        C & E1 & F1 & G1 --> H[Fuzzy Matching & Análisis]
        H --> I[Flask App (app.py)]
        I --> J[Plantillas HTML (results.html)]
    

* * *

5\. Flujo de Datos
------------------

1.  **Sitemap**
    *   Extrae URLs (y meta) → **SQLite** (tabla: `content`).
2.  **Scrape de Keywords**
    *   **Google Autocomplete** → `autocomplete.csv`
    *   **People Also Ask** → `paa.csv`
    *   **Google Trends** → `trends.csv`
3.  **Fuzzy Matching**
    *   Se comparan las keywords con `existing_content.db` (títulos/descripciones) para determinar “Cubierta / No cubierta”.
4.  **Visualización**
    *   En Flask, se muestran tanto las URLs existentes como las nuevas keywords, indicando su origen y estatus.

* * *

6\. Diseño e Implementación
---------------------------

### 6.1. Módulo de Configuración (config.py)

Encargado de centralizar variables y ajustar parámetros (por ejemplo, `SIMILARITY_THRESHOLD`, `RATE_LIMIT_DELAY`, etc.). Puedes usar `.env` con `python-dotenv` para mayor flexibilidad.

### 6.2. Scrapers y Procesamiento

#### 6.2.1. `sitemap_parser.py`

*   **Función principal:** `parse_sitemap(sitemap_url)`.
*   Descarga `sitemap.xml`, extrae `<loc>` y, opcionalmente, scrapear la URL para obtener `<title>` y `<meta name="description">`.

#### 6.2.2. `google_autocomplete.py`

*   **Función:** `get_autocomplete_keywords(seed_keyword)`.
*   Usa la endpoint `http://suggestqueries.google.com/complete/search?client=firefox&q=`.

#### 6.2.3. `google_paa.py`

*   **Función:** `get_paa_keywords(seed_keyword)`.
*   Emplea **Playwright** en modo headless para obtener preguntas de "People Also Ask".

#### 6.2.4. `google_trends.py`

*   **Función:** `get_trends_keywords(seed_keyword)`.
*   Configura Pytrends (idioma, zona horaria) y obtiene “related queries”.

#### 6.2.5. Fuzzy Matching

*   **Función sugerida:** `match_keywords_with_content(keywords, content_rows)`.
*   Compara cada keyword con los títulos/descripciones usando, por ejemplo, `difflib.SequenceMatcher`.

### 6.3. Interfaz Web con Flask

`app.py` define rutas como:

*   **`/` (GET/POST)**: Para parametrizar el proceso (`sitemap_url`, `seed_keywords`, etc.).
*   **`/results` (GET)**: Muestra la tabla con URLs y la tabla de keywords (origen + estatus).
*   **`/add_keyword` (GET/POST)**: Permite añadir manualmente una nueva keyword.

Utiliza **templates** (`index.html`, `results.html`, etc.) y archivos **estáticos** (`style.css`, `main.js`) para presentar un dashboard básico.

### 6.4. Persistencia y Cache

*   **SQLite**:
    *   Tabla `content` con campos `url`, `title`, `description`.
*   **Archivos CSV**:
    *   Se guardan temporalmente las keywords de cada fuente (`autocomplete.csv`, etc.).
*   **Caching**:
    *   Evita repetir scraping si ya se hizo recientemente (por ejemplo, guardando timestamps).

* * *

7\. Manejo de Errores y Seguridad
---------------------------------

*   **Rate Limiting**: `time.sleep(RATE_LIMIT_DELAY)` para prevenir bloqueos.
*   **Rotación de User-Agents** (opcional).
*   **Excepciones**: Manejo con `try/except` y registro en logs (`logging` module).
*   **Localhost**: Ejecutar preferiblemente en localhost para no exponer la app de scraping públicamente.

* * *

8\. Pruebas y Validación
------------------------

1.  **Extracción de Sitemap**
    *   Verificar que URLs se almacenan en `existing_content.db`.
2.  **Scraping de Autocomplete**
    *   Probar con keywords de ejemplo y confirmar la correcta extracción.
3.  **People Also Ask**
    *   Validar que se obtengan preguntas y se guarden en `paa.csv`.
4.  **Interfaz Web**
    *   Comprobar que `/results` muestre todos los datos (URLs, keywords, estado).
5.  **Fuzzy Matching**
    *   Testear con ejemplos conocidos para confirmar clasificación.

* * *

9\. Despliegue y Operación
--------------------------

*   **Local**:
    
        flask run --host=0.0.0.0 --port=5000 # Visitar http://localhost:5000/ 
    
*   **Producción** (Opciones):
    *   **Docker**: Crear `Dockerfile` y desplegar en servicios como _Railway_, _Render_, etc.
    *   **Heroku**: `Procfile` con `web: python app.py` y `runtime.txt` (Python 3.10+).
    *   **Netlify**: No es el destino ideal para Flask, pero podría usarse con Netlify Functions + contenedor Docker.

* * *

10\. Mejoras Futuras y Roadmap
------------------------------

1.  **Integrar NLP** (por ejemplo, spaCy) para comparaciones semánticas más avanzadas.
2.  **Dashboard Interactivo** con gráficos (Plotly, Chart.js) de tendencias.
3.  **Automatización** con un _cron job_ (Linux) o Task Scheduler (Windows).
4.  **Integración con CMS** (WordPress, Drupal, etc.) para crear borradores automáticamente.
5.  **Cache Avanzado** que evite completamente repeticiones de scraping durante un período (ej. 24-72 h).

* * *

11\. Instrucciones para el "Developer IA"
-----------------------------------------

En esta sección final, se detallan los pasos **exactos** que tu _Developer IA_ (Windsurf, Codeium, etc.) puede seguir para **generar** el código **en la secuencia lógica** sin que tengas que intervenir manualmente:

1.  **Crear la Carpeta de Proyecto**
    *   Nombre sugerido: `keyword_idea_generator`.
    *   Incluir un `requirements.txt` con las librerías indicadas.
2.  **Generar un Entorno Virtual** (si aplica) y el Esqueleto de Flask
    *   `app.py` con una ruta mínima `@app.route('/')` que devuelva "Hello World" para probar.
3.  **Configurar la Estructura de Directorios**
    *   `scraper/`, `data/`, `templates/`, `static/`, etc.
4.  **Crear `sitemap_parser.py`**
    *   Función: `parse_sitemap(sitemap_url)` que baje y parsee el XML del sitemap.
5.  **Crear Módulos de Scraping de Keywords**
    *   `google_autocomplete.py` con `get_autocomplete_keywords(keyword)`.
    *   `google_paa.py` con `get_paa_keywords(keyword)` usando Playwright.
    *   `google_trends.py` con `get_trends_keywords(keyword)` usando Pytrends.
6.  **Implementar el Sistema de Persistencia**
    *   **SQLite** para almacenar contenido del sitemap (tabla `content`).
    *   **CSV** en `data/keywords/` para guardar las nuevas keywords.
7.  **Agregar Lógica de Fuzzy Matching**
    *   Por ejemplo, en un archivo `core/fuzzy_match.py` (o dentro de `sitemap_parser.py`) con la función `match_keywords_with_content(...)`.
8.  **Diseñar las Rutas Flask en `app.py`**
    *   **`/` (GET/POST)**: formulario para ingresar el URL del sitemap y seed keywords.
    *   **`/results` (GET)**: muestra la lista de URLs y las keywords (cubiertas / no cubiertas).
    *   **`/add_keyword` (GET/POST)**: permite añadir una keyword manualmente.
9.  **Generar Plantillas y Archivos Estáticos**
    *   `base.html` (layout), `index.html`, `results.html`, `add_keyword.html`.
    *   **CSS** (estilos básicos) y **JS** (lógica de frontend opcional).
10.  **Realizar Pruebas**
    *   _Caso 1_: Verificar extracción del sitemap.
    *   _Caso 2_: Autocomplete con seed keywords.
    *   _Caso 3_: PAA con Playwright.
    *   _Caso 4_: Google Trends.
    *   _Caso 5_: Fuzzy matching con contenido existente.
11.  **Documentar y Mejorar**
    *   Crear o actualizar el `README.md` con instrucciones de instalación y uso final.
    *   (Opcional) Crear un `Dockerfile` si se desea desplegar en contenedores.

**Resultado**: Al completar estos pasos, tu IA generará los archivos necesarios y tu proyecto quedará totalmente funcional _sin que toques manualmente el código_.

* * *

12\. Referencias y Recursos
---------------------------

*   **Flask**: [Documentación Oficial](https://flask.palletsprojects.com/)
*   **BeautifulSoup**: [Sitio Oficial](https://www.crummy.com/software/BeautifulSoup/)
*   **Playwright**: [Playwright para Python](https://playwright.dev/python/)
*   **Pytrends**: [Pytrends en GitHub](https://github.com/GeneralMills/pytrends)
*   **difflib**: [Documentación en Python](https://docs.python.org/3/library/difflib.html)
*   **Despliegue en Docker**: [Documentación de Docker](https://docs.docker.com/)