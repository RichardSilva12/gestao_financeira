import os
import firebase_admin
from firebase_admin import credentials, auth
from dotenv import load_dotenv

load_dotenv()  

cred_path = os.getenv("FIREBASE_CREDENTIAL")

cred = credentials.Certificate(cred_path)
firebase_app = firebase_admin.initialize_app(cred)
firebase_auth = auth
