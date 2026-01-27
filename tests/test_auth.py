
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import pytest
from flask import Flask, request, jsonify
from werkzeug.security import generate_password_hash

# Sample Flask app simulating auth routes
@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True

    # Mock register route
    @app.route('/register', methods=['POST'])
    def register():
        data = request.json
        if not data.get('username') or not data.get('password'):
            return jsonify({"success": False, "errors": ["Missing username or password"]}), 400
        hashed = generate_password_hash(data['password'])
        return jsonify({"success": True, "username": data['username'], "hashed_password": hashed}), 201

    # Mock login route
    @app.route('/login', methods=['POST'])
    def login():
        data = request.json
        if data.get('username') == 'testuser' and data.get('password') == 'testpass':
            return jsonify({"success": True, "message": "Login successful"}), 200
        return jsonify({"success": False, "errors": ["Invalid credentials"]}), 401

    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_register_success(client):
    response = client.post('/register', json={"username": "testuser", "password": "123456"})
    json_data = response.get_json()
    assert response.status_code == 201
    assert json_data["success"] is True
    assert "hashed_password" in json_data

def test_register_missing_fields(client):
    response = client.post('/register', json={"username": ""})
    json_data = response.get_json()
    assert response.status_code == 400
    assert json_data["success"] is False

def test_login_success(client):
    response = client.post('/login', json={"username": "testuser", "password": "testpass"})
    json_data = response.get_json()
    assert response.status_code == 200
    assert json_data["success"] is True

def test_login_failure(client):
    response = client.post('/login', json={"username": "wrong", "password": "wrong"})
    json_data = response.get_json()
    assert response.status_code == 401
    assert json_data["success"] is False
