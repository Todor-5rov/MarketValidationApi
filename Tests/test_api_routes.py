import pytest
from unittest.mock import MagicMock
from flask import json
from api_routes import api_bp
from api_functions.api_functions import ApiFunctions
from Config import config
from flask import Flask


# Create a mock app and register the blueprint
@pytest.fixture
def app():
    app = Flask(__name__)
    app.register_blueprint(api_bp)
    return app


# Use the `client` fixture to send requests to the app
@pytest.fixture
def client(app):
    return app.test_client()


# Test the create_form route
def test_create_form(client, mocker):
    mocker.patch.object(ApiFunctions, 'create_google_form', return_value={"status": "success"})

    response = client.post('/api/create_form')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'


# Test the call_agent route
def test_call_agent(client, mocker):
    mocker.patch.object(ApiFunctions, 'call_openai_agent', return_value={"status": "success"})

    response = client.post('/api/call_agent')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'


# Test the analyze_feedback route
def test_analyze_feedback(client, mocker):
    mocker.patch.object(ApiFunctions, 'analyze_feedback', return_value={"status": "success"})

    response = client.post('/api/analyze_feedback')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'


# Test the send_email route
def test_send_email(client, mocker):
    mocker.patch.object(ApiFunctions, 'send_email', return_value={"status": "success"})

    response = client.post('/api/send_email')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'


# Test the feedback route
def test_feedback(client, mocker):
    mocker.patch.object(ApiFunctions, 'feedback', return_value={"status": "success"})

    response = client.post('/api/feedback')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'


# Test the webhook route
def test_webhook(client, mocker):
    mocker.patch.object(ApiFunctions, 'stripe_webhook', return_value={"status": "success"})

    response = client.post('/api/webhook')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'


# Test the translate_to_bg route
def test_translate_to_bg(client, mocker):
    mocker.patch.object(ApiFunctions, 'translate_to_bulgarian', return_value={"status": "success"})

    response = client.post('/api/translate_to_bg', json={"text": "Hello"})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'


# Test the translate_to_en route
def test_translate_to_en(client, mocker):
    mocker.patch.object(ApiFunctions, 'translate_to_english', return_value={"status": "success"})

    response = client.post('/api/translate_to_en', json={"text": "Здравей"})
    assert response.status_code == 200
    data = json.loads(response.data)
    assert data['status'] == 'success'
