from flask import Flask, jsonify, request
import requests
import time
import os
app = Flask(__name__)


# Function to get place details using the Places Details API
def get_place_details(api_key, place_id):
    details_endpoint = "https://maps.googleapis.com/maps/api/place/details/json"
    details_params = {
        'place_id': place_id,
        'fields': 'name,formatted_address,website',  # Request only the fields we care about
        'key': api_key
    }

    details_response = requests.get(details_endpoint, params=details_params)

    if details_response.status_code == 200:
        return details_response.json().get('result', {})
    else:
        return {}


# Function to perform a text search using Google Places API and handle pagination
def get_restaurants(api_key, query):
    endpoint = "https://maps.googleapis.com/maps/api/place/textsearch/json"
    params = {
        'query': query,
        'key': api_key
    }

    restaurants = []
    while True:
        response = requests.get(endpoint, params=params)

        if response.status_code == 200:
            results = response.json().get('results', [])
            for place in results:
                name = place.get('name')
                address = place.get('formatted_address')
                place_id = place.get('place_id')

                place_details = get_place_details(api_key, place_id)
                website = place_details.get('website', 'N/A')

                restaurant_info = {
                    'name': name,
                    'address': address,
                    'website': website
                }
                restaurants.append(restaurant_info)

            next_page_token = response.json().get('next_page_token')
            if next_page_token:
                time.sleep(2)
                params['pagetoken'] = next_page_token
            else:
                break
        else:
            print(f"Error: Unable to fetch data. HTTP Status Code: {response.status_code}")
            break

    return restaurants


# Function to scrape emails from a given website using RapidAPI Email Scraper
def scrape_contact_info(website_url, rapidapi_key):
    url = "https://website-social-scraper-api.p.rapidapi.com/contacts"
    querystring = {"website": website_url}

    headers = {
        "x-rapidapi-key": rapidapi_key,
        "x-rapidapi-host": "website-social-scraper-api.p.rapidapi.com"
    }

    retries = 5
    while retries > 0:
        response = requests.get(url, headers=headers, params=querystring)

        if response.status_code == 200:
            return response.json()  # Return the JSON response on success
        elif response.status_code == 429:
            time.sleep(5)  # Wait before retrying
            retries -= 1
        else:
            print(f"Error: Unable to scrape contact info. HTTP Status Code: {response.status_code}")
            return None

    return None


# Define the API endpoint
@app.route('/api/emails', methods=['GET'])
def api_get_emails():
    google_api_key = request.args.get('google_api_key')  # Get Google API key from query parameters
    rapidapi_key = request.args.get('rapidapi_key')  # Get RapidAPI key from query parameters
    query = request.args.get('query')  # The search query

    if not google_api_key or not rapidapi_key or not query:
        return jsonify({"error": "API keys and query are required"}), 400

    # Get restaurants based on the query
    restaurants = get_restaurants(google_api_key, query)

    emails = []
    if restaurants:
        for restaurant in restaurants:
            if restaurant['website'] != 'N/A':
                contact_info = scrape_contact_info(restaurant['website'], rapidapi_key)
                if contact_info and 'emails' in contact_info:
                    emails.extend(contact_info['emails'])  # Collect all emails found
            else:
                print("No website available, skipping email scraping.")

        return jsonify(emails), 200  # Return only the list of emails
    else:
        return jsonify({"error": "No restaurants found"}), 404



@app.route('/api/upload_form', methods=['POST'])
def upload_form():
    if 'file' not in request.files and 'form_link' not in request.form:
        return jsonify({"error": "No form file or link provided"}), 400

    # If a file is uploaded
    if 'file' in request.files:
        form_file = request.files['file']

        # Check if the file has a valid filename
        if form_file.filename == '':
            return jsonify({"error": "No selected file"}), 400

        # Save the file to the FormFiles directory
        file_path = os.path.join(UPLOAD_FOLDER, form_file.filename)
        form_file.save(file_path)

        return jsonify({"message": "Form file uploaded successfully", "filename": form_file.filename}), 200

    # If a link to a form is provided
    if 'form_link' in request.form:
        form_link = request.form['form_link']
        # Validate the link (optional)
        return jsonify({"message": "Form link received", "link": form_link}), 200



# Run the app
if __name__ == "__main__":
    app.run(debug=True)
