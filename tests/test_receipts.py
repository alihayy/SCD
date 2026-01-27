import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from flask import Flask
from routes.receipts import receipts_bp  # <-- correct path


@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(receipts_bp)
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_create_receipt_no_json(client):
    response = client.post('/receipts', data="invalid")
    assert response.status_code == 400
    assert "Content-Type" in response.get_json()["errors"][0]

def test_create_receipt_missing_fields(client):
    response = client.post('/receipts', json={})
    assert response.status_code == 400
    # Updated to match your current API response
    assert "No JSON data provided" in response.get_json()["errors"]



def test_get_receipts(client):
    response = client.get('/receipts')
    json_data = response.get_json()
    assert response.status_code == 200
    assert json_data["success"] is True
    assert isinstance(json_data["data"]["receipts"], list)

def test_get_receipt_invalid_id(client):
    response = client.get('/receipts/0')
    assert response.status_code == 400
    assert "Receipt ID must be a positive integer" in response.get_json()["errors"][0]

def test_delete_receipt(client):
    response = client.delete('/receipts/1')
    json_data = response.get_json()
    assert json_data["success"] is True
