import pytest
from keyword_idea_generator.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_index_get(client):
    """Test que la página principal carga correctamente"""
    rv = client.get('/')
    assert rv.status_code == 200
    assert b'Generador de Ideas' in rv.data

def test_index_post_no_data(client):
    """Test que el POST sin datos retorna error 400"""
    rv = client.post('/')
    assert rv.status_code == 400

def test_index_post_invalid_url(client):
    """Test que el POST con URL inválida retorna error"""
    rv = client.post('/', data={
        'sitemap_url': 'http://invalid.url',
        'seed_keywords': 'test,keywords'
    })
    assert rv.status_code == 400

def test_index_post_no_keywords(client):
    """Test que el POST sin keywords retorna error"""
    rv = client.post('/', data={
        'sitemap_url': 'http://example.com/sitemap.xml'
    })
    assert rv.status_code == 400

def test_results_page(client):
    """Test the results page loads correctly"""
    rv = client.get('/results')
    assert rv.status_code == 200
    assert b'Resultados del' in rv.data

def test_save_keyword(client):
    """Test saving a keyword"""
    rv = client.post('/save_keyword', data={
        'keyword': 'test keyword',
        'type': 'autocomplete'
    })
    assert rv.status_code == 200
    json_data = rv.get_json()
    assert json_data['success'] == True

def test_export(client):
    """Test exporting keywords"""
    rv = client.post('/export', data={'type': 'all'})
    assert rv.status_code == 200
    assert b'Keyword,Tipo,Fecha' in rv.data
