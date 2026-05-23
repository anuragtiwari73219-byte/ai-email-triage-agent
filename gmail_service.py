"""
Gmail API service for OAuth 2.0 authentication, reading emails,
creating drafts, and managing labels.

Safety: This module NEVER calls messages.send(). All replies are drafts only.
"""

import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config import (
    GMAIL_SCOPES,
    CREDENTIALS_FILE,
    TOKEN_FILE,
    URGENT_LABEL_NAME,
    URGENT_LABEL_COLOR,
)


class GmailService:
    """Handles all Gmail API interactions."""

    def __init__(self):
        self.service = None
        self.creds = None
        self.user_email = None

    # ─── Authentication ──────────────────────────────────────────────────

    def authenticate(self):
        """
        Run the OAuth 2.0 flow.
        - Loads existing token from disk if available.
        - Refreshes expired tokens automatically.
        - Opens browser for consent if no valid token exists.
        """
        creds = None

        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, GMAIL_SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists(CREDENTIALS_FILE):
                    raise FileNotFoundError(
                        f"'{CREDENTIALS_FILE}' not found. "
                        "Download it from Google Cloud Console → APIs & Services → Credentials."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(
                    CREDENTIALS_FILE, GMAIL_SCOPES
                )
                creds = flow.run_local_server(port=0, prompt='consent')

            # Persist the token for future runs
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())

        self.creds = creds
        self.service = build('gmail', 'v1', credentials=creds)

        # Fetch authenticated user's email
        profile = self.service.users().getProfile(userId='me').execute()
        self.user_email = profile.get('emailAddress', '')

        return True

    def is_authenticated(self):
        """Check if we have a valid Gmail service."""
        return self.service is not None

    # ─── Read Emails ─────────────────────────────────────────────────────

    def get_emails(self, max_results=20):
        """
        Fetch the most recent inbox emails.
        Returns a list of dicts with id, thread_id, subject, from, to,
        date, snippet, body, and labels.
        """
        if not self.service:
            raise Exception("Not authenticated. Call authenticate() first.")

        results = (
            self.service.users()
            .messages()
            .list(userId='me', labelIds=['INBOX'], maxResults=max_results)
            .execute()
        )

        messages = results.get('messages', [])
        emails = []

        for msg in messages:
            msg_data = (
                self.service.users()
                .messages()
                .get(userId='me', id=msg['id'], format='full')
                .execute()
            )

            headers = msg_data.get('payload', {}).get('headers', [])
            header_map = {}
            for h in headers:
                header_map[h['name'].lower()] = h['value']

            email_info = {
                'id': msg['id'],
                'thread_id': msg_data.get('threadId', ''),
                'subject': header_map.get('subject', '(No Subject)'),
                'from': header_map.get('from', 'Unknown'),
                'to': header_map.get('to', ''),
                'date': header_map.get('date', ''),
                'snippet': msg_data.get('snippet', ''),
                'body': self._extract_body(msg_data),
                'labels': msg_data.get('labelIds', []),
            }
            emails.append(email_info)

        return emails

    def _extract_body(self, msg_data):
        """Extract plain-text body from an email message."""
        payload = msg_data.get('payload', {})

        # Direct text/plain message
        if payload.get('mimeType') == 'text/plain':
            data = payload.get('body', {}).get('data', '')
            if data:
                return base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')

        # Multipart — look for text/plain part
        parts = payload.get('parts', [])
        for part in parts:
            if part.get('mimeType') == 'text/plain':
                data = part.get('body', {}).get('data', '')
                if data:
                    return base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')

            # Nested multipart
            nested_parts = part.get('parts', [])
            for nested in nested_parts:
                if nested.get('mimeType') == 'text/plain':
                    data = nested.get('body', {}).get('data', '')
                    if data:
                        return base64.urlsafe_b64decode(data).decode(
                            'utf-8', errors='replace'
                        )

        # Fallback to snippet
        return msg_data.get('snippet', '')

    # ─── Create Drafts (NEVER sends) ────────────────────────────────────

    def create_draft(self, to, subject, body, thread_id=None):
        """
        Create a Gmail draft reply.
        ⚠️ This ONLY saves a draft. It does NOT call messages.send().
        """
        if not self.service:
            raise Exception("Not authenticated.")

        message = MIMEText(body, 'plain', 'utf-8')
        message['to'] = to
        message['from'] = self.user_email or 'me'
        message['subject'] = f"Re: {subject}" if not subject.startswith('Re:') else subject

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

        draft_body = {'message': {'raw': raw}}
        if thread_id:
            draft_body['message']['threadId'] = thread_id

        draft = (
            self.service.users()
            .drafts()
            .create(userId='me', body=draft_body)
            .execute()
        )

        return draft

    # ─── Label Management ────────────────────────────────────────────────

    def add_urgent_label(self, message_id):
        """
        Add the red 'URGENT-FLAG' label to a message.
        Creates the label if it doesn't exist yet.
        """
        if not self.service:
            raise Exception("Not authenticated.")

        label_id = self._get_or_create_label(URGENT_LABEL_NAME)

        self.service.users().messages().modify(
            userId='me',
            id=message_id,
            body={'addLabelIds': [label_id]},
        ).execute()

        return label_id

    def _get_or_create_label(self, label_name):
        """Find an existing Gmail label by name, or create it with red color."""
        labels_response = self.service.users().labels().list(userId='me').execute()

        for label in labels_response.get('labels', []):
            if label['name'] == label_name:
                return label['id']

        # Create new label
        label_body = {
            'name': label_name,
            'labelListVisibility': 'labelShow',
            'messageListVisibility': 'show',
            'color': URGENT_LABEL_COLOR,
        }

        created = (
            self.service.users()
            .labels()
            .create(userId='me', body=label_body)
            .execute()
        )

        return created['id']
