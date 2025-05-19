import pytest
from datetime import datetime, timedelta

# Import fixtures from conftest

class TestAIEmailSystem:
    """Test cases for the AI Email System"""

    def test_availability_request(self, email_handler, test_customer):
        """Test AI response to availability request"""
        test_email = {
            'body': 'Hi, I would like to check availability for 2024-03-20',
            'from': test_customer.email,
            'subject': 'Availability Check'
        }
        
        response = email_handler.process_email(
            email_body=test_email['body'],
            from_email=test_email['from'],
            from_name=f"{test_customer.first_name} {test_customer.last_name}"
        )
        
        # Verify response contains expected elements
        assert 'available slots' in response.lower()
        assert '2024-03-20' in response
        assert test_customer.first_name in response

    def test_booking_request(self, email_handler, test_customer):
        """Test AI response to booking request"""
        # Use a date 7 days in the future
        future_date = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        test_email = {
            'body': f'I would like to book an appointment for {future_date} at 14:30',
            'from': test_customer.email,
            'subject': 'Booking Request'
        }
        
        response = email_handler.process_email(
            email_body=test_email['body'],
            from_email=test_email['from'],
            from_name=f"{test_customer.first_name} {test_customer.last_name}"
        )
        
        # Verify response contains expected elements
        assert 'appointment' in response.lower()
        assert future_date in response
        assert '14:30' in response

    @pytest.mark.parametrize("email,expected_sentiment", [
        ('I am very frustrated with the service!', 'negative'),
        ('Thank you for your excellent service!', 'positive'),
        ('I need to check my appointment time.', 'neutral')
    ])
    def test_sentiment_analysis(self, ai_responder, email, expected_sentiment):
        """Test sentiment analysis of different email tones"""
        sentiment = ai_responder.analyze_sentiment(email)
        assert expected_sentiment in sentiment['sentiment'].lower()

    def test_information_extraction(self, ai_responder):
        """Test extraction of key information from emails"""
        test_email = """
        Hi, I'm John Smith and I'd like to book an appointment.
        My phone number is 555-0123 and I prefer morning slots.
        I'm interested in the service on 2024-03-20.
        """
        
        extracted_info = ai_responder.extract_key_information(test_email)
        assert extracted_info['extracted_info']['name'] == 'John Smith'
        assert extracted_info['extracted_info']['phone'] == '555-0123'
        assert extracted_info['extracted_info']['date'] == '2024-03-20'

    def test_unknown_request_handling(self, email_handler, test_customer):
        """Test AI response to unknown request types"""
        test_email = {
            'body': 'Hello, I have a general question about your services.',
            'from': test_customer.email,
            'subject': 'General Inquiry'
        }
        
        response = email_handler.process_email(
            email_body=test_email['body'],
            from_email=test_email['from'],
            from_name=f"{test_customer.first_name} {test_customer.last_name}"
        )
        
        # Verify response contains guidance
        assert 'try one of the following' in response.lower()
        assert 'check availability' in response.lower()
        assert 'book an appointment' in response.lower()

    def test_past_date_booking_rejection(self, email_handler, test_customer):
        """Test that booking requests for past dates are rejected"""
        # Use yesterday's date
        past_date = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
        test_email = {
            'body': f'I would like to book an appointment for {past_date} at 14:30',
            'from': test_customer.email,
            'subject': 'Booking Request'
        }
        
        response = email_handler.process_email(
            email_body=test_email['body'],
            from_email=test_email['from'],
            from_name=f"{test_customer.first_name} {test_customer.last_name}"
        )
        
        # Verify response indicates past date rejection
        assert 'cannot process bookings for past dates' in response.lower()
        assert 'future date' in response.lower() 