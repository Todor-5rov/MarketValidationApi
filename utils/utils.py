import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from Config.config import Config


def scrape_contact_info_parallel(websites):
        """Scrape emails concurrently from a list of websites."""
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_website = {executor.submit(scrape_contact_info, website): website for website in websites}
            results = {}
            for future in as_completed(future_to_website):
                website = future_to_website[future]
                try:
                    results[website] = future.result()
                except Exception as e:
                    print(f"Error scraping {website}: {e}")
                    results[website] = None
            return results

def get_place_details(place_id):
        """Fetch place details using Google Places API."""
        details_endpoint = "https://maps.googleapis.com/maps/api/place/details/json"
        details_params = {
            'place_id': place_id,
            'fields': 'name,formatted_address,website',  # Request only the fields we care about
            'key': Config.GOOGLE_API_KEY
        }

        details_response = requests.get(details_endpoint, params=details_params)

        return details_response.json().get('result', {}) if details_response.status_code == 200 else {}

def get_businesses(query):
        """Retrieve restaurants based on a search query."""
        endpoint = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            'query': query,
            'key': Config.GOOGLE_API_KEY,
            'radius': 5000
        }

        busineses = []
        while True:
            response = requests.get(endpoint, params=params)
            if response.status_code == 200:
                results = response.json().get('results', [])
                for place in results:
                    name = place.get('name')
                    address = place.get('formatted_address')
                    place_id = place.get('place_id')

                    place_details = get_place_details(place_id)
                    website = place_details.get('website', 'N/A')

                    restaurant_info = {
                        'name': name,
                        'address': address,
                        'website': website
                    }
                    busineses.append(restaurant_info['website'])
                next_page_token = response.json().get('next_page_token')
                if next_page_token:
                    time.sleep(2)  # Wait for the next page to be available
                    params['pagetoken'] = next_page_token
                else:
                    break
            else:
                print(f"Error: Unable to fetch data. HTTP Status Code: {response.status_code}")
                break

        return busineses

def scrape_contact_info(website_url):
        """Scrape emails from a given website using RapidAPI Email Scraper."""
        url = "https://website-social-scraper-api.p.rapidapi.com/contacts"
        querystring = {"website": website_url}
        headers = {
            "x-rapidapi-key": Config.RAPID_API_KEY,
            "x-rapidapi-host": "website-social-scraper-api.p.rapidapi.com"
        }

        retries = 2
        while retries > 0:
            response = requests.get(url, headers=headers, params=querystring)

            if response.status_code == 200:
                return response.json()  # Return the JSON response on success
            elif response.status_code == 429:
                retries -= 1
                time.sleep(0.5)
            else:
                print(f"Error: Unable to scrape contact info. HTTP Status Code: {response.status_code}")
                return None

        return None

def fetch_sheet_data(spreadsheet_id):
        """
        Fetch data from the Google Apps Script endpoint and convert it to a Pandas DataFrame.

        Args:
            spreadsheet_id (str): The ID of the Google Spreadsheet.

        Returns:
            pd.DataFrame: The data converted into a Pandas DataFrame.
        """
        # URL of the Google Apps Script endpoint
        endpoint = "https://script.google.com/macros/s/AKfycbx5kuuR9WqK9ZxFNrWuy2lvEwpeG1CimGBfwcVtpEReBoSnNc1gCO6XiQcVsm598U8C/exec"

        try:
            # Make the GET request
            response = requests.post(url=endpoint, json={'id': spreadsheet_id})

            # Raise an exception if the request failed
            response.raise_for_status()

            # Parse the JSON response
            data = response.json()
            # Convert JSON data to a Pandas DataFrame
            df = pd.DataFrame(data)
            return df
        except requests.exceptions.RequestException as e:
            print(f"HTTP Request failed: {e}")
            return pd.DataFrame()  # Return an empty DataFrame on error
        except ValueError as e:
            print(f"Error parsing JSON: {e}")
            return pd.DataFrame()