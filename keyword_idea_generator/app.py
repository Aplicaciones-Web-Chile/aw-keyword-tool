import os
import sqlite3
import logging
from datetime import datetime
from flask import Flask, render_template, request, send_file, flash, redirect, url_for, jsonify, current_app, g
from flask_socketio import SocketIO
from .config import Config
from .scraper.google_paa import GooglePAA
from .scraper.google_trends import GoogleTrends
from .scraper.google_autocomplete import GoogleAutocomplete
from .scraper.google_paa_free import GooglePAAFree
from .scraper.google_trends_free import GoogleTrendsFree
from .scraper.google_autocomplete_free import GoogleAutocompleteFree

def get_db():
    """Obtener conexión a la base de datos"""
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE_PATH'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row
    
    return g.db

def init_db():
    """Inicializar la base de datos"""
    # Asegurar que el directorio data existe
    import os
    data_dir = os.path.join(os.path.dirname(current_app.config['DATABASE_PATH']))
    os.makedirs(data_dir, exist_ok=True)
    
    db = get_db()
    
    # Eliminar tablas existentes
    db.executescript('''
        DROP TABLE IF EXISTS autocomplete_results;
        DROP TABLE IF EXISTS paa_results;
        DROP TABLE IF EXISTS trends_results;
        DROP TABLE IF EXISTS saved_keywords;
        DROP TABLE IF EXISTS sitemaps;
        DROP TABLE IF EXISTS seed_keywords;
    ''')
    
    # Crear tablas nuevas
    db.executescript('''
        CREATE TABLE autocomplete_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            seed_keyword TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE paa_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            seed_keyword TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE trends_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL,
            seed_keyword TEXT NOT NULL,
            score INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE saved_keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE sitemaps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE seed_keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    ''')
    
    db.commit()

def create_app(test_config=None):
    """Crear y configurar la aplicación"""
    app = Flask(__name__)
    
    if test_config is None:
        app.config.from_object(Config)
    else:
        app.config.update(test_config)
        
    app.secret_key = app.config.get('SECRET_KEY', 'dev')
    
    # Inicializar la base de datos al crear la app
    with app.app_context():
        init_db()
    
    # Inicializar scrapers
    google_paa = GooglePAA(app.config.get('SERPAPI_KEY'))
    google_trends = GoogleTrends(app.config.get('SERPAPI_KEY'))
    google_autocomplete = GoogleAutocomplete(app.config.get('SERPAPI_KEY'))
    
    # Inicializar scrapers gratuitos
    google_paa_free = GooglePAAFree()
    google_trends_free = GoogleTrendsFree()
    google_autocomplete_free = GoogleAutocompleteFree()
    
    def close_db(e=None):
        """Cerrar conexión a la base de datos"""
        db = g.pop('db', None)
        if db is not None:
            db.close()
            
    app.teardown_appcontext(close_db)
    
    @app.route("/", methods=["GET", "POST"])
    def index():
        if request.method == "POST":
            sitemap_url = request.form.get("sitemap_url")
            seed_keywords = request.form.get("seed_keywords", "").strip()
            
            if not sitemap_url and not seed_keywords:
                flash("Por favor ingresa una URL de sitemap y al menos una palabra clave", "error")
                return render_template("index.html")
            
            if not sitemap_url:
                flash("Por favor ingresa una URL de sitemap", "error")
                return render_template("index.html")
            
            # Procesar keywords
            keywords = [k.strip() for k in seed_keywords.split("\n") if k.strip()]
            if not keywords:
                flash("Por favor ingresa al menos una palabra clave válida", "error")
                return render_template("index.html")
                
            try:
                # Guardar sitemap
                db = get_db()
                db.execute('INSERT OR REPLACE INTO sitemaps (url) VALUES (?)', [sitemap_url])
                
                # Procesar cada keyword
                for keyword in keywords:
                    try:
                        # Guardar keyword semilla
                        db.execute('''
                            INSERT OR REPLACE INTO seed_keywords (keyword)
                            VALUES (?)
                        ''', [keyword])
                        
                        # Intentar primero con los scrapers gratuitos
                        try:
                            # Obtener sugerencias de autocompletado
                            suggestions = google_autocomplete_free.get_suggestions_with_prefixes(keyword)
                            if suggestions:
                                for suggestion in suggestions:
                                    db.execute(
                                        'INSERT INTO autocomplete_results (keyword, seed_keyword) VALUES (?, ?)',
                                        [suggestion, keyword]
                                    )
                        except Exception as e:
                            app.logger.error(f"Error con autocompletado gratuito: {str(e)}")
                            # Fallback a SerpAPI
                            suggestions = google_autocomplete.get_suggestions(keyword)
                            for suggestion in suggestions:
                                db.execute(
                                    'INSERT INTO autocomplete_results (keyword, seed_keyword) VALUES (?, ?)',
                                    [suggestion, keyword]
                                )
                        
                        try:
                            # Obtener preguntas relacionadas
                            questions = google_paa_free.get_related_questions(keyword)
                            questions.extend(google_paa_free.get_questions_from_serp(keyword))
                            if questions:
                                for question in questions:
                                    db.execute(
                                        'INSERT INTO paa_results (keyword, seed_keyword) VALUES (?, ?)',
                                        [question, keyword]
                                    )
                        except Exception as e:
                            app.logger.error(f"Error con PAA gratuito: {str(e)}")
                            # Fallback a SerpAPI
                            questions = google_paa.get_questions(keyword)
                            for question in questions:
                                db.execute(
                                    'INSERT INTO paa_results (keyword, seed_keyword) VALUES (?, ?)',
                                    [question, keyword]
                                )
                        
                        try:
                            # Obtener tendencias relacionadas
                            trends = google_trends_free.get_related_queries(keyword)
                            if trends:
                                for trend in trends:
                                    db.execute(
                                        'INSERT INTO trends_results (keyword, seed_keyword, score) VALUES (?, ?, ?)',
                                        [trend['keyword'], keyword, trend['score']]
                                    )
                        except Exception as e:
                            app.logger.error(f"Error con trends gratuito: {str(e)}")
                            # Fallback a SerpAPI
                            trends = google_trends.get_related_keywords(keyword)
                            for trend in trends:
                                db.execute(
                                    'INSERT INTO trends_results (keyword, seed_keyword, score) VALUES (?, ?, ?)',
                                    [trend['keyword'], keyword, trend['score']]
                                )
                        
                        db.commit()
                        
                    except Exception as e:
                        app.logger.error(f"Error al procesar keyword {keyword}: {str(e)}")
                        flash(f'Error al procesar la palabra clave: {keyword}', 'error')
                        continue
                    
                db.commit()
                return redirect(url_for("results"))
                
            except Exception as e:
                app.logger.error(f"Error general procesando keywords: {str(e)}")
                flash("Error procesando las palabras clave. Por favor intenta de nuevo.", "error")
                return render_template("index.html")
                
        return render_template("index.html")

    @app.route("/results")
    def results():
        """Mostrar resultados de keywords"""
        db = get_db()
        
        # Obtener keywords semilla
        seed_keywords = db.execute('''
            SELECT DISTINCT keyword 
            FROM seed_keywords 
            ORDER BY created_at DESC
        ''').fetchall()
        
        results = {}
        for seed in seed_keywords:
            keyword = seed['keyword']
            results[keyword] = {
                'autocomplete': [
                    {'keyword': row['keyword']} 
                    for row in db.execute('''
                        SELECT keyword 
                        FROM autocomplete_results 
                        WHERE seed_keyword = ?
                    ''', [keyword]).fetchall()
                ],
                'paa': [
                    {'keyword': row['keyword']} 
                    for row in db.execute('''
                        SELECT keyword 
                        FROM paa_results 
                        WHERE seed_keyword = ?
                    ''', [keyword]).fetchall()
                ],
                'trends': [
                    {'keyword': row['keyword'], 'score': row['score']} 
                    for row in db.execute('''
                        SELECT keyword, score 
                        FROM trends_results 
                        WHERE seed_keyword = ?
                        ORDER BY score DESC
                    ''', [keyword]).fetchall()
                ]
            }
        
        return render_template("results.html", results=results)

    @app.route("/api/sitemaps", methods=["GET"])
    def get_sitemaps():
        """Obtener lista de sitemaps guardados"""
        db = get_db()
        sitemaps = db.execute('SELECT * FROM sitemaps ORDER BY created_at DESC').fetchall()
        return jsonify([dict(sitemap) for sitemap in sitemaps])

    @app.route("/api/sitemaps", methods=["POST"])
    def save_sitemap():
        """Guardar un nuevo sitemap"""
        url = request.json.get('url')
        
        if not url:
            return jsonify({"error": "URL es requerida"}), 400
            
        db = get_db()
        try:
            db.execute('INSERT OR REPLACE INTO sitemaps (url) VALUES (?)', [url])
            db.commit()
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/sitemaps", methods=["DELETE"])
    def delete_sitemap():
        """Eliminar un sitemap guardado"""
        url = request.json.get('url')
        
        if not url:
            return jsonify({"error": "URL es requerida"}), 400
            
        db = get_db()
        try:
            db.execute('DELETE FROM sitemaps WHERE url = ?', [url])
            db.commit()
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/keywords/manage", methods=["POST"])
    def manage_keywords():
        """Guardar o eliminar keyword favorita"""
        data = request.json
        keyword = data.get('keyword')
        action = data.get('action')
        
        if not keyword or action not in ['save', 'unsave']:
            return jsonify({"error": "Datos inválidos"}), 400
            
        db = get_db()
        try:
            if action == 'save':
                db.execute('''
                    INSERT OR REPLACE INTO saved_keywords (keyword)
                    VALUES (?)
                ''', [keyword])
            else:
                db.execute('DELETE FROM saved_keywords WHERE keyword = ?', [keyword])
                
            db.commit()
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/export", methods=["GET"])
    def export_keywords():
        """Exportar keywords a CSV"""
        export_type = request.args.get('type', 'all')
        
        db = get_db()
        keywords = []
        
        if export_type == 'all':
            # Exportar todas las keywords
            keywords = db.execute('''
                SELECT 'seed' as type, keyword FROM seed_keywords
                UNION ALL
                SELECT 'autocomplete' as type, keyword FROM autocomplete_results
                UNION ALL
                SELECT 'paa' as type, keyword FROM paa_results
                UNION ALL
                SELECT 'trends' as type, keyword FROM trends_results
            ''').fetchall()
        elif export_type == 'saved':
            # Exportar solo keywords guardadas
            keywords = db.execute('SELECT \'saved\' as type, keyword FROM saved_keywords').fetchall()
        
        # Generar CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(['tipo', 'keyword'])
        for k in keywords:
            writer.writerow([k['type'], k['keyword']])
        
        # Enviar archivo
        output.seek(0)
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={
                "Content-Disposition": f"attachment;filename=keywords_{export_type}.csv",
                "Content-Type": "text/csv"
            }
        )

    # Rutas API
    @app.route('/api/check_keyword', methods=['POST'])
    def check_keyword():
        """Verificar si una keyword existe en la base de datos"""
        try:
            data = request.get_json()
            keyword = data.get('keyword')
            
            if not keyword:
                return jsonify({'error': 'No se proporcionó una keyword'}), 400
            
            # Verificar en cada tabla
            db = get_db()
            exists = False
            
            # Verificar en autocomplete_results
            cursor = db.execute('SELECT 1 FROM autocomplete_results WHERE seed_keyword = ? LIMIT 1', [keyword])
            if cursor.fetchone():
                exists = True
            
            # Verificar en trends_results
            if not exists:
                cursor = db.execute('SELECT 1 FROM trends_results WHERE seed_keyword = ? LIMIT 1', [keyword])
                if cursor.fetchone():
                    exists = True
            
            # Verificar en paa_results
            if not exists:
                cursor = db.execute('SELECT 1 FROM paa_results WHERE seed_keyword = ? LIMIT 1', [keyword])
                if cursor.fetchone():
                    exists = True
            
            return jsonify({'exists': exists})
            
        except Exception as e:
            current_app.logger.error(f"Error al verificar keyword: {str(e)}")
            return jsonify({'error': 'Error interno del servidor'}), 500

    @app.route('/api/delete_keyword', methods=['POST'])
    def delete_keyword():
        """Eliminar una keyword y sus resultados de la base de datos"""
        try:
            data = request.get_json()
            keyword = data.get('keyword')
            
            if not keyword:
                return jsonify({'error': 'No se proporcionó una keyword'}), 400
            
            # Eliminar de todas las tablas
            db = get_db()
            
            db.execute('DELETE FROM autocomplete_results WHERE seed_keyword = ?', [keyword])
            db.execute('DELETE FROM trends_results WHERE seed_keyword = ?', [keyword])
            db.execute('DELETE FROM paa_results WHERE seed_keyword = ?', [keyword])
            
            db.commit()
            
            return jsonify({'success': True})
            
        except Exception as e:
            current_app.logger.error(f"Error al eliminar keyword: {str(e)}")
            return jsonify({'error': 'Error interno del servidor'}), 500

    return app

if __name__ == "__main__":
    app = create_app()
    socketio = SocketIO(app, cors_allowed_origins="*")
    socketio.run(app, host="0.0.0.0", port=5004, debug=True)
