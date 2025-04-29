import os
import firebase_admin
from firebase_admin import credentials, auth
import pyrebase
import json
from dotenv import load_dotenv

load_dotenv(override=True)

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    firebase_admin_sdk_path = os.getenv("FIREBASE_ADMIN_SDK")
    if not firebase_admin_sdk_path:
        raise ValueError("FIREBASE_ADMIN_SDK environment variable is not set or is empty.")
    if not os.path.exists(firebase_admin_sdk_path):
        raise FileNotFoundError(f"Firebase Admin SDK JSON file not found at: {firebase_admin_sdk_path}")
    cred = credentials.Certificate(firebase_admin_sdk_path)
    firebase_admin.initialize_app(cred)

# Pyrebase configuration
firebase_config = {
    "apiKey": os.getenv("FIREBASE_API_KEY"),
    "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
    "projectId": os.getenv("FIREBASE_PROJECT_ID"),
    "storageBucket": os.getenv("FIREBASE_STORAGE_BUCKET"),
    "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
    "appId": os.getenv("FIREBASE_APP_ID"),
    "measurementId": os.getenv("FIREBASE_MEASUREMENT_ID"),
    "databaseURL": os.getenv("FIREBASE_DATABASE_URL")
}
firebase = pyrebase.initialize_app(firebase_config)
pyrebase_auth = firebase.auth()

def login_user(email, password):
    try:
        user = pyrebase_auth.sign_in_with_email_and_password(email, password)
        return user
    except Exception as e:
        return {"error": str(e)}

def register_user(email, password):
    try:
        user = pyrebase_auth.create_user_with_email_and_password(email, password)
        return user
    except Exception as e:
        return {"error": str(e)}

def verify_token(id_token):
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception as e:
        return {"error": str(e)}
