from datetime import datetime, timedelta
from sqlalchemy.orm import sessionmaker
from src.infrastructure.database import init_db
from src.infrastructure.repositories import SQLAlchemyScheduleRepository, SQLAlchemyBookingRepository
from email_parser import RegexEmailParser
from availability import AvailabilityService
from response import EmailResponseHandler

class AppointmentManager:
    def __init__(self):
        self.engine = init_db()
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # Initialize repositories
        self.schedule_repository = SQLAlchemyScheduleRepository(self.session)
        self.booking_repository = SQLAlchemyBookingRepository(self.session)
        
        # Initialize services
        self.email_parser = RegexEmailParser()
        self.availability_service = AvailabilityService(
            self.schedule_repository,
            self.booking_repository
        )
        self.response_handler = EmailResponseHandler()
        
    def get_available_slots(self, date, employee_id=None):
        """Get available slots for a specific date and optionally for a specific employee"""
        return self.availability_service.get_available_slots(date, employee_id)

    def create_booking(self, email, name, appointment_time, employee_id, duration_minutes=30):
        """Create a new booking"""
        booking_data = {
            'email': email,
            'name': name,
            'employee_id': employee_id,
            'appointment_time': appointment_time,
            'duration_minutes': duration_minutes
        }
        return self.booking_repository.create_booking(booking_data)

    def parse_email_request(self, email_body):
        """Parse email content to determine the type of request"""
        availability_request = self.email_parser.parse_availability_request(email_body)
        if availability_request:
            return availability_request
            
        booking_request = self.email_parser.parse_booking_request(email_body)
        if booking_request:
            return booking_request
            
        return {'type': 'unknown'}

    def process_email(self, email_body: str, from_email: str, from_name: str) -> str:
        """Process an email and generate appropriate response"""
        request = self.email_parser.parse_availability_request(email_body)
        if request:
            available_slots = self.availability_service.get_available_slots(request['date'])
            return self.response_handler.handle_availability_request(request['date'], available_slots)
            
        request = self.email_parser.parse_booking_request(email_body)
        if request:
            # Find the first available employee for the requested time
            day_of_week = request['appointment_time'].weekday()
            schedules = self.schedule_repository.get_all_schedules_for_day(day_of_week)
            
            for schedule in schedules:
                start_time = datetime.combine(request['appointment_time'].date(), schedule['start_time'])
                end_time = datetime.combine(request['appointment_time'].date(), schedule['end_time'])
                
                if start_time <= request['appointment_time'] < end_time:
                    # Check if the slot is actually available
                    bookings = self.booking_repository.get_bookings_for_employee(
                        schedule['id'], 
                        request['appointment_time']
                    )
                    
                    slot_available = True
                    for booking in bookings:
                        if (request['appointment_time'] >= booking['appointment_time'] and 
                            request['appointment_time'] < booking['appointment_time'] + 
                            timedelta(minutes=booking['duration_minutes'])):
                            slot_available = False
                            break
                    
                    if slot_available:
                        # Create the booking
                        booking_data = {
                            'email': from_email,
                            'name': from_name,
                            'employee_id': schedule['id'],
                            'appointment_time': request['appointment_time'],
                            'employee_name': schedule['employee_name']
                        }
                        booking = self.booking_repository.create_booking(booking_data)
                        return self.response_handler.handle_booking_request(booking)
            
            return "I'm sorry, but the requested time slot is not available. Please check the available slots and try again."
            
        return self.response_handler.handle_unknown_request() 