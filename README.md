# Email Integration System

A Python-based system for integrating with email services, currently supporting Gmail IMAP with OAuth2 authentication.

## Features

- Gmail IMAP integration with OAuth2 authentication
- Email reading and processing capabilities
- SQLAlchemy-based data models for storing email-related data
- Availability scheduling system for appointments
- Caching system for improved performance

## Project Structure

```
src/
├── connectors/         # Email service connectors
├── core/              # Core models and business logic
├── infrastructure/    # Database and external service implementations
└── services/          # Business services
tests/                 # Test files
```

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/email-integration.git
cd email-integration
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file with the following variables:
```
GMAIL_CLIENT_ID=your_client_id
GMAIL_CLIENT_SECRET=your_client_secret
DATABASE_URL=your_database_url
```

## Usage

### Gmail Integration

```python
from src.connectors.gmail_connector import GmailConnector
from src.auth.google_auth import get_gmail_access_token

# Initialize the connector
connector = GmailConnector(
    user_email="your.email@gmail.com",
    access_token_provider=get_gmail_access_token
)

# Connect and read emails
with connector as gmail:
    emails = gmail.read_emails(criteria="UNSEEN", num_emails=10)
    for email in emails:
        print(f"Subject: {email['subject']}")
        print(f"From: {email['from']}")
        print(f"Body: {email['body'][:200]}...")
```

## Development

### Running Tests

```bash
pytest tests/
```

### Code Style

This project follows PEP 8 style guidelines. To check your code:

```bash
flake8 src/ tests/
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for providing the GPT models
- SQLAlchemy for database ORM
- pytest for testing framework

## Connecting a Gmail Inbox (OAuth 2.0)

This application can read emails from a Gmail inbox using OAuth 2.0 for secure authentication. This method is preferred over using passwords directly.

### 1. Prerequisites:
   - A Google Account.
   - The `google-auth` and `google-auth-oauthlib` Python libraries. You can install them by adding `google-auth google-auth-oauthlib` to your `requirements.txt` and running `pip install -r requirements.txt`.

### 2. Set up OAuth 2.0 Credentials in Google Cloud Console:

   a. **Go to the Google Cloud Console:** [https://console.cloud.google.com/](https://console.cloud.google.com/)

   b. **Create or Select a Project:**
      - If you don't have a project, create one.
      - Otherwise, select an existing project.

   c. **Enable the Gmail API:**
      - In the navigation menu, go to "APIs & Services" > "Library".
      - Search for "Gmail API" and enable it for your project.

   d. **Configure OAuth Consent Screen:**
      - Go to "APIs & Services" > "OAuth consent screen".
      - Choose "External" if you're not a Google Workspace user, or "Internal" if you are and want to limit it to your organization.
      - Fill in the required application details (App name, User support email, Developer contact information).
      - **Scopes:** You don't need to add scopes here initially if your application will request them dynamically. However, the primary scope used by the `GmailConnector` for reading emails is `https://mail.google.com/`.
      - **Test Users:** Add your Gmail account(s) as test users while your app is in "testing" mode to avoid the "unverified app" screen for these accounts.

   e. **Create OAuth 2.0 Client ID:**
      - Go to "APIs & Services" > "Credentials".
      - Click "+ CREATE CREDENTIALS" and select "OAuth client ID".
      - **Application type:**
          - For local testing and desktop applications, choose "Desktop app".
          - If you're building a web application that will run on a server, choose "Web application". You'll need to specify "Authorized redirect URIs" (e.g., `http://localhost:8080/oauth2callback` for local development, or your production callback URL).
      - Give your client ID a name (e.g., "Gmail Connector Client").
      - After creation, Google will provide you with a **Client ID** and **Client Secret**. Download the JSON file or copy these values. **Store them securely and never commit them to your version control.**

### 3. Storing Credentials Securely:

   It's recommended to store your Client ID and Client Secret (and any downloaded JSON file) securely:
   - **Environment Variables:** Set environment variables like `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`.
   - **Configuration File:** Use a configuration file that is *not* committed to version control (e.g., add it to `.gitignore`).

   The downloaded `client_secret_....json` file is often used by Google's client libraries to manage the OAuth flow.

### 4. Implementing an Access Token Provider:

   The `GmailConnector` class (in `src/connectors/gmail_connector.py`) requires an `access_token_provider` function in its constructor. This function is responsible for obtaining and returning a valid OAuth 2.0 access token.

   Here's a conceptual example of how you might implement such a provider using `google-auth-oauthlib` for a desktop application flow. You'll need to adapt this to your application's specific needs (e.g., web app flow, token storage, and refresh logic).

   ```python
   # In a new file, e.g., src/auth/google_auth.py
   from google_auth_oauthlib.flow import InstalledAppFlow
   from google.auth.transport.requests import Request
   from google.oauth2.credentials import Credentials
   import os.path

   # Define the scope
   SCOPES = ['https://mail.google.com/']
   TOKEN_PATH = 'token.json' # Path to store/load the token
   CREDENTIALS_PATH = 'credentials.json' # Path to your downloaded client_secret_....json

   def get_gmail_access_token():
       """Gets a valid Gmail access token, handling refresh and new login."""
       creds = None
       # The file token.json stores the user's access and refresh tokens, and is
       # created automatically when the authorization flow completes for the first time.
       if os.path.exists(TOKEN_PATH):
           creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
       
       # If there are no (valid) credentials available, let the user log in.
       if not creds or not creds.valid:
           if creds and creds.expired and creds.refresh_token:
               try:
                   creds.refresh(Request())
               except Exception as e:
                   print(f"Failed to refresh token: {e}. Initiating new login.")
                   creds = None # Force new login
           else:
               if not os.path.exists(CREDENTIALS_PATH):
                   raise FileNotFoundError(
                       f"Credentials file not found at {CREDENTIALS_PATH}. "
                       "Please download your OAuth 2.0 client secret JSON from Google Cloud Console."
                   )
               flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
               # For web apps, you'd use a different flow, e.g., from google_auth_oauthlib.flow import Flow
               # and manage redirect_uri.
               creds = flow.run_local_server(port=0) # For Desktop app flow
           
           # Save the credentials for the next run
           with open(TOKEN_PATH, 'w') as token_file:
               token_file.write(creds.to_json())
       
       if not creds.token:
           raise ValueError("Failed to obtain a valid token.")
       return creds.token
   ```

### 5. Using the `GmailConnector`:

   Once you have your `access_token_provider` function, you can use the `GmailConnector`:

   ```python
   from src.connectors.gmail_connector import GmailConnector
   from src.auth.google_auth import get_gmail_access_token # Assuming you created this

   USER_EMAIL = "your-company-email@gmail.com" # The Gmail account to read from

   def main():
       try:
           # The get_gmail_access_token function will handle the OAuth flow
           # (prompting for login the first time, refreshing tokens, etc.)
           with GmailConnector(USER_EMAIL, get_gmail_access_token) as gmail:
               print(f"Successfully connected to {USER_EMAIL}")
               
               print("\nFetching last 5 unseen emails...")
               # You can customize criteria, mailbox, and number of emails
               emails = gmail.read_emails(criteria="UNSEEN", mailbox="INBOX", num_emails=5)
               
               if emails:
                   for email_data in emails:
                       print(f"\n--- Email ID: {email_data['id']} ---")
                       print(f"From: {email_data['from']}")
                       print(f"Subject: {email_data['subject']}")
                       print(f"Date: {email_data['date']}")
                       print(f"Body Preview: {email_data['body'][:200]}...")
               else:
                   print("No new emails found or an error occurred.")

       except FileNotFoundError as e:
           print(f"Configuration error: {e}")
           print("Please ensure 'credentials.json' is in the correct location and you've run the auth flow once.")
       except ConnectionError as e:
           print(f"Connection failed: {e}")
       except Exception as e:
           print(f"An unexpected error occurred: {e}")

   if __name__ == '__main__':
       main()
   ```

   **Note:** The first time you run code that uses `get_gmail_access_token` (or a similar function from `google-auth-oauthlib`), it will typically open a web browser to ask you to log in to your Google account and authorize the application. After successful authorization, a `token.json` (or similar) file will be created to store the access and refresh tokens, so you won't need to log in every time. 