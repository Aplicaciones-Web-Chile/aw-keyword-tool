from flask import Flask, render_template, request, jsonify, redirect, url_for, send_file, flash
from .config import Config
import sqlite3
import json
import csv
from io import StringIO
from datetime import datetime
import os

from .scraper.sitemap_parser import SitemapParser
from .scraper.google_trends import GoogleTrends
from .scraper.google_paa import GooglePAA
from .scraper.google_autocomplete import GoogleAutocomplete

app = Flask(__name__)
app.config.from_object(Config)


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


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        sitemap_url = request.form["sitemap_url"]
        seed_keywords = request.form["seed_keywords"].split(",")

        # Process sitemap
        SitemapParser.parse_sitemap(sitemap_url)

        # Generate keywords
        for keyword in seed_keywords:
            GoogleAutocomplete.get_autocomplete_keywords(keyword.strip())
            GooglePAA.get_paa_keywords(keyword.strip())
            GoogleTrends.get_trends_keywords(keyword.strip())

        return redirect(url_for("results"))

    return render_template("index.html")


@app.route("/results")
def results():
    # Leer datos de los archivos CSV
    autocomplete_keywords = []
    paa_questions = []
    trends_keywords = []

    try:
        # Leer datos de Google Autocomplete
        with open(
            app.config["KEYWORD_PATHS"]["autocomplete"], "r", encoding="utf-8"
        ) as f:
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

        # Crear un buffer para el CSV
        si = StringIO()
        cw = csv.writer(si)
        cw.writerow(["Keyword", "Tipo", "Fecha"])  # Encabezados

        # Obtener datos según el tipo
        if export_type == "all":
            keywords = []
            # Autocomplete keywords
            with open(
                app.config["KEYWORD_PATHS"]["autocomplete"], "r", encoding="utf-8"
            ) as f:
                for line in f:
                    keywords.append([line.strip(), "autocomplete", ""])

            # PAA keywords
            with open(app.config["KEYWORD_PATHS"]["paa"], "r", encoding="utf-8") as f:
                for line in f:
                    keywords.append([line.strip(), "paa", ""])

            # Trends keywords
            with open(
                app.config["KEYWORD_PATHS"]["trends"], "r", encoding="utf-8"
            ) as f:
                for line in f:
                    keywords.append([line.strip(), "trends", ""])
        else:
            keywords = []
            with open(
                app.config["KEYWORD_PATHS"][export_type], "r", encoding="utf-8"
            ) as f:
                for line in f:
                    keywords.append([line.strip(), export_type, ""])

        # Escribir datos al CSV
        for keyword in keywords:
            cw.writerow(keyword)

        # Preparar el archivo para descarga
        output = si.getvalue()
        si.close()

        return send_file(
            StringIO(output), as_attachment=True, attachment_filename="keywords.csv"
        )
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5004, debug=True)
