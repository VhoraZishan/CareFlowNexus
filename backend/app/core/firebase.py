import os
from dotenv import load_dotenv
import firebase_admin
from firebase_admin import credentials, firestore

# Load .env BEFORE reading env vars
load_dotenv()

cred_path = os.getenv("FIREBASE_CRED_PATH")

if not cred_path:
    raise RuntimeError("FIREBASE_CRED_PATH is not set")

cred = credentials.Certificate(cred_path)
firebase_admin.initialize_app(cred)

db = firestore.client()
