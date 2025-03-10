import smtplib
import pytest
from unittest.mock import patch, MagicMock
from flask import Flask, request
from api_functions.api_functions import ApiFunctions
import pandas as pd
import json
import os


@pytest.fixture
def test_app():
    """Creates a test Flask app for testing."""
    app = Flask(__name__)
    app.testing = True
    return app


@pytest.fixture
def client(test_app):
    """Creates a test client."""
    return test_app.test_client()


@patch("api_functions.api_functions.requests.post")
def test_create_google_form_success(mock_requests_post, test_app):
    """Tests the successful creation of a Google Form."""

    with test_app.test_request_context(json={
        "form_title": "Survey Form",
        "questions": ["What is your name?", "How old are you?"]
    }):
        # Mock the response from requests.post
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "formUrl": "https://forms.google.com/survey",
            "spreadsheetUrl": "https://sheets.google.com/survey_data"
        }
        mock_requests_post.return_value = mock_response

        # Call the function
        response, status_code = ApiFunctions.create_google_form()

        # Assertions
        assert status_code == 200
        assert response["formUrl"] == "https://forms.google.com/survey"
        assert response["spreadsheetUrl"] == "https://sheets.google.com/survey_data"


@patch("api_functions.api_functions.requests.post")
def test_create_google_form_failure(mock_requests_post, test_app):
    """Tests failure case when Google Form creation fails."""

    with test_app.test_request_context(json={
        "form_title": "Survey Form",
        "questions": ["What is your name?", "How old are you?"]
    }):
        # Mock the response from requests.post to simulate an error
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_requests_post.return_value = mock_response

        # Call the function
        response, status_code = ApiFunctions.create_google_form()

        # Assertions
        assert status_code == 500
        assert response["error"] == "Failed to create Google Form"


@patch("api_functions.api_functions.requests.post")
def test_create_google_form_invalid_json(mock_requests_post, test_app):
    """Tests case where API response is not valid JSON."""

    with test_app.test_request_context(json={
        "form_title": "Survey Form",
        "questions": ["What is your name?", "How old are you?"]
    }):
        # Mock the response from requests.post to return an invalid JSON response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_requests_post.return_value = mock_response

        # Call the function
        response, status_code = ApiFunctions.create_google_form()

        # Assertions
        assert status_code == 500
        assert response["error"] == "Invalid JSON response from Google Apps Script"


@pytest.fixture
def test_app():
    """Creates a Flask app for testing."""
    app = Flask(__name__)
    app.testing = True
    return app


@pytest.fixture
def client(test_app):
    """Creates a test client for Flask app."""
    return test_app.test_client()


def test_call_openai_agent_success(test_app):
    """Tests successful response from OpenAI API."""

    with test_app.test_request_context(json={"business_description": "We sell eco-friendly products."}):
        mock_client = MagicMock()
        mock_chat_response = MagicMock()
        mock_chat_response.choices = [MagicMock(message=MagicMock(content="This is a test response."))]
        mock_client.chat.completions.create.return_value = mock_chat_response

        response = ApiFunctions.call_openai_agent(mock_client)

        assert response == "This is a test response."


def test_call_openai_agent_failure(test_app):
    """Tests handling of API failure."""

    with test_app.test_request_context(json={"business_description": "We sell eco-friendly products."}):
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        response = ApiFunctions.call_openai_agent(mock_client)

        assert response is None


def test_call_openai_agent_empty_description(test_app):
    """Tests behavior when business_description is empty."""

    with test_app.test_request_context(json={"business_description": ""}):
        mock_client = MagicMock()
        mock_chat_response = MagicMock()
        mock_chat_response.choices = [MagicMock(message=MagicMock(content="Empty input response."))]
        mock_client.chat.completions.create.return_value = mock_chat_response

        response = ApiFunctions.call_openai_agent(mock_client)

        assert response == None


def test_call_openai_agent_missing_description(test_app):
    """Tests behavior when business_description key is missing."""

    with test_app.test_request_context(json={}):
        mock_client = MagicMock()

        # Ensure OpenAI is NEVER called when `business_description` is missing
        response = ApiFunctions.call_openai_agent(mock_client)

        assert response is None  # This is the expected output when description is missing
        mock_client.chat.completions.create.assert_not_called()  # Ensure OpenAI was NOT called


def test_call_openai_agent_unexpected_api_response(test_app):
    """Tests behavior when OpenAI API returns an unexpected response structure."""

    with test_app.test_request_context(json={"business_description": "AI automation company."}):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(choices=[])

        response = ApiFunctions.call_openai_agent(mock_client)

        assert response is None  # Should return None if choices list is empty


def test_call_openai_agent_partial_response(test_app):
    """Tests when OpenAI API returns a response missing 'message.content'."""

    with test_app.test_request_context(json={"business_description": "Tech startup"}):
        mock_client = MagicMock()
        mock_chat_response = MagicMock()
        mock_chat_response.choices = [MagicMock(message=MagicMock(content=None))]  # No content
        mock_client.chat.completions.create.return_value = mock_chat_response

        response = ApiFunctions.call_openai_agent(mock_client)

        assert response is None  # Should return None if content is missing


@pytest.fixture
def test_app():
    """Create a Flask test app."""
    app = Flask(__name__)
    app.config["TESTING"] = True
    return app


def test_analyze_feedback_success(test_app):
    """Test successful analysis of survey data."""
    with test_app.test_request_context(json={"spreadsheetId": "test_spreadsheet"}):
        mock_client = MagicMock()

        # Create a mock Pandas DataFrame as fake survey data
        fake_data = pd.DataFrame({"Question": ["Q1", "Q2"], "Response": ["Yes", "No"]})

        with patch("api_functions.api_functions.fetch_sheet_data", return_value=fake_data):
            # Mock OpenAI API response
            mock_client.chat.completions.create.return_value.choices = [
                MagicMock(message=MagicMock(content="Analysis result"))
            ]

            response = ApiFunctions.analyze_feedback(mock_client)

            # Decode the response content (which is a Flask Response object)
            data = json.loads(response[0].data.decode("utf-8"))

            # Check that response status code is 200
            assert response[1] == 200

            # Check that the insights are present in the response
            assert "insights" in data
            assert data["insights"] == "Analysis result"


def test_analyze_feedback_no_data(test_app):
    """Test API when survey data is missing (empty DataFrame)."""
    with test_app.test_request_context(json={"spreadsheetId": "test_spreadsheet"}):
        mock_client = MagicMock()

        # Return an empty DataFrame
        empty_df = pd.DataFrame()

        with patch("api_functions.api_functions.fetch_sheet_data", return_value=empty_df):
            response = ApiFunctions.analyze_feedback(mock_client)

            # Decode the response content (which is a Flask Response object)
            data = json.loads(response[0].data.decode("utf-8"))

            # Check that the status code is 400
            assert response[1] == 400  # Expecting 400, not 500

            # Check that the error message is correct
            assert "error" in data
            assert data["error"] == "No survey data provided"


def test_analyze_feedback_openai_error(test_app):
    """Test API when OpenAI API fails."""
    with test_app.test_request_context(json={"spreadsheetId": "test_spreadsheet"}):
        mock_client = MagicMock()

        fake_data = pd.DataFrame({"Question": ["Q1", "Q2"], "Response": ["Yes", "No"]})

        with patch("api_functions.api_functions.fetch_sheet_data", return_value=fake_data):
            # Simulate OpenAI API failure
            mock_client.chat.completions.create.side_effect = Exception("OpenAI API error")

            response = ApiFunctions.analyze_feedback(mock_client)

            # Decode the response content (which is a Flask Response object)
            data = json.loads(response[0].data.decode("utf-8"))

            # Check that the status code is 500
            assert response[1] == 500

            # Check that the error message is correct
            assert "error" in data
            assert data["error"] == "Failed to analyze survey data"

