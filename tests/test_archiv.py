import os
import json
from pathlib import Path
import pytest
from app import app


@pytest.fixture
def client(tmp_path):
    app.config['TESTING'] = True
    app.config['ARCHIV_DIR'] = str(tmp_path / "archiv")
    app.config['CHECKLIST_DIR'] = str(tmp_path / "checklists")

    Path(app.config['ARCHIV_DIR']).mkdir()
    Path(app.config['CHECKLIST_DIR']).mkdir()

    with app.test_client() as client:
        yield client

def test_get_archiv(client):
    test_file = Path(app.config['ARCHIV_DIR']) / "test.json"
    test_file.write_text(json.dumps({"hello": "world"}))

    response = client.get('/archiv')
    assert response.status_code == 200
    assert b"test" in response.data  # falls dein Template das ausgibt

def test_post_restore(client):
    test_file = Path(app.config['ARCHIV_DIR']) / "restoreme.json"
    test_file.write_text(json.dumps({"restore": True}))

    response = client.post('/archiv', data={'restore': 'restoreme'}, follow_redirects=True)

    restored_file = Path(app.config['CHECKLIST_DIR']) / "restoreme.json"
    assert restored_file.exists()
    assert not Path(app.config['ARCHIV_DIR']).joinpath("restoreme.json").exists()
    assert response.status_code == 200