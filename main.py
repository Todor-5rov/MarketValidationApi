import requests
import json

# Define the local server URL
BASE_URL = "http://127.0.0.1:5000"


# Step 1: Generate questions based on a business description
def generate_questions():
    business_description = """
    A cloud-based project management tool designed for small to medium-sized businesses (SMBs) 
    to help them streamline their workflows, collaborate more effectively, and integrate with 
    popular business tools like Slack, Google Workspace, and Trello. The goal is to increase 
    productivity and reduce the complexity of managing projects across different departments or teams.
    """

    url = f"{BASE_URL}/api/generate_questions"
    headers = {'Content-Type': 'application/json'}

    data = {
        "business_description": business_description
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        print("Questions generated successfully.")
        return response.json()['questions']
    else:
        print(f"Error generating questions: {response.json()}")
        return None


# Step 2: Create a Google Form with the generated questions
def create_form(questions):
    url = f"{BASE_URL}/api/create_form"
    headers = {'Content-Type': 'application/json'}

    data = {
        "formTitle": "SMB Project Management Tool Survey",
        "questions": questions
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        print("Form created successfully.")
        return response.json()['formUrl']
    else:
        print(f"Error creating form: {response.json()}")
        return None


# Step 3: Send an email with the form link
def send_email(form_url):
    url = f"{BASE_URL}/api/send_email"
    headers = {'Content-Type': 'application/json'}

    data = {
        "recipient": "tochkatapetrov@gmail.com",  # Test recipient
        "form_url": form_url
    }

    response = requests.post(url, headers=headers, json=data)

    if response.status_code == 200:
        print("Email sent successfully.")
    else:
        print(f"Error sending email: {response.json()}")


# Main function to run the full test
if __name__ == "__main__":
    # Generate questions
    questions = generate_questions()

    if questions:
        # Create a form
        form_url = create_form(questions)

        if form_url:
            # Send an email with the form link
            send_email(form_url)
