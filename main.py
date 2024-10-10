from flask import Flask, jsonify, request
import requests
import time
import os
import openai

app = Flask(__name__)

# Load OpenAI API Key from environment variables
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
openai.api_key = OPENAI_API_KEY

# System instructions for the OpenAI agent
SYSTEM_INSTRUCTIONS = """
You are an intelligent assistant that generates market validation questions based on a business idea description provided by the user. You will be provided with a description of a new business idea, and your task is to generate a series of survey questions that can help validate the business idea with potential customers. Here are the key guidelines:

1. **Understanding the Idea**: Read the business description carefully and identify its core elements: the product or service, the target audience, and the problem it solves.
2. **Focus on Validation**: Generate questions that help validate if potential customers are interested in this product/service, what features or aspects they value, how they are currently solving the problem, and their willingness to pay.
3. **Diversity of Questions**: Include a mix of question types: Short Text, Paragraph, Multiple Choice, Checkboxes, Linear Scale, Dropdown, and Date.
4. **Question Content**: Focus on areas like customer needs, experience, willingness to pay, product features, and competitors.
5. **Contextual Relevance**: Ensure that the questions are relevant to the specific business idea provided.
6. **Tone**: Keep the tone professional, clear, and user-friendly.
"""

# -------------------------- Utility Functions --------------------------

def get_place_details(api_key, place_id):
    """Fetch place details using Google Places API."""
    details_endpoint = "https://maps.googleapis.com/maps/api/place/details/json"
    details_params = {
        'place_id': place_id,
        'fields': 'name,formatted_address,website',  # Request only the fields we care about
        'key': api_key
    }

    details_response = requests.get(details_endpoint, params=details_params)

    return details_response.json().get('result', {}) if details_response.status_code == 200 else {}

def get_restaurants(api_key, query):
    """Retrieve restaurants based on a search query."""
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
                time.sleep(2)  # Wait for the next page to be available
                params['pagetoken'] = next_page_token
            else:
                break
        else:
            print(f"Error: Unable to fetch data. HTTP Status Code: {response.status_code}")
            break

    return restaurants

def scrape_contact_info(website_url, rapidapi_key):
    """Scrape emails from a given website using RapidAPI Email Scraper."""
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

def create_google_form(form_title, questions):
    """Create a Google Form by calling the Google Apps Script web app."""
    url = "https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec"  # Replace with your deployed script URL
    payload = {
        "formTitle": form_title,
        "questions": questions
    }

    response = requests.post(url, json=payload)

    return response.json() if response.status_code == 200 else None

def call_openai_agent(business_description):
    """Call the OpenAI API to generate survey questions based on a business description."""
    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",  # or "gpt-3.5-turbo" depending on your needs
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTIONS},
                {"role": "user", "content": business_description}
            ],
            max_tokens=500  # Adjust the max tokens if needed
        )
        return response['choices'][0]['message']['content']
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return None

# -------------------------- API Endpoints --------------------------

@app.route('/api/emails', methods=['GET'])
def api_get_emails():
    """Endpoint to get emails of restaurants based on a search query."""
    google_api_key = request.args.get('google_api_key')
    rapidapi_key = request.args.get('rapidapi_key')
    query = request.args.get('query')

    if not google_api_key or not rapidapi_key or not query:
        return jsonify({"error": "API keys and query are required"}), 400

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
    """Endpoint to upload a form file or link."""
    if 'file' not in request.files and 'form_link' not in request.form:
        return jsonify({"error": "No form file or link provided"}), 400

    if 'file' in request.files:
        form_file = request.files['file']
        if form_file.filename == '':
            return jsonify({"error": "No selected file"}), 400
        file_path = os.path.join("FormFiles", form_file.filename)
        form_file.save(file_path)
        return jsonify({"message": "Form file uploaded successfully", "filename": form_file.filename}), 200

    if 'form_link' in request.form:
        form_link = request.form['form_link']
        return jsonify({"message": "Form link received", "link": form_link}), 200

@app.route('/api/generate_questions', methods=['POST'])
def generate_questions():
    """Endpoint to generate questions based on a business description."""
    data = request.json
    business_description = data.get('business_description')

    if not business_description:
        return jsonify({"error": "Business description is required"}), 400

    questions = call_openai_agent(business_description)

    if questions:
        return jsonify({"questions": questions}), 200
    else:
        return jsonify({"error": "Failed to generate questions"}), 500

@app.route('/api/create_form', methods=['POST'])
def create_form():
    """Endpoint to create a Google Form."""
    data = request.json
    form_title = data.get('formTitle')
    questions = data.get('questions')

    if not form_title or not questions:
        return jsonify({"error": "formTitle and questions are required"}), 400

    form_url = create_google_form(form_title, questions)

    if form_url:
        return jsonify({"formUrl": form_url}), 200
    else:
        return jsonify({"error": "Failed to create form"}), 500

# -------------------------- Main Execution --------------------------

if __name__ == "__main__":
    app.run(debug=True)
