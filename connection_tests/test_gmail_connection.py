import sys
import os
from dotenv import load_dotenv

# Adjust path to find the 'src' directory from 'connection_tests' folder
# __file__ is .../connection_tests/test_gmail_connection.py
# current_script_dir is .../connection_tests
# project_root should be .../ (one level up from current_script_dir)
current_script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_script_dir)
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)
print(src_path)

# Load .env file from project root
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path)

try:
    from connectors.gmail_connector import GmailConnector
    from auth.google_auth import get_gmail_access_token
except ImportError as e:
    print(f"Error importing modules: {e}")
    print(f"Attempted to add {src_path} to sys.path based on script location.")
    print("Please ensure 'src' directory exists at the project root and this script is in a subdirectory like 'connection_tests'.")
    sys.exit(1)

# --- Get USER_EMAIL from environment variable ---
USER_EMAIL = os.getenv("GMAIL_TEST_USER_EMAIL")
# ---

def main():
    if not USER_EMAIL:
        print("ERROR: GMAIL_TEST_USER_EMAIL not found in environment variables.")
        print(f"Please set it in your .env file at {dotenv_path}")
        return

    print(f"Attempting to connect to Gmail as {USER_EMAIL}...")
    print("This will use the get_gmail_access_token function, which may open a browser for OAuth.")

    try:
        with GmailConnector(USER_EMAIL, get_gmail_access_token) as gmail:
            print(f"\nSuccessfully connected to {USER_EMAIL}")
            
            print("\nFetching last 5 unseen emails...")
            emails = gmail.read_emails(criteria="UNSEEN", mailbox="INBOX", num_emails=5)
            
            if emails:
                for email_data in emails:
                    print(f"\n--- Email ID: {email_data['id']} ---")
                    print(f"From: {email_data['from']}")
                    print(f"Subject: {email_data['subject']}")
                    print(f"Date: {email_data['date']}")
                    body_preview = email_data.get('body', 'N/A')[:200]
                    print(f"Body Preview: {body_preview}...")
            else:
                print("No new unseen emails found or an error occurred while fetching.")

    except FileNotFoundError as e:
        print(f"\n--- CONFIGURATION ERROR ---")
        print(f"{e}")
        print("Please ensure your Google Cloud OAuth 2.0 credentials JSON file is available.")
        print("The system looks for it based on the 'GOOGLE_CREDENTIALS_FILE_PATH' environment variable,")
        print("or defaults to a file named 'credentials.json' in the project root if the env var is not set.")
    except ConnectionError as e:
        print(f"\n--- CONNECTION ERROR ---")
        print(f"Failed to connect: {e}")
        print("This could be due to incorrect credentials, network issues, or Gmail IMAP not being enabled for the account.")
    except Exception as e:
        print(f"\n--- UNEXPECTED ERROR ---")
        print(f"An unexpected error occurred: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main() 