import os
import smtplib
from imapclient import IMAPClient
from email.message import EmailMessage
from email.parser import BytesParser
from email.policy import default
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json

from src.infrastructure.database import get_session
from src.infrastructure.repositories import SQLAlchemyScheduleRepository, SQLAlchemyBookingRepository
from src.services.email_parser import RegexEmailParser
from src.services.availability import AvailabilityService
from src.services.response import EmailResponseHandler
from src.services.ai_responder import AIResponder
from src.core.models import Customer

load_dotenv()

class EmailHandler:
    def __init__(self):
        self.imap_server = os.getenv('IMAP_SERVER')
        self.smtp_server = os.getenv('SMTP_SERVER')
        self.email_user = os.getenv('EMAIL_USER')
        self.email_pass = os.getenv('EMAIL_PASS')
        
        # Initialize database session
        self.session = get_session()
        
        # Initialize repositories
        self.schedule_repository = SQLAlchemyScheduleRepository(self.session)
        self.booking_repository = SQLAlchemyBookingRepository(self.session)
        
        # Initialize services
        self.email_parser = RegexEmailParser()
        self.availability_service = AvailabilityService(self.session)
        self.response_handler = EmailResponseHandler()
        self.ai_responder = AIResponder()

    def fetch_unread_emails(self):
        with IMAPClient(self.imap_server) as server:
            server.login(self.email_user, self.email_pass)
            server.select_folder('INBOX')
            messages = server.search(['UNSEEN'])
            emails = []
            for uid, message_data in server.fetch(messages, ['RFC822']).items():
                email_message = BytesParser(policy=default).parsebytes(message_data[b'RFC822'])
                emails.append({
                    'uid': uid,
                    'from': email_message['from'],
                    'subject': email_message['subject'],
                    'body': email_message.get_body(preferencelist=('plain')).get_content()
                })
            return emails

    def process_email(self, email_body: str, from_email: str, from_name: str) -> str:
        """Process an email and generate appropriate response using AI"""
        # First, analyze the email content
        sentiment = self.ai_responder.analyze_sentiment(email_body)
        extracted_info = self.ai_responder.extract_key_information(email_body)
        
        # Determine request type
        request_type = None
        if self.email_parser.parse_availability_request(email_body):
            request_type = "availability_request"
        elif self.email_parser.parse_booking_request(email_body):
            request_type = "booking_request"
        
        # Get customer info from database
        customer_info = self.session.query(Customer).filter_by(email=from_email).first()
        customer_context = f"Customer since: {customer_info.created_at.strftime('%Y-%m-%d')}" if customer_info else "New customer"
        
        # Generate AI response
        ai_response = self.ai_responder.generate_response(
            customer_name=from_name,
            customer_info=customer_context,
            email_body=email_body,
            request_type=request_type
        )
        
        # Process the request based on type
        if request_type == "availability_request":
            request = self.email_parser.parse_availability_request(email_body)
            # Use a default service ID of 1 for testing
            available_slots = self.availability_service.get_available_slots(
                date=request['date'],
                service_id=1  # Default service ID for testing
            )
            system_response = self.response_handler.handle_availability_request(request['date'], available_slots)
            # Combine AI response with system response
            final_response = f"{ai_response}\n\n{system_response}"
            
        elif request_type == "booking_request":
            request = self.email_parser.parse_booking_request(email_body)
            if not request:
                system_response = "I couldn't understand the booking details. Please provide a date in YYYY-MM-DD format and time in HH:MM format."
                final_response = f"{ai_response}\n\n{system_response}"
            else:
                # Validate booking date is in the future
                booking_date = datetime.strptime(request['date'], '%Y-%m-%d').date()
                if booking_date < datetime.now().date():
                    system_response = "I apologize, but I cannot process bookings for past dates. Please provide a future date for your appointment."
                    final_response = f"{ai_response}\n\n{system_response}"
                else:
                    # Format the booking data with all required fields
                    booking_time = datetime.strptime(f"{request['date']} {request['time']}", '%Y-%m-%d %H:%M')
                    booking_data = {
                        'name': from_name,
                        'email': from_email,
                        'employee_name': "Test Employee",  # In production, this would be selected based on availability
                        'appointment_time': booking_time,
                        'duration_minutes': 60,  # Default duration, in production this would come from the service
                        'service_id': 1  # Default service ID for testing
                    }
                    
                    # Process booking logic...
                    system_response = self.response_handler.handle_booking_request(booking_data)
                    final_response = f"{ai_response}\n\n{system_response}"
            
        else:
            # For unknown requests, use AI response with guidance
            system_response = self.response_handler.handle_unknown_request()
            final_response = f"{ai_response}\n\n{system_response}"
        
        # Log the interaction
        self._log_interaction(from_email, email_body, final_response, sentiment, extracted_info)
        
        return final_response

    def _log_interaction(self, email: str, request: str, response: str, sentiment: dict, extracted_info: dict):
        """Log customer interaction for analysis"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "email": email,
            "request": request,
            "response": response,
            "sentiment": sentiment,
            "extracted_info": extracted_info
        }
        
        # Save to a log file
        log_file = "customer_interactions.log"
        with open(log_file, "a") as f:
            f.write(json.dumps(log_entry) + "\n")

    def send_email(self, to_address: str, subject: str, body: str):
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = self.email_user
        msg['To'] = to_address
        msg.set_content(body)
        with smtplib.SMTP(self.smtp_server, 587) as server:
            server.starttls()
            server.login(self.email_user, self.email_pass)
            server.send_message(msg)

    def process_unread_emails(self):
        """Process all unread emails and send responses"""
        emails = self.fetch_unread_emails()
        for email in emails:
            response = self.process_email(
                email_body=email['body'],
                from_email=email['from'],
                from_name=email['from'].split('@')[0]  # Simple name extraction
            )
            self.send_email(
                to_address=email['from'],
                subject="Re: " + email['subject'],
                body=response
            ) 