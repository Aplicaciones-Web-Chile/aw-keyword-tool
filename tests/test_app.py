import pytest
from keyword_idea_generator.app import app
import os
import tempfile

@pytest.fixture
def client():
    db_fd, app.config['DATABASE_PATH'] = tempfile.mkstemp()
    app.config['TESTING'] = True

    with app.test_client() as client:
        yield client

    os.close(db_fd)
    os.unlink(app.config['DATABASE_PATH'])

def test_index(client):
    """Test the index page loads correctly"""
    rv = client.get('/')
    assert rv.status_code == 200
    assert b'Generador de Ideas' in rv.data

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
