import os
import tempfile
import pytest
from keyword_idea_generator.app import create_app
from keyword_idea_generator.config import Config

@pytest.fixture
def app():
    """Crear aplicación de prueba"""
    db_fd, db_path = tempfile.mkstemp()
    app = create_app({
        'TESTING': True,
        'DATABASE_PATH': db_path,
        'SECRET_KEY': 'test'
    })
    
    with app.app_context():
        from keyword_idea_generator.app import init_db
        init_db()
    
    yield app
    
    os.close(db_fd)
    os.unlink(db_path)

@pytest.fixture
def client(app):
    """Cliente de prueba"""
    return app.test_client()

def test_index_page(client):
    """Probar que la página principal carga correctamente"""
    response = client.get('/')
    assert response.status_code == 200
    assert b'Configurar An\xc3\xa1lisis' in response.data

def test_save_sitemap(client):
    """Probar guardar y recuperar sitemaps"""
    # Guardar sitemap
    response = client.post('/api/sitemaps', json={
        'url': 'https://test.com/sitemap.xml'
    })
    assert response.status_code == 200
    assert response.json['success'] is True
    
    # Obtener sitemaps
    response = client.get('/api/sitemaps')
    assert response.status_code == 200
    sitemaps = response.json
    assert len(sitemaps) == 1
    assert sitemaps[0]['url'] == 'https://test.com/sitemap.xml'
    
    # Eliminar sitemap
    response = client.delete('/api/sitemaps', json={
        'url': 'https://test.com/sitemap.xml'
    })
    assert response.status_code == 200
    assert response.json['success'] is True
    
    # Verificar que se eliminó
    response = client.get('/api/sitemaps')
    assert len(response.json) == 0

def test_process_keywords(client):
    """Probar procesamiento de keywords"""
    # Primero guardamos un sitemap
    client.post('/api/sitemaps', json={
        'url': 'https://test.com/sitemap.xml'
    })
    
    # Luego procesamos keywords
    response = client.post('/', data={
        'sitemap_url': 'https://test.com/sitemap.xml',
        'seed_keywords': 'test keyword 1\ntest keyword 2'
    }, follow_redirects=True)
    assert response.status_code == 200

def test_manage_keywords(client):
    """Probar guardar y eliminar keywords favoritas"""
    # Guardar keyword
    response = client.post('/api/keywords/manage', json={
        'keyword': 'test keyword',
        'action': 'save'
    })
    assert response.status_code == 200
    assert response.json['success'] is True
    
    # Eliminar keyword
    response = client.post('/api/keywords/manage', json={
        'keyword': 'test keyword',
        'action': 'unsave'
    })
    assert response.status_code == 200
    assert response.json['success'] is True

def test_index_post_no_data(client):
    """Test que el POST sin datos muestra error"""
    response = client.post('/', follow_redirects=True)
    assert response.status_code == 200
    assert b'Por favor ingresa una URL de sitemap y al menos una palabra clave' in response.data

def test_index_post_no_keywords(client):
    """Test que el POST sin keywords muestra error"""
    response = client.post('/', data={
        'sitemap_url': 'https://test.com/sitemap.xml',
        'seed_keywords': ''
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b'Por favor ingresa al menos una palabra clave v\xc3\xa1lida' in response.data

def test_export(client):
    """Test exportar keywords"""
    # Guardar algunas keywords
    client.post('/api/keywords/manage', json={
        'keyword': 'test keyword',
        'action': 'save'
    })
    
    # Exportar todas las keywords
    response = client.get('/export?type=all')
    assert response.status_code == 200
    assert 'text/csv; charset=utf-8' in response.headers['Content-Type']
    assert 'attachment;filename=keywords_all.csv' in response.headers['Content-Disposition']
    
    # Exportar solo keywords guardadas
    response = client.get('/export?type=saved')
    assert response.status_code == 200
    assert 'text/csv; charset=utf-8' in response.headers['Content-Type']
    assert 'attachment;filename=keywords_saved.csv' in response.headers['Content-Disposition']
