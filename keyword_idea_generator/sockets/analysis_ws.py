from flask_socketio import Namespace, emit
from flask import request, current_app
from ..config import Config

class AnalysisNamespace(Namespace):
    def on_connect(self):
        """Manejador de conexión de cliente"""
        emit('connection_status', {'status': 'connected', 'client_id': request.sid})

    def on_start_analysis(self, data):
        """Inicia el análisis de una URL"""
        url = data.get('url')
        if not url:
            emit('error', {'message': 'URL requerida'})
            return
        
        try:
            # Notificar inicio de análisis
            emit('analysis_progress', {
                'progress': 10,
                'message': 'Iniciando análisis...',
                'url': url
            })

            # Simular progreso de análisis
            emit('analysis_progress', {
                'progress': 50,
                'message': 'Analizando contenido...',
                'url': url
            })

            # Notificar finalización
            emit('analysis_complete', {
                'progress': 100,
                'message': 'Análisis completado',
                'url': url,
                'results': {
                    'status': 'success',
                    'timestamp': current_app.config['ANALYSIS_TIMESTAMP']
                }
            })
        except Exception as e:
            current_app.logger.error(f"Error en análisis: {str(e)}")
            emit('error', {'message': f'Error durante el análisis: {str(e)}'})

    def on_disconnect(self):
        """Manejador de desconexión de cliente"""
        emit('connection_status', {'status': 'disconnected'})