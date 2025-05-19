from datetime import datetime
from typing import Optional, Dict
import re
from src.core.interfaces import EmailParser

class RegexEmailParser(EmailParser):
    def parse_availability_request(self, email_body: str) -> Optional[Dict]:
        email_body = email_body.lower()
        if 'availability' in email_body or 'available' in email_body:
            date_match = re.search(r'\d{4}-\d{2}-\d{2}', email_body)
            if date_match:
                try:
                    date = datetime.strptime(date_match.group(), '%Y-%m-%d').date()
                    return {'type': 'availability', 'date': date}
                except ValueError:
                    pass
        return None

    def parse_booking_request(self, email_body: str) -> Optional[Dict]:
        email_body = email_body.lower()
        if 'book' in email_body or 'schedule' in email_body:
            date_match = re.search(r'\d{4}-\d{2}-\d{2}', email_body)
            time_match = re.search(r'\d{2}:\d{2}', email_body)
            if date_match and time_match:
                try:
                    date = datetime.strptime(date_match.group(), '%Y-%m-%d').date()
                    time = datetime.strptime(time_match.group(), '%H:%M').time()
                    appointment_time = datetime.combine(date, time)
                    return {
                        'type': 'booking',
                        'date': date.strftime('%Y-%m-%d'),
                        'time': time.strftime('%H:%M'),
                        'appointment_time': appointment_time
                    }
                except ValueError:
                    pass
        return None 