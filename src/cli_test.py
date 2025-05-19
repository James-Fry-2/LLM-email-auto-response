import argparse
from services.ai_responder import AIResponder
from api.email_handler import EmailHandler
from infrastructure.database import get_session
from datetime import datetime

def main():
    parser = argparse.ArgumentParser(description='Test AI Email Response System')
    parser.add_argument('--email', default='test@example.com', help='Test email address')
    parser.add_argument('--name', default='Test User', help='Test user name')
    args = parser.parse_args()

    # Initialize components
    session = get_session()
    email_handler = EmailHandler()
    ai_responder = AIResponder()

    print("\n=== AI Email Response System Test Interface ===")
    print("Type 'exit' to quit\n")

    while True:
        # Get user input
        print("\nEnter your test email message (or 'exit' to quit):")
        email_body = input("> ").strip()
        
        if email_body.lower() == 'exit':
            break

        # Process the email
        print("\nProcessing email...")
        response = email_handler.process_email(
            email_body=email_body,
            from_email=args.email,
            from_name=args.name
        )

        # Display the response
        print("\n=== AI Response ===")
        print(response)
        print("\n=== End Response ===")

        # Show sentiment analysis
        sentiment = ai_responder.analyze_sentiment(email_body)
        print("\n=== Sentiment Analysis ===")
        print(sentiment['sentiment'])
        print("\n=== End Sentiment ===")

        # Show extracted information
        extracted_info = ai_responder.extract_key_information(email_body)
        print("\n=== Extracted Information ===")
        print(extracted_info['extracted_info'])
        print("\n=== End Extracted Information ===")

if __name__ == '__main__':
    main() 