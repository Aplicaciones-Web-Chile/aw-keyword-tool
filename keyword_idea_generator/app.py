from flask import Flask, request, jsonify, render_template, redirect, url_for, send_file
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

# Crear instancias de Flask y SocketIO
app = Flask(__name__)
app.config.from_object(Config)
socketio = SocketIO(app, cors_allowed_origins="*")

# Registrar namespace de WebSocket
socketio.on_namespace(AnalysisNamespace('/analysis'))

# Database initialization
def init_db():
    with sqlite3.connect(app.config["DATABASE_PATH"]) as conn:
        # Tabla para el contenido del sitemap
        conn.execute(
            """CREATE TABLE IF NOT EXISTS content
                     (url TEXT PRIMARY KEY,
                      title TEXT,
                      description TEXT)"""
        )

        # Tabla para keywords guardadas
        conn.execute(
            """CREATE TABLE IF NOT EXISTS saved_keywords
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      keyword TEXT NOT NULL,
                      type TEXT NOT NULL,
                      created_at DATETIME NOT NULL,
                      UNIQUE(keyword, type))"""
        )

init_db()

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        sitemap_url = request.form.get("sitemap_url")
        seed_keywords = request.form.get("seed_keywords", "").split(",")
        
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
    # Leer datos de los archivos CSV
    autocomplete_keywords = []
    paa_questions = []
    trends_keywords = []

    try:
        # Leer datos de Google Autocomplete
        with open(app.config["KEYWORD_PATHS"]["autocomplete"], "r", encoding="utf-8") as f:
            for line in f:
                term = line.strip()
                autocomplete_keywords.append({"term": term, "volume": None})
    except FileNotFoundError:
        pass

    try:
        # Leer datos de People Also Ask
        with open(app.config["KEYWORD_PATHS"]["paa"], "r", encoding="utf-8") as f:
            paa_questions = [line.strip() for line in f]
    except FileNotFoundError:
        pass

    try:
        # Leer datos de Google Trends
        with open(app.config["KEYWORD_PATHS"]["trends"], "r", encoding="utf-8") as f:
            for line in f:
                term = line.strip()
                trends_keywords.append({"term": term, "score": "N/A"})
    except FileNotFoundError:
        pass

    return render_template(
        "results.html",
        autocomplete_keywords=autocomplete_keywords,
        paa_questions=paa_questions,
        trends_keywords=trends_keywords,
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

@app.route("/export", methods=["POST"])
def export_keywords():
    try:
        export_type = request.form.get("type", "all")
        
        if export_type not in ["all", "autocomplete", "paa", "trends"]:
            return jsonify({"error": "Tipo de exportación inválido"}), 400

        # Crear un buffer para el CSV
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Keyword", "Tipo", "Fecha"])  # Encabezados

        keywords = []
        
        # Función helper para leer keywords
        def read_keywords_file(file_path, keyword_type):
            try:
                if os.path.exists(file_path):
                    with open(file_path, "r", encoding="utf-8") as f:
                        return [[line.strip(), keyword_type, ""] for line in f]
                return []
            except Exception as e:
                app.logger.error(f"Error leyendo {keyword_type}: {str(e)}")
                return []

        # Obtener datos según el tipo
        if export_type == "all":
            # Autocomplete keywords
            keywords.extend(read_keywords_file(
                app.config["KEYWORD_PATHS"]["autocomplete"],
                "autocomplete"
            ))

            # PAA keywords
            keywords.extend(read_keywords_file(
                app.config["KEYWORD_PATHS"]["paa"],
                "paa"
            ))

            # Trends keywords
            keywords.extend(read_keywords_file(
                app.config["KEYWORD_PATHS"]["trends"],
                "trends"
            ))
        else:
            keywords.extend(read_keywords_file(
                app.config["KEYWORD_PATHS"][export_type],
                export_type
            ))

        # Escribir datos al CSV
        for keyword in keywords:
            writer.writerow(keyword)

        # Convertir a bytes para send_file
        output.seek(0)
        bytes_output = BytesIO()
        bytes_output.write(output.getvalue().encode('utf-8-sig'))
        bytes_output.seek(0)
        output.close()

        return send_file(
            bytes_output,
            mimetype="text/csv",
            as_attachment=True,
            download_name="keywords.csv"
        )
    except Exception as e:
        app.logger.error(f"Error en exportación: {str(e)}")
        return jsonify({"error": f"Error en la exportación: {str(e)}"}), 500

def create_app():
    return app

if __name__ == "__main__":
    socketio.run(app, host="0.0.0.0", port=5004, debug=True)
