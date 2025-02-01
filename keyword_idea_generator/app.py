from flask import Flask, request, jsonify, render_template, redirect, url_for, send_file, g
from flask_socketio import SocketIO
import sqlite3
import csv
from io import StringIO, BytesIO
import os
from .config import Config
from .scraper.sitemap_parser import SitemapParser
from .scraper.google_trends import GoogleTrends
from .scraper.google_paa import GooglePAA
from .scraper.google_autocomplete import GoogleAutocomplete
from .sockets.analysis_ws import AnalysisNamespace
from urllib.parse import urlparse
from datetime import datetime

# Crear instancias de Flask y SocketIO
app = Flask(__name__)
app.config.from_object(Config)
socketio = SocketIO(app, cors_allowed_origins="*")

# Registrar namespace de WebSocket
socketio.on_namespace(AnalysisNamespace('/analysis'))

# Database initialization
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(Config.DATABASE_PATH)
        g.db.row_factory = sqlite3.Row
    return g.db

def init_db():
    db = get_db()
    
    # Crear tabla de dominios si no existe
    db.execute('''
        CREATE TABLE IF NOT EXISTS domains (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            sitemap_url TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Crear tabla de keywords guardadas si no existe
    db.execute('''
        CREATE TABLE IF NOT EXISTS saved_keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            type TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabla para el contenido del sitemap
    db.execute(
        """CREATE TABLE IF NOT EXISTS content
                 (url TEXT PRIMARY KEY,
                  title TEXT,
                  description TEXT)"""
    )
    
    # Tablas para resultados de análisis
    db.execute('''
        CREATE TABLE IF NOT EXISTS autocomplete_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            seed_keyword TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    db.execute('''
        CREATE TABLE IF NOT EXISTS paa_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            seed_keyword TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    db.execute('''
        CREATE TABLE IF NOT EXISTS trends_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            seed_keyword TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    db.commit()

@app.teardown_appcontext
def close_db(error):
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Inicializar la base de datos al inicio
with app.app_context():
    init_db()

@app.route("/api/domains", methods=["GET"])
def get_domains():
    """Obtener lista de dominios guardados"""
    db = get_db()
    domains = db.execute('SELECT * FROM domains ORDER BY created_at DESC').fetchall()
    return jsonify([dict(domain) for domain in domains])

@app.route("/api/domains", methods=["POST"])
def save_domain():
    """Guardar un nuevo dominio"""
    sitemap_url = request.json.get('sitemap_url')
    name = request.json.get('name')
    
    if not sitemap_url:
        return jsonify({"error": "URL del sitemap es requerida"}), 400
        
    # Si no se proporciona un nombre, extraer del sitemap_url
    if not name:
        parsed = urlparse(sitemap_url)
        name = parsed.netloc
    
    db = get_db()
    db.execute('INSERT INTO domains (name, sitemap_url) VALUES (?, ?)',
               [name, sitemap_url])
    db.commit()
    
    return jsonify({"success": True, "name": name})

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        sitemap_url = request.form.get("sitemap_url")
        seed_keywords = request.form.get("seed_keywords", "").split("\n")
        
        if not sitemap_url:
            return jsonify({"error": "URL del sitemap es requerida"}), 400
            
        if not seed_keywords or not seed_keywords[0]:
            return jsonify({"error": "Se requieren palabras clave semilla"}), 400

        try:
            # Process sitemap
            if not SitemapParser.parse_sitemap(sitemap_url):
                return jsonify({"error": "URL del sitemap inválida o inaccesible"}), 400

            # Generate keywords
            for keyword in seed_keywords:
                if keyword.strip():
                    try:
                        GoogleAutocomplete.get_autocomplete_keywords(keyword.strip())
                        GooglePAA.get_paa_keywords(keyword.strip())
                        GoogleTrends.get_trends_keywords(keyword.strip())
                    except Exception as e:
                        app.logger.error(f"Error procesando keyword {keyword}: {str(e)}")

            return redirect(url_for("results"))
        except Exception as e:
            app.logger.error(f"Error en el procesamiento: {str(e)}")
            return jsonify({"error": str(e)}), 400

    return render_template("index.html")

@app.route("/results")
def results():
    """Mostrar resultados del análisis"""
    keywords = {}
    db = get_db()
    
    # Obtener todas las keywords guardadas
    saved_keywords = {row['keyword'] for row in db.execute('SELECT keyword FROM saved_keywords').fetchall()}
    
    # Obtener keywords por tipo y agruparlas por keyword semilla
    for type_name in ['autocomplete', 'paa', 'trends']:
        rows = db.execute(f'SELECT keyword, seed_keyword FROM {type_name}_results ORDER BY created_at DESC').fetchall()
        for row in rows:
            seed = row['seed_keyword']
            if seed not in keywords:
                keywords[seed] = {'autocomplete': [], 'paa': [], 'trends': []}
            keywords[seed][type_name].append(row['keyword'])
    
    return render_template('results.html', keywords=keywords, saved_keywords=saved_keywords)

@app.route("/api/keywords", methods=["POST"])
def manage_keywords():
    """Guardar o eliminar keywords"""
    data = request.json
    keyword = data.get('keyword')
    action = data.get('action')
    
    if not keyword or action not in ['save', 'unsave']:
        return jsonify({"error": "Parámetros inválidos"}), 400
    
    db = get_db()
    try:
        if action == 'save':
            db.execute('INSERT INTO saved_keywords (keyword, type) VALUES (?, ?)',
                      [keyword, 'manual'])
        else:
            db.execute('DELETE FROM saved_keywords WHERE keyword = ?', [keyword])
        db.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/export")
def export_keywords():
    """Exportar keywords a CSV"""
    export_type = request.args.get('type', 'all')
    db = get_db()
    
    if export_type == 'selected':
        rows = db.execute('SELECT keyword, type FROM saved_keywords ORDER BY created_at DESC').fetchall()
    else:
        # Obtener todas las keywords de todos los tipos
        keywords = []
        for type_name in ['autocomplete', 'paa', 'trends']:
            type_keywords = db.execute(f'SELECT keyword, seed_keyword, ? as type FROM {type_name}_results',
                                     [type_name]).fetchall()
            keywords.extend(type_keywords)
        rows = keywords
    
    # Crear CSV en memoria
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Keyword', 'Tipo', 'Keyword Semilla'])
    
    for row in rows:
        writer.writerow([row['keyword'], row['type'], row.get('seed_keyword', '')])
    
    # Enviar archivo
    output.seek(0)
    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'keywords_{export_type}_{datetime.now().strftime("%Y%m%d")}.csv'
    )

@app.route("/add_keyword", methods=["GET", "POST"])
def add_keyword():
    if request.method == "POST":
        # Handle manual keyword addition
        pass
    return render_template("add_keyword.html")

@app.route("/save_keyword", methods=["POST"])
def save_keyword():
    try:
        keyword = request.form.get("keyword")
        keyword_type = request.form.get("type")

        # Guardar en la base de datos
        with sqlite3.connect(app.config["DATABASE_PATH"]) as conn:
            conn.execute(
                """INSERT OR IGNORE INTO saved_keywords 
                          (keyword, type, created_at) 
                          VALUES (?, ?, datetime('now'))""",
                (keyword, keyword_type),
            )

        return jsonify({"success": True, "message": "Keyword guardada correctamente"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

def create_app():
    return app

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5004, debug=True)
