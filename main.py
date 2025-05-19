from db_handler import DBHandler
from ai_responder import AIResponder
from email_handler import EmailHandler


def main():
    db = DBHandler()
    ai = AIResponder()
    emailer = EmailHandler()

    # Fetch unread emails
    emails = emailer.fetch_unread_emails()
    for mail in emails:
        sender = mail['from']
        subject = mail['subject']
        body = mail['body']
        customer = db.get_customer_info(sender)
        if customer:
            name, info = customer
        else:
            name, info = 'Customer', 'No additional info.'
        response = ai.generate_response(name, info, body)
        emailer.send_email(sender, f"Re: {subject}", response)
        print(f"Auto-responded to {sender}")

if __name__ == "__main__":
    main()    