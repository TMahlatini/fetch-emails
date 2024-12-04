# Gmail Email Fetcher API

A Flask-based REST API that fetches and processes emails from Gmail using the Gmail API. This application is designed to retrieve emails matching specific queries and return them in a structured JSON format.

## Features

- Gmail API integration with OAuth 2.0 authentication
- Configurable email query parameters
- Returns email data including subject, body, sender, date, and message ID
- Support for both development and production environments
- Automatic token refresh handling

## Prerequisites

- Python 3.x
- Google Cloud Platform account
- Gmail API enabled
- OAuth 2.0 credentials configured

## Environment Variables

### Development
No environment variables required. The application will use local credential files.

### Production
The following environment variables must be set:
- `DEVELOPMENT`: Set to 'false'
- `CREDENTIALS_JSON_BASE64`: Base64 encoded Google OAuth credentials
- `TOKEN_JSON_BASE64`: Base64 encoded OAuth token

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd <repository-name>

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Setup Google OAUTH creds:

    a. Go to https://console.cloud.google.com/apis/credentials
    b. Create new credentials
    c. Select OAuth 2.0 client IDs
    d. Select Desktop app
    e. Download the credentials file and put it in the root of the project as `credentials.json`

## Usage

### Starting the Server

1. Start the server:
```bash
python3 fetch_emails_app.py
```

The server will start on port 5002 by default.

### API Endpoints

#### GET /fetch-emails
Fetches emails based on the specified query. If no query is provided, the default query is `is:unread`.

Query Parameters:
- `query` 

Example Request:
```bash
curl "http://localhost:5002/fetch-emails?query=from:example@email.com"
curl "http://localhost:5002/fetch-emails" # default query is "is:unread"
```

Response Format:
```json
[
  {
    "subject": "Email Subject",
    "body": "Email Body",
    "message_id": "<message-id>",
    "sender": "sender@email.com",
    "date": "Email Date"
  }
]
```

## Development vs Production

- Development mode uses local credential files
- Production mode loads credentials from environment variables
- Set `DEVELOPMENT=false` in production environment

## Error Handling

- Invalid credentials will return a 500 error
- Missing environment variables in production will be logged
- Token refresh errors are handled automatically

## Security Notes

- Keep your credentials.json and token.json secure
- Never commit these files to version control
- In production, always use environment variables for sensitive data


