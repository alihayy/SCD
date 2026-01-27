
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from flask import Flask
from routes.reports import reports_bp  # <-- use routes, not labmanagement.routes


@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(reports_bp)
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_health_check(client):
    response = client.get('/reports/health')
    json_data = response.get_json()
    assert response.status_code in [200, 503]
    assert "service" in json_data["data"]

def test_list_reports_invalid_patient(client):
    response = client.get('/reports/0/list')
    json_data = response.get_json()
    assert response.status_code == 400
    assert "Invalid patient ID" in json_data["message"]

def test_download_report_invalid_patient(client):
    response = client.get('/reports/0')
    json_data = response.get_json()
    assert response.status_code == 400
    assert "Invalid patient ID" in json_data["message"]

def test_upload_report_no_file(client):
    response = client.post('/reports', data={"patient_id": "1"})
    json_data = response.get_json()
    assert response.status_code == 400
    assert "No file part in request" in json_data["errors"][0]
