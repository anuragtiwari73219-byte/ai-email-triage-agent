"""
Configuration constants for the AI Email Triage Agent.
"""

import os
from dotenv import load_dotenv

load_dotenv()

# ─── Gmail API ────────────────────────────────────────────────────────────────
GMAIL_SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.compose',
    'https://www.googleapis.com/auth/gmail.labels',
    'https://www.googleapis.com/auth/gmail.modify',
]

CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'

# ─── Email Fetching ──────────────────────────────────────────────────────────
MAX_EMAILS = 20

# ─── Google Gemini AI ────────────────────────────────────────────────────────
GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')

# ─── Categorization ─────────────────────────────────────────────────────────
URGENCY_LEVELS = ['High', 'Medium', 'Low']
TOPICS = ['Work', 'Finance', 'Promotions', 'Personal', 'Spam']

# ─── Gmail Labels ────────────────────────────────────────────────────────────
URGENT_LABEL_NAME = 'URGENT-FLAG'
URGENT_LABEL_COLOR = {
    'textColor': '#ffffff',
    'backgroundColor': '#cc3a21',  # Red
}

# ─── Flask ───────────────────────────────────────────────────────────────────
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5000
FLASK_DEBUG = True
