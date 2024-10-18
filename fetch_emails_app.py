from flask import Flask, jsonify
import os
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
import json

app = Flask(__name__)

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def load_credentials_from_env():
    """
    Load credentials.json and token.json from environment variables (stored as base64)
    and save them to temporary files.
    """
    # Decode and save credentials.json from environment
    credentials_base64 = os.getenv('CREDENTIALS_JSON_BASE64')
    credentials_json = base64.b64decode(credentials_base64).decode('utf-8')
    
    with open('credentials.json', 'w') as f:
        f.write(credentials_json)

    # Decode and save token.json from environment
    token_base64 = os.getenv('TOKEN_JSON_BASE64')
    token_json = base64.b64decode(token_base64).decode('utf-8')
    
    with open('token.json', 'w') as f:
        f.write(token_json)

def update_token_in_env(token_json):
    """
    Update the token.json in the environment variable after refreshing the token.
    """
    token_base64 = base64.b64encode(token_json.encode('utf-8')).decode('utf-8')
    # Update Heroku environment variable with new token.json
    os.system(f"heroku config:set TOKEN_JSON_BASE64={token_base64}")

def authenticate_gmail():
    """
    Authenticate and refresh Gmail API credentials.
    """
    creds = None
    load_credentials_from_env()

    # Load the credentials from token.json file
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # Check if the credentials are valid, refresh if necessary
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            # Save the refreshed token to token.json
            with open('token.json', 'w') as token_file:
                token_file.write(creds.to_json())
            # Update the token in the environment
            update_token_in_env(creds.to_json())
        else:
            # If no valid credentials, start OAuth flow
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            # Save the new token
            with open('token.json', 'w') as token_file:
                token_file.write(creds.to_json())
            # Update the token in the environment
            update_token_in_env(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)
    return service

@app.route('/fetch-emails', methods=['GET'])
def fetch_emails():
    service = authenticate_gmail()
    query = 'to:rides@whitman.edu'
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
            'sender': sender
        })
    print(jsonify(email_data))
    return jsonify(email_data)

if __name__ == '__main__':
    app.run(port=5000, debug=True)
