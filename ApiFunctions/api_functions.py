from flask import jsonify, request
import requests
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import stripe
import Config.config
from ModelInstructions.model_instructions import Instructions
from Utils.utils import scrape_contact_info_parallel, get_businesses, fetch_sheet_data

stripe.api_key = Config.config.Config.STRIPE_SECRET_KEY

class ApiFunctions:
    @staticmethod
    def get_business_emails():
        # return list("tochkatapetrov@gmail.com")
        data = request.json
        query = data.get("googlePlacesQuery")

        # Step 1: Get the websites to scrape
        websites = get_businesses(query)

        # Step 2: Scrape contact info in parallel
        response = scrape_contact_info_parallel(websites)

        # Step 3: Collect emails
        emails = []
        for website in response:
            if response.get(website) is not None:
                # Assuming the API response contains an "emails" field with a list of emails
                email_list = response.get(website).get("emails", [])
                if email_list:  # Check if there's at least one email in the list
                    emails.append(email_list[0])  # Add the first email from the list
        return list(set(emails)), 200

    @staticmethod
    def create_google_form():
        """Create a Google Form by calling the Google Apps Script web app."""
        data = request.json
        form_title = data.get("form_title")
        questions = data.get("questions")

        url = "https://script.google.com/macros/s/AKfycbzIQ2UFxgqcNasLr24x4CKDtIwtqEMJ-0O5mUrBqRGeZ59CR-_UrQekZCwSePa0VvGb/exec"
        payload = {
            "formTitle": form_title,
            "questions": questions
        }

        # Make the request to the Google Apps Script
        response = requests.post(url, json=payload)

        # Handle response
        if response.status_code == 200:
            try:
                # Extract the formUrl and spreadsheetUrl from the response
                form_data = response.json()  # Get the JSON response

                form_url = form_data.get("formUrl")  # Extract the formUrl
                spreadsheet_url = form_data.get("spreadsheetUrl")  # Extract the spreadsheetUrl

                # Return both URLs in the response
                return {
                           "formUrl": form_url,
                           "spreadsheetUrl": spreadsheet_url
                       }, 200
            except ValueError:
                return {"error": "Invalid JSON response from Google Apps Script"}, 500
        else:
            return {"error": "Failed to create Google Form"}, response.status_code

    @staticmethod
    def call_openai_agent(client):
        data = request.json
        description = data.get("business_description")

        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": Instructions.SYSTEM_INSTRUCTIONS_FORM},
                    {"role": "user", "content": description}
                ],
                max_tokens=1000
            )

            return response.choices[0].message.content

        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return None

    @staticmethod
    def analyze_feedback(client):
        """
        Analyze product validation survey data and return actionable insights.
        """
        data = request.json
        spreadsheetId = data.get("spreadsheetId")
        survey_data = fetch_sheet_data(spreadsheetId).to_string()

        if not survey_data:
            return jsonify({"error": "No survey data provided"}), 400

        try:
            # Call the OpenAI API to analyze the survey data
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": Instructions.SYSTEM_INSTRUCTIONS_ANALYSIS},
                    {"role": "user", "content": f"Here is the survey data:\n\n{survey_data}"}
                ],
                max_tokens=1000
            )

            # Extract and return the content of the response
            insights = response.choices[0].message.content
            return jsonify({"insights": insights})

        except Exception as e:
            print(f"Error calling OpenAI API: {e}")
            return jsonify({"error": "Failed to analyze survey data"}), 500

    @staticmethod
    def send_email():
        data = request.json
        recipients = data.get("recipients")  # Expecting a list of email addresses
        form_url = data.get("formUrl")
        recipients = "tochkatapetrov@gmail.com"
        # Mailgun configuration
        mailgun_domain = os.getenv('MAILGUN_DOMAIN')
        mailgun_pwd = os.getenv('MAILGUN_PASSWORD')
        sender_email = f'info@{mailgun_domain}'  # Use the Mailgun postmaster email
        # sender_password = os.getenv("MAILGUN_API_KEY")  # Your Mailgun API key or SMTP password

        # Create the message object
        message = MIMEMultipart("alternative")
        message["Subject"] = "Your Feedback is Highly Appreciated - Take our Quick Survey!"
        message["From"] = sender_email

        # Email body content
        html_content = f"""
        <html>
        <head>
        <style>
            .btn {{
                background-color: #4CAF50;
                color: white;
                padding: 10px 20px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 16px;
                margin: 4px 2px;
                cursor: pointer;
                border-radius: 5px;
            }}
            .btn:hover {{
                background-color: #45a049;
                text-decoration: none;
                color: white;
            }}
            .container {{
                padding: 20px;
                font-family: Arial, sans-serif;
            }}
        </style>
        </head>
        <body>
            <div class="container">
                <h2>Hello!</h2>
                <p>We are conducting a brief survey as part of our research for an exciting new product.</p>
                <p>Your valuable feedback will help us shape this innovation. We would love to hear from you!</p>
                <a href="{form_url}" class="btn">Take the Survey</a>
                <p>Thank you for your time and input!</p>
                <br>
                Best regards,
                <br><br>
            </div>
        </body>
        </html>
        """

        # Attach the HTML content
        part = MIMEText(html_content, "html")
        message.attach(part)

        # Check if recipients is a list, otherwise convert it to a list
        if isinstance(recipients, str):
            recipients = [recipients]  # Convert a single email to a list

        # Prepare to send emails
        success_count = 0
        failure_count = 0

        try:
            # Create an SMTP session using Mailgun's SMTP server
            server = smtplib.SMTP('smtp.eu.mailgun.org', 587)  # Use port 587 for TLS
            server.starttls()  # Upgrade to secure connection
            server.login(sender_email, mailgun_pwd)

            # Send the email to each recipient
            for recipient in recipients:
                message["To"] = recipient  # Update the To field for each recipient
                server.sendmail(sender_email, recipient, message.as_string())
                success_count += 1

            server.quit()

            return {"status": "Email sent successfully", "success_count": success_count}

        except Exception as e:
            failure_count += 1
            print(f"Failed to send email: {e}")
            return {"status": "Error", "message": str(e), "failure_count": failure_count}

    @staticmethod
    def feedback():
        data = request.json
        name = data.get('name')
        email = "info@pro-val.net"
        message = data.get('message')

        # Email content
        subject = "New Contact Form Submission"
        body = f"Name: {name}\nEmail: {email}\nMessage: {message}"
        mailgun_domain = os.getenv('MAILGUN_DOMAIN')
        mailgun_pwd = os.getenv('MAILGUN_PASSWORD')
        sender_email = f'info@{mailgun_domain}'
        # Set up the MIME
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = "info@pro-val.net"  # Replace with your receiving email
        msg['Subject'] = subject

        # Attach the body with the msg instance
        msg.attach(MIMEText(body, 'plain'))

        try:
            # Establish SMTP connection
            with smtplib.SMTP('smtp.eu.mailgun.org', 587) as server:
                server.starttls()  # Upgrade to secure connection
                server.login(sender_email, mailgun_pwd)
                server.sendmail(sender_email, "info@pro-val.net", msg.as_string())

            return jsonify({"message": "Email sent successfully"}), 200
        except Exception as e:
            return jsonify({"message": "Failed to send email", "error": str(e)}), 500

    @staticmethod
    def stripe_webhook(db):
        payload = request.get_json()
        event_type = payload["type"]

        if event_type == "checkout.session.completed":
            session = payload["data"]["object"]
            user_id = session["client_reference_id"]  # Assumes this was set as the Firebase user ID

            if session["mode"] == "subscription":
                subscription_id = session["subscription"]
                subscription = stripe.Subscription.retrieve(subscription_id)

                # Update Firestore with subscription details
                user_ref = db.collection("subscriptions").document(user_id)
                user_ref.set({
                    "subscriptionId": subscription_id,
                    "subscriptionStatus": subscription["status"],
                    "expirationDate": subscription["current_period_end"]
                }, merge=True)

        return jsonify({"status": "success"}), 200
