import firebase_admin
from firebase_admin import credentials, firestore, storage
import os
from .config import FIREBASE_CREDENTIALS_PATH, FIREBASE_STORAGE_BUCKET

# Initialize Firebase Admin SDK
def initialize_firebase():
    if not firebase_admin._apps:
        if FIREBASE_CREDENTIALS_PATH and os.path.exists(FIREBASE_CREDENTIALS_PATH):
            cred = credentials.Certificate(FIREBASE_CREDENTIALS_PATH)
            firebase_admin.initialize_app(cred, {
                'storageBucket': FIREBASE_STORAGE_BUCKET
            })
        else:
            # For local development, you can use default credentials
            # Make sure to set GOOGLE_APPLICATION_CREDENTIALS environment variable
            firebase_admin.initialize_app()
    
    return firestore.client(), storage.bucket()

# Get Firestore client
def get_firestore():
    return firestore.client()

# Get Storage bucket
def get_storage_bucket():
    return storage.bucket()

