import pytest
import requests
from unittest.mock import patch, MagicMock, call
import pandas as pd
from utils.utils import fetch_sheet_data, scrape_contact_info, get_businesses, get_place_details, scrape_contact_info_parallel
import requests
from unittest.mock import patch, Mock
from concurrent.futures import Future
import time

def test_fetch_sheet_data_success():
    mock_data = [{"column1": "value1", "column2": "value2"}]
    expected_df = pd.DataFrame(mock_data)
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_data
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        result_df = fetch_sheet_data("valid_spreadsheet_id")
        pd.testing.assert_frame_equal(result_df, expected_df)

def test_fetch_sheet_data_http_error():
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("HTTP Error")
        mock_post.return_value = mock_response
        result_df = fetch_sheet_data("valid_spreadsheet_id")
        assert result_df.equals(pd.DataFrame())

def test_fetch_sheet_data_invalid_json():
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        result_df = fetch_sheet_data("valid_spreadsheet_id")
        assert result_df.equals(pd.DataFrame())

def test_fetch_sheet_data_network_error():
    with patch('requests.post') as mock_post:
        mock_post.side_effect = requests.exceptions.ConnectionError("Network error")
        result_df = fetch_sheet_data("valid_spreadsheet_id")
        assert result_df.equals(pd.DataFrame())

def test_fetch_sheet_data_empty_spreadsheet_id():
    mock_data = [{"column1": "value1", "column2": "value2"}]
    expected_df = pd.DataFrame(mock_data)
    with patch('requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.json.return_value = mock_data
        mock_response.raise_for_status = MagicMock()
        mock_post.return_value = mock_response
        result_df = fetch_sheet_data("")
        pd.testing.assert_frame_equal(result_df, expected_df)


def test_scrape_contact_info_success():
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'email': 'example@example.com'}
        mock_get.return_value = mock_response

        result = scrape_contact_info('http://example.com')
        assert result == {'email': 'example@example.com'}

def test_scrape_contact_info_rate_limit_fallback():
    with patch('requests.get') as mock_get:
        mock_response_429 = Mock()
        mock_response_429.status_code = 429  # Simulate rate limit response

        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {'email': 'example@example.com'}

        # First call returns 429, second call returns 200
        mock_get.side_effect = [mock_response_429, mock_response_200]

        result = scrape_contact_info('http://example.com')

        print(f"Mock requests.get call count: {mock_get.call_count}")  # Debugging

        assert mock_get.call_count == 2  # Ensure function retried once
        assert result == {'email': 'example@example.com'}

def test_scrape_contact_info_failure():
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        result = scrape_contact_info('http://example.com')
        assert result is None

def test_scrape_contact_info_rate_limit_exceeded():
    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response
        result = scrape_contact_info('http://example.com')
        assert result is None


@patch('requests.get')
def test_get_place_details_success(mock_get):
    expected_result = {
        'name': 'Test Place',
        'formatted_address': '123 Test St, Test City, TC',
        'website': 'http://testplace.com'
    }
    response_data = {
        'result': expected_result
    }

    mock_response = Mock()
    mock_response.json.return_value = response_data
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    result = get_place_details("test_place_id")
    assert result == expected_result

@patch('requests.get')
def test_get_place_details_no_result(mock_get):
    mock_response = Mock()
    mock_response.json.return_value = {}
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    result = get_place_details("test_place_id_no_result")
    assert result == {}

@patch('requests.get')
def test_get_place_details_incorrect_status_code(mock_get):
    mock_response = Mock()
    mock_response.json.return_value = {
        'result': {
            'name': 'Test Place',
            'formatted_address': '123 Test St, Test City, TC',
            'website': 'http://testplace.com'
        }
    }
    mock_response.status_code = 404
    mock_get.return_value = mock_response

    result = get_place_details("test_place_id_error")
    assert result == {}

@patch('requests.get')
def test_get_place_details_missing_fields(mock_get):
    response_data = {
        'result': {
            'name': 'Incomplete Place'
            # Missing formatted_address and website
        }
    }

    mock_response = Mock()
    mock_response.json.return_value = response_data
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    result = get_place_details("test_place_id_incomplete")
    assert result == {'name': 'Incomplete Place'}

@patch('requests.get')
def test_get_place_details_empty_result(mock_get):
    mock_response = Mock()
    mock_response.json.return_value = {'result': {}}
    mock_response.status_code = 200
    mock_get.return_value = mock_response

    result = get_place_details("test_place_id_empty")
    assert result == {}

@patch('requests.get')
def test_get_place_details_api_key_error(mock_get):
    mock_response = Mock()
    mock_response.json.return_value = {'error_message': 'Invalid API key', 'status': 'REQUEST_DENIED'}
    mock_response.status_code = 403
    mock_get.return_value = mock_response

    result = get_place_details("test_place_id_invalid_key")
    assert result == {}


@pytest.fixture
def mock_api_response():
    return {
        'results': [
            {
                'name': 'Test Restaurant 1',
                'formatted_address': '123 Test St',
                'place_id': 'test_place_id_1',
            },
            {
                'name': 'Test Restaurant 2',
                'formatted_address': '456 Test Ave',
                'place_id': 'test_place_id_2',
            }
        ],
        'next_page_token': None
    }


@pytest.fixture
def mock_place_details():
    return {
        'result': {
            'website': 'http://test-restaurant.com',
            'name': 'Test Restaurant',
            'formatted_address': '123 Test St'
        }
    }


def test_get_businesses_successful_request(mock_api_response, mock_place_details):
    """Test successful API request with multiple results"""
    with patch('requests.get') as mock_get:
        # Create separate mock responses for each API call
        search_response = Mock()
        search_response.status_code = 200
        search_response.json.return_value = mock_api_response

        details_response = Mock()
        details_response.status_code = 200
        details_response.json.return_value = mock_place_details

        # Configure mock to return different responses based on the endpoint
        def get_side_effect(*args, **kwargs):
            if 'textsearch' in args[0]:
                return search_response
            else:
                return details_response

        mock_get.side_effect = get_side_effect

        result = get_businesses("test query")

        assert len(result) == 2
        assert result == ['http://test-restaurant.com', 'http://test-restaurant.com']
        assert mock_get.call_count == 3  # One for search, two for place details


def test_get_businesses_with_pagination(mock_api_response, mock_place_details):
    """Test pagination handling"""
    with patch('requests.get') as mock_get, \
            patch('time.sleep') as mock_sleep:  # Mock sleep to speed up tests

        # First page response
        first_page = dict(mock_api_response)
        first_page['next_page_token'] = 'test_token'

        # Second page response
        second_page = dict(mock_api_response)
        second_page['next_page_token'] = None

        # Create mock responses
        first_search_response = Mock()
        first_search_response.status_code = 200
        first_search_response.json.return_value = first_page

        second_search_response = Mock()
        second_search_response.status_code = 200
        second_search_response.json.return_value = second_page

        details_response = Mock()
        details_response.status_code = 200
        details_response.json.return_value = mock_place_details

        search_responses = [first_search_response, second_search_response]
        search_response_index = 0

        def get_side_effect(*args, **kwargs):
            nonlocal search_response_index
            if 'textsearch' in args[0]:
                response = search_responses[search_response_index]
                search_response_index = min(search_response_index + 1, len(search_responses) - 1)
                return response
            else:
                return details_response

        mock_get.side_effect = get_side_effect

        result = get_businesses("test query")

        assert len(result) == 4  # Two results from each page
        assert mock_sleep.called
        assert mock_get.call_count == 6  # Two pages plus four place details


def test_get_businesses_missing_website(mock_api_response):
    """Test handling of missing website in place details"""
    with patch('requests.get') as mock_get:
        # Create search response
        search_response = Mock()
        search_response.status_code = 200
        search_response.json.return_value = mock_api_response

        # Create details response without website
        details_response = Mock()
        details_response.status_code = 200
        details_response.json.return_value = {
            'result': {
                'name': 'Test Restaurant',
                'formatted_address': '123 Test St'
            }
        }

        def get_side_effect(*args, **kwargs):
            if 'textsearch' in args[0]:
                return search_response
            else:
                return details_response

        mock_get.side_effect = get_side_effect

        result = get_businesses("test query")

        assert len(result) == 2
        assert result == ['N/A', 'N/A']
        assert mock_get.call_count == 3


def test_get_businesses_api_error():
    """Test handling of API error response"""
    with patch('requests.get') as mock_get:
        error_response = Mock()
        error_response.status_code = 400
        mock_get.return_value = error_response

        result = get_businesses("test query")

        assert result == []
        assert mock_get.call_count == 1


def test_get_businesses_empty_results():
    """Test handling of empty results from API"""
    with patch('requests.get') as mock_get:
        empty_response = Mock()
        empty_response.status_code = 200
        empty_response.json.return_value = {'results': [], 'next_page_token': None}
        mock_get.return_value = empty_response

        result = get_businesses("test query")

        assert result == []
        assert mock_get.call_count == 1


@pytest.fixture
def mock_successful_response():
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        'result': {
            'emails': ['contact@example.com'],
            'phones': ['+1234567890'],
            'social_links': ['https://linkedin.com/company/example']
        }
    }
    return mock_response


def test_parallel_scraping_successful():
    """Test successful parallel scraping of multiple websites"""
    websites = ['http://example1.com', 'http://example2.com']

    with patch('requests.get') as mock_get:
        # Set up mock responses
        response1 = Mock()
        response1.status_code = 200
        response1.json.return_value = {'result': {'emails': ['contact@example1.com']}}

        response2 = Mock()
        response2.status_code = 200
        response2.json.return_value = {'result': {'emails': ['contact@example2.com']}}

        mock_get.side_effect = [response1, response2]

        results = scrape_contact_info_parallel(websites)

        assert len(results) == 2
        assert mock_get.call_count == 2
        assert results['http://example1.com']['result']['emails'] == ['contact@example1.com']
        assert results['http://example2.com']['result']['emails'] == ['contact@example2.com']


def test_parallel_scraping_with_errors():
    """Test parallel scraping handling of failed requests"""
    websites = ['http://example1.com', 'http://error.com']

    with patch('requests.get') as mock_get:
        # Set up responses
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {'result': {'emails': ['contact@example1.com']}}

        error_response = Mock()
        error_response.status_code = 403

        mock_get.side_effect = [success_response, error_response]

        results = scrape_contact_info_parallel(websites)

        assert len(results) == 2
        assert results['http://example1.com']['result']['emails'] == ['contact@example1.com']
        assert results['http://error.com'] is None


def test_parallel_scraping_empty_list():
    """Test parallel scraping with empty website list"""
    websites = []
    results = scrape_contact_info_parallel(websites)
    assert results == {}


def test_parallel_scraping_max_workers():
    """Test parallel scraping respects max_workers limit"""
    websites = ['site1.com', 'site2.com', 'site3.com']

    # Create a mock executor and its context manager instance.
    mock_executor = Mock()
    mock_instance = Mock()
    mock_executor.return_value = mock_instance
    # Simulate context manager behavior.
    mock_instance.__enter__ = Mock(return_value=mock_instance)
    mock_instance.__exit__ = Mock(return_value=None)

    with patch('utils.utils.ThreadPoolExecutor', mock_executor), \
            patch('requests.get') as mock_get:
        # Set up a mock response for requests.get.
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'result': {'emails': ['test@example.com']}}
        mock_get.return_value = mock_response

        # Set up the submit method on the executor to return a completed future.
        def submit_side_effect(*args, **kwargs):
            future = Future()
            future.set_result(mock_response.json.return_value)
            return future

        mock_instance.submit.side_effect = submit_side_effect

        results = scrape_contact_info_parallel(websites)

        # Verify the executor was created with max_workers=10.
        mock_executor.assert_called_once_with(max_workers=10)
        assert len(results) == 3

        # Verify the executor was used for each website.
        assert mock_instance.submit.call_count == len(websites)


def test_parallel_scraping_mixed_results():
    """Test parallel scraping with mix of successful, failed, and None results"""
    websites = ['success.com', 'error.com', 'timeout.com']

    with patch('requests.get') as mock_get:
        # Set up different responses
        success_response = Mock()
        success_response.status_code = 200
        success_response.json.return_value = {'result': {'emails': ['contact@success.com']}}

        error_response = Mock()
        error_response.status_code = 403

        timeout_response = Mock()
        timeout_response.status_code = 408

        mock_get.side_effect = [success_response, error_response, timeout_response]

        results = scrape_contact_info_parallel(websites)

        assert len(results) == 3
        assert results['success.com']['result']['emails'] == ['contact@success.com']
        assert results['error.com'] is None
        assert results['timeout.com'] is None


def test_parallel_scraping_empty_response():
    """Test parallel scraping with empty response"""
    websites = ['empty.com']

    with patch('requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'result': {'emails': []}}
        mock_get.return_value = mock_response

        results = scrape_contact_info_parallel(websites)

        assert len(results) == 1
        assert results['empty.com']['result']['emails'] == []