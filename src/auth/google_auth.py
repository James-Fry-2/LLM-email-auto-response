from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import os.path
import os # Ensure os is imported if not already comprehensively at the top

# Define the scope for Gmail API
SCOPES = ['https://mail.google.com/']
TOKEN_PATH = 'token.json' # Path to store/load the token

# Get credentials path from environment variable or use default
CREDENTIALS_PATH_FROM_ENV = os.getenv('GOOGLE_CREDENTIALS_FILE_PATH', 'credentials.json')

def get_gmail_access_token():
    """Gets a valid Gmail access token, handling refresh and new login.
    
    This function implements the OAuth 2.0 flow for a desktop application
    as described in the project's README.md.
    It will look for an existing token in `token.json` or initiate
    a new authorization flow using `credentials.json`.
    
    Returns:
        google.oauth2.credentials.Credentials: A valid Credentials object.
        
    Raises:
        FileNotFoundError: If `credentials.json` is not found during a new login.
        ValueError: If a valid token cannot be obtained.
    """
    creds = None
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                # Log this error or handle it more gracefully
                print(f"Failed to refresh token: {e}. Initiating new login.")
                creds = None # Force new login
        else:
            # Use the resolved credentials path
            credentials_path_to_use = CREDENTIALS_PATH_FROM_ENV
            if not os.path.exists(credentials_path_to_use):
                raise FileNotFoundError(
                    f"Credentials file not found. Searched at path: '{credentials_path_to_use}'. "
                    "This path is determined by the GOOGLE_CREDENTIALS_FILE_PATH environment variable "
                    "or defaults to 'credentials.json' if the variable is not set. "
                    "Please download your OAuth 2.0 client secret JSON from Google Cloud Console."
                )
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path_to_use, SCOPES)
            # For web apps, a different flow and redirect_uri management would be needed.
            creds = flow.run_local_server(port=0) # For Desktop app flow
        
        # Save the credentials for the next run
        with open(TOKEN_PATH, 'w') as token_file:
            token_file.write(creds.to_json())
            
    if not creds or not creds.token: # Check for creds themselves and if token exists within
        raise ValueError("Failed to obtain a valid token.")
        
    return creds.token # Return only the access token string 