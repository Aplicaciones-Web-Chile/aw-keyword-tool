# Generador de Ideas para Contenido Web 🚀

Una herramienta profesional para generar ideas de contenido web basada en datos de Google Autocomplete, People Also Ask y Google Trends.

## 🌟 Características

- 🔍 Análisis de palabras clave de Google Autocomplete
- ❓ Extracción de preguntas frecuentes (People Also Ask)
- 📈 Integración con datos de Google Trends
- 💾 Exportación de datos a CSV
- 📱 Interfaz responsive y moderna
- 🔄 Paginación y ordenamiento de resultados

## 🛠️ Tecnologías

- Python 3.8+
- Flask
- SQLite
- Bootstrap 5
- DataTables
- jQuery
- Font Awesome

## 📋 Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)
- Navegador web moderno

## 🚀 Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/yourusername/aw-keyword-tool.git
cd aw-keyword-tool
```

2. Crear y activar entorno virtual:
```bash
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
```

3. Instalar dependencias:
```bash
pip install -r requirements.txt
```

4. Configurar variables de entorno:
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

5. Iniciar la aplicación:
```bash
cd keyword_idea_generator
python app.py
```

La aplicación estará disponible en `http://localhost:5004`

## 🔧 Configuración

La configuración se realiza a través del archivo `config.py`. Los principales parámetros son:

- `DATABASE_PATH`: Ruta de la base de datos SQLite
- `KEYWORD_PATHS`: Rutas de los archivos de palabras clave
- `MAX_KEYWORDS`: Número máximo de palabras clave a generar

## 📖 Uso

1. Ingresa la URL del sitemap de tu sitio web
2. Añade palabras clave semilla
3. La herramienta generará:
   - Sugerencias de autocompletado de Google
   - Preguntas frecuentes relacionadas
   - Términos relacionados de Google Trends
4. Exporta los resultados en formato CSV

## 🤝 Contribuir

Las contribuciones son bienvenidas. Por favor, sigue estos pasos:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📝 Licencia

Este proyecto está bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## ✨ Autor

AplicacionesWeb - [@aplicacionesweb](https://github.com/Aplicaciones-Web-Chile/)

## 📞 Soporte

Para soporte, email juan@jorquera.com o abre un issue en GitHub.
