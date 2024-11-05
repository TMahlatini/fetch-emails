from flask import Flask, jsonify, request
import os
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError
import logging

app = Flask(__name__)

# Set up logging
logging.basicConfig(level=logging.INFO)

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly', 'https://www.googleapis.com/auth/gmail.modify']
DEVELOPMENT = os.getenv('DEVELOPMENT', 'True').lower() == 'true'

def load_credentials_from_env():
    """Load and decode credentials from environment variables if in production."""
    if not DEVELOPMENT:
        credentials_base64 = os.getenv('CREDENTIALS_JSON_BASE64')
        token_base64 = os.getenv('TOKEN_JSON_BASE64')
        
        if not credentials_base64 or not token_base64:
            logging.error("Environment variables for credentials are missing.")
            return False

        with open('credentials.json', 'wb') as f:
            f.write(base64.b64decode(credentials_base64))

        with open('token.json', 'wb') as f:
            f.write(base64.b64decode(token_base64))
    return True

def update_token_in_env(token_json):
    """Update the environment variable with the refreshed token."""
    if not DEVELOPMENT:
        token_base64 = base64.b64encode(token_json.encode('utf-8')).decode('utf-8')
        os.system(f"heroku config:set TOKEN_JSON_BASE64={token_base64}")

def authenticate_gmail():
    """Authenticate and refresh Gmail API credentials."""
    creds = None
    load_credentials_from_env()
    

    # Attempt to load credentials from token.json
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # If credentials are invalid or missing, refresh them or reauthenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # Save the refreshed token to token.json
                with open('token.json', 'w') as token_file:
                    token_file.write(creds.to_json())
                # Update the environment variable with the refreshed token
                update_token_in_env(creds.to_json())
            except RefreshError as e:
                logging.error("Refresh token is invalid or revoked. Manual reauthentication required.")
        else:
            # Manual authentication flow (only run once if needed)
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            flow.access_type = 'offline'
            creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token_file:
                token_file.write(creds.to_json())
            update_token_in_env(creds.to_json())

    return build('gmail', 'v1', credentials=creds)

@app.route('/fetch-emails', methods=['GET'])
def fetch_emails():
    """Fetch emails based on the specified query."""
    
    service = authenticate_gmail()
    if service is None:
        return jsonify({"error": "Failed to authenticate Gmail service."}), 500

    query = request.args.get('query', 'to:rides@whitman.edu')
    base_query = request.args.get('query', 'to:rides@whitman.edu')
    query = f"{base_query} is:unread"
    results = service.users().messages().list(userId='me', q=query).execute()
    messages = results.get('messages', [])
    
    email_data = []
    for message in messages:
        msg = service.users().messages().get(userId='me', id=message['id'], format='full').execute()
        payload = msg['payload']
        headers = payload.get('headers', [])
        
        subject = next((header['value'] for header in headers if header['name'] == 'Subject'), 'No Subject')
        message_id = next((header['value'] for header in headers if header['name'] == 'Message-ID'), 'No Message-ID')
        sender = next((header['value'] for header in headers if header['name'] == 'From'), 'Unknown Sender')
        date = next((header['value'] for header in headers if header['name'] == 'Date'), 'No Date')
        body = ''

        if 'parts' in payload:
            for part in payload['parts']:
                if part['mimeType'] == 'text/plain' and 'data' in part['body']:
                    body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
        else:
            if 'data' in payload['body']:
                body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')

        email_data.append({
            'subject': subject,
            'body': body,
            'message_id': message_id,
            'sender': sender,
            'date': date
        })
    
 
    for message in messages:
        service.users().messages().modify(
            userId='me',
            id=message['id'],
            body={'removeLabelIds': ['UNREAD']}
        ).execute()
    
    print(jsonify(email_data))
    return jsonify(email_data)

if __name__ == '__main__':
    app.run(port=5002, debug=True)
