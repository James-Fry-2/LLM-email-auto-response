import imaplib
import base64
import email
from email.header import decode_header
from .base_connector import EmailConnector

class GmailConnector(EmailConnector):
    """
    Connects to a Gmail account using IMAP with OAuth 2.0 (XOAUTH2).
    """
    IMAP_HOST = 'imap.gmail.com'
    IMAP_PORT = 993

    def __init__(self, user_email, access_token_provider):
        """
        Initializes the GmailConnector.

        Args:
            user_email (str): The user's Gmail address.
            access_token_provider (callable): A function that returns a valid 
                                              OAuth 2.0 access token.
                                              This function will be called when
                                              a new token is needed.
        """
        self.user_email = user_email
        self.access_token_provider = access_token_provider
        self.imap_server = None
        self._access_token = None # Store current token

    def _get_fresh_access_token(self):
        """Fetches a fresh access token using the provider."""
        if not callable(self.access_token_provider):
            raise ValueError("access_token_provider must be a callable function.")
        try:
            self._access_token = self.access_token_provider()
            if not self._access_token:
                raise ValueError("access_token_provider returned an empty token.")
        except Exception as e:
            # Log this error appropriately in a real application
            print(f"Error obtaining access token: {e}")
            raise ConnectionError("Failed to obtain access token.") from e
        return self._access_token

    def connect(self):
        """
        Connects to Gmail IMAP server and authenticates using XOAUTH2.
        """
        try:
            access_token = self._get_fresh_access_token()
            
            auth_string = f"user={self.user_email}\x01auth=Bearer {access_token}\x01\x01".encode('utf-8')

            self.imap_server = imaplib.IMAP4_SSL(self.IMAP_HOST, self.IMAP_PORT)
            
            # Log the command being sent
            # print(f"C: AUTHENTICATE XOAUTH2 <auth_string_base64_sent_to_lambda>")
            
            # The lambda now returns the raw bytes of the auth_string, imaplib will Base64 encode it.
            # Ensure the second argument is the LAMBDA, not auth_string directly.
            status, response = self.imap_server.authenticate('XOAUTH2', lambda x: auth_string)
            
            if status != 'OK':
                # Decode error response if available
                error_detail = ""
                try:
                    # The response from server might be a list of bytes
                    if isinstance(response, list) and len(response) > 0 and isinstance(response[0], bytes):
                        decoded_error = base64.b64decode(response[0]).decode('utf-8')
                        error_detail = f" Server response: {decoded_error}"
                except Exception:
                    pass # Ignore decoding errors, use raw response
                raise ConnectionError(f"XOAUTH2 authentication failed: {status} - {response}.{error_detail}")

            print(f"Successfully authenticated as {self.user_email}")
            return True
        except imaplib.IMAP4.error as e:
            # Log this error
            print(f"IMAP connection error: {e}")
            self.imap_server = None # Ensure server is None if connection failed
            raise ConnectionError(f"Failed to connect to Gmail IMAP: {e}") from e
        except Exception as e: # Catch other potential errors like token provider issues
            print(f"An unexpected error occurred during connect: {e}")
            self.imap_server = None
            raise

    def disconnect(self):
        """
        Logs out and closes the IMAP connection.
        """
        if self.imap_server:
            try:
                self.imap_server.logout()
                print(f"Logged out from {self.user_email}")
            except imaplib.IMAP4.error as e:
                # Log this error, but don't prevent shutdown
                print(f"Error during logout: {e}")
            finally:
                self.imap_server = None
        else:
            print("Not connected, no need to disconnect.")


    def _decode_header(self, header_value):
        """Decodes email header, handling multiple encodings."""
        if header_value is None:
            return ""
        parts = decode_header(header_value)
        decoded_parts = []
        for part, charset in parts:
            if isinstance(part, bytes):
                try:
                    decoded_parts.append(part.decode(charset or 'utf-8', errors='replace'))
                except LookupError: # Unknown encoding
                    decoded_parts.append(part.decode('utf-8', errors='replace')) # Fallback
            else: # Already a string
                decoded_parts.append(part)
        return "".join(decoded_parts)

    def read_emails(self, criteria="UNSEEN", mailbox="INBOX", num_emails=10):
        """
        Reads emails from the specified mailbox based on criteria.

        Args:
            criteria (str): Search criteria (e.g., "UNSEEN", "ALL", "FROM \"user@example.com\"").
            mailbox (str): The mailbox to read from (default: "INBOX").
            num_emails (int): Maximum number of emails to fetch.

        Returns:
            list: A list of dictionaries, each representing an email.
                  Returns empty list on failure or if no emails found.
        """
        if not self.imap_server:
            # print("Not connected. Call connect() first.")
            # Or attempt to reconnect:
            print("Not connected. Attempting to reconnect...")
            try:
                self.connect()
            except ConnectionError as e:
                print(f"Reconnection failed: {e}")
                return []

        emails_data = []
        try:
            status, _ = self.imap_server.select(mailbox)
            if status != 'OK':
                print(f"Failed to select mailbox {mailbox}: {status}")
                return emails_data

            # Search for emails
            # The criteria needs to be a string. If it contains non-ASCII, it needs to be UTF-8 encoded.
            # However, imaplib handles this internally for the search command if you pass a string.
            # For literals like "SUBJECT \"My Subject\"", ensure correct quoting.
            status, data = self.imap_server.search(None, criteria) # `None` for default charset (usually UTF-8)
            if status != 'OK':
                print(f"Failed to search emails with criteria '{criteria}': {status}")
                return emails_data

            email_ids = data[0].split()
            if not email_ids:
                print(f"No emails found matching criteria '{criteria}' in {mailbox}.")
                return emails_data

            # Fetch latest N emails
            latest_email_ids = email_ids[-num_emails:]

            for email_id in reversed(latest_email_ids): # Fetch newest first
                status, msg_data = self.imap_server.fetch(email_id, '(RFC822)')
                if status != 'OK':
                    print(f"Failed to fetch email ID {email_id.decode()}: {status}")
                    continue

                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        subject = self._decode_header(msg.get("Subject"))
                        from_ = self._decode_header(msg.get("From"))
                        to_ = self._decode_header(msg.get("To"))
                        date_ = self._decode_header(msg.get("Date"))
                        
                        body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                content_disposition = str(part.get("Content-Disposition"))

                                if "attachment" not in content_disposition:
                                    if content_type == "text/plain":
                                        try:
                                            payload = part.get_payload(decode=True)
                                            charset = part.get_content_charset() or 'utf-8'
                                            body = payload.decode(charset, errors='replace')
                                            break # Prefer plain text
                                        except Exception as e:
                                            print(f"Error decoding plain text part: {e}")
                                    elif content_type == "text/html" and not body: # Fallback to HTML if no plain text
                                        try:
                                            payload = part.get_payload(decode=True)
                                            charset = part.get_content_charset() or 'utf-8'
                                            # In a real app, you'd sanitize this HTML or use a library to convert to text
                                            body = payload.decode(charset, errors='replace') 
                                        except Exception as e:
                                            print(f"Error decoding HTML part: {e}")
                        else: # Not multipart
                            try:
                                payload = msg.get_payload(decode=True)
                                charset = msg.get_content_charset() or 'utf-8'
                                body = payload.decode(charset, errors='replace')
                            except Exception as e:
                                print(f"Error decoding non-multipart body: {e}")

                        emails_data.append({
                            'id': email_id.decode(),
                            'subject': subject,
                            'from': from_,
                            'to': to_,
                            'date': date_,
                            'body': body.strip() # Strip leading/trailing whitespace
                        })
            return emails_data

        except imaplib.IMAP4.error as e:
            print(f"IMAP error while reading emails: {e}")
            # Check if connection is broken (e.g., by timeout)
            if isinstance(e, (imaplib.IMAP4.abort, imaplib.IMAP4.readonly)):
                print("IMAP connection lost. Attempting to disconnect.")
                self.disconnect() # Mark as disconnected
            return [] # Return empty list on error
        except Exception as e:
            print(f"An unexpected error occurred during read_emails: {e}")
            return []
            
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()

# Example Usage (Illustrative - requires a real access_token_provider)
if __name__ == '__main__':
    # This is a placeholder. In a real app, this function would
    # use a library like google-auth-oauthlib to get a token.
    def sample_token_provider():
        print("Requesting new access token...")
        # In a real scenario, this would involve OAuth flow or reading a stored token.
        # For testing, you might manually paste a short-lived token here.
        # IMPORTANT: Do NOT commit real tokens to version control.
        # return "YOUR_MANUALLY_OBTAINED_ACCESS_TOKEN" 
        raise NotImplementedError("Please implement a real token provider.")

    USER_EMAIL = "your_email@gmail.com" # Replace with your Gmail address

    if USER_EMAIL == "your_email@gmail.com":
        print("Please configure USER_EMAIL and a real sample_token_provider.")
    else:
        print(f"Attempting to connect to Gmail as {USER_EMAIL}...")
        print("NOTE: This example will fail without a valid access_token_provider and OAuth setup.")
        
        try:
            with GmailConnector(USER_EMAIL, sample_token_provider) as gmail:
                print("\nFetching unseen emails...")
                unseen_emails = gmail.read_emails(criteria="UNSEEN", num_emails=5)
                if unseen_emails:
                    for email_info in unseen_emails:
                        print(f"\n--- Email ID: {email_info['id']} ---")
                        print(f"From: {email_info['from']}")
                        print(f"Subject: {email_info['subject']}")
                        print(f"Date: {email_info['date']}")
                        print(f"Body Preview: {email_info['body'][:200]}...")
                else:
                    print("No unseen emails found or error fetching them.")

        except ConnectionError as e:
            print(f"Connection failed: {e}")
        except NotImplementedError as e:
            print(f"Setup incomplete: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}") 