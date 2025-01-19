from flask import Blueprint
from ApiFunctions.api_functions import ApiFunctions
from openai import Client
from Config.config import Config
import firebase_admin
from firebase_admin import firestore, credentials

api_bp = Blueprint('api', __name__)
client = Client()
client.api_key = Config.OPENAI_API_KEY
firebase_credentials = credentials.Certificate(Config.FIREBASE_CREDENTIALS_PATH)
firebase_admin.initialize_app(firebase_credentials)
db = firestore.client()

@api_bp.route('/api/create_form', methods=['POST'])
def create_form():
    return ApiFunctions.get_business_emails()

@api_bp.route('/api/call_agent', methods=['POST'])
def call_agent():
    return ApiFunctions.call_openai_agent(client)

@api_bp.route('/api/analyze_feedback', methods=['POST'])
def analyze_feedback():
    return ApiFunctions.analyze_feedback(client)

@api_bp.route('/api/send_email', methods=['POST'])
def send_email():
    return ApiFunctions.send_email()

@api_bp.route('/api/feedback', methods=['POST'])
def feedback():
    return ApiFunctions.feedback()

@api_bp.route("/api/webhook", methods=["POST"])
def webhook():
    return ApiFunctions.stripe_webhook(db)

@api_bp.route("/api/translate_to_bg", methods=["POST"])
def translate_to_bg():
    return ApiFunctions.translate_to_bulgarian()

@api_bp.route("/api/translate_to_en", methods=["POST"])
def translate_to_en():
    return ApiFunctions.translate_to_english()