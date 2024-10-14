from flask import Flask, jsonify
import os.path
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

app = Flask(__name__)

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def authenticate_gmail():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

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
