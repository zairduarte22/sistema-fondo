import os
import firebase_admin
from firebase_admin import credentials, auth
import pyrebase
import json
import streamlit as st

# Construct Firebase Admin SDK JSON dynamically
firebase_admin_sdk_json = {
    "type": st.secrets["auth"]["FIREBASE_ADMIN_SDK"]["type"],
    "project_id": st.secrets["auth"]["FIREBASE_ADMIN_SDK"]["project_id"],
    "private_key_id": st.secrets["auth"]["FIREBASE_ADMIN_SDK"]["private_key_id"],
    "private_key": st.secrets["auth"]["FIREBASE_ADMIN_SDK"]["private_key"],
    "client_email": st.secrets["auth"]["FIREBASE_ADMIN_SDK"]["client_email"],
    "client_id": st.secrets["auth"]["FIREBASE_ADMIN_SDK"]["client_id"],
    "auth_uri": st.secrets["auth"]["FIREBASE_ADMIN_SDK"]["auth_uri"],
    "token_uri": st.secrets["auth"]["FIREBASE_ADMIN_SDK"]["token_uri"],
    "auth_provider_x509_cert_url": st.secrets["auth"]["FIREBASE_ADMIN_SDK"]["auth_provider_x509_cert_url"],
    "client_x509_cert_url": st.secrets["auth"]["FIREBASE_ADMIN_SDK"]["client_x509_cert_url"],
    "universe_domain": st.secrets["auth"]["FIREBASE_ADMIN_SDK"]["universe_domain"]
}

# Initialize Firebase Admin SDK
if not firebase_admin._apps:
    cred = credentials.Certificate(firebase_admin_sdk_json)
    firebase_admin.initialize_app(cred)

# Pyrebase configuration
firebase_config = {
    "apiKey": st.secrets["auth"]["login"]["FIREBASE_API_KEY"],
    "authDomain": st.secrets["auth"]["login"]["FIREBASE_AUTH_DOMAIN"],
    "projectId": st.secrets["auth"]["login"]["FIREBASE_PROJECT_ID"],
    "storageBucket": st.secrets["auth"]["login"]["FIREBASE_STORAGE_BUCKET"],
    "messagingSenderId": st.secrets["auth"]["login"]["FIREBASE_MESSAGING_SENDER_ID"],
    "appId": st.secrets["auth"]["login"]["FIREBASE_APP_ID"],
    "measurementId": st.secrets["auth"]["login"]["FIREBASE_MEASUREMENT_ID"],
    "databaseURL": st.secrets["auth"]["login"]["FIREBASE_DATABASE_URL"]
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
