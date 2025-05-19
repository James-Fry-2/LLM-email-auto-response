from datetime import datetime, timedelta
from typing import List, Dict, Optional
import re
from src.core.interfaces import AvailabilityService, EmailParser, ResponseHandler
from repositories import ScheduleRepository, BookingRepository

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
                    return {'type': 'booking', 'appointment_time': appointment_time}
                except ValueError:
                    pass
        return None

class AppointmentAvailabilityService(AvailabilityService):
    def __init__(self, schedule_repository: ScheduleRepository, booking_repository: BookingRepository):
        self.schedule_repository = schedule_repository
        self.booking_repository = booking_repository

    def get_available_slots(self, date: datetime, employee_id: Optional[int] = None) -> List[Dict]:
        day_of_week = date.weekday()
        
        if employee_id:
            schedules = [self.schedule_repository.get_employee_schedule(employee_id, day_of_week)]
            if not schedules[0]:
                return []
        else:
            schedules = self.schedule_repository.get_all_schedules_for_day(day_of_week)
        
        available_slots = []
        
        for schedule in schedules:
            bookings = self.booking_repository.get_bookings_for_employee(schedule['id'], date)
            
            current_time = datetime.combine(date, schedule['start_time'])
            end_time = datetime.combine(date, schedule['end_time'])
            
            while current_time < end_time:
                slot_available = True
                for booking in bookings:
                    if (current_time >= booking['appointment_time'] and 
                        current_time < booking['appointment_time'] + timedelta(minutes=booking['duration_minutes'])):
                        slot_available = False
                        break
                
                if slot_available:
                    available_slots.append({
                        'time': current_time,
                        'employee_id': schedule['employee_id'],
                        'employee_name': schedule['employee_name']
                    })
                current_time += timedelta(minutes=30)
            
        return available_slots

class EmailResponseHandler(ResponseHandler):
    def handle_availability_request(self, date: datetime, available_slots: List[Dict]) -> str:
        if not available_slots:
            return f"I'm sorry, but there are no available slots for {date.strftime('%Y-%m-%d')}."
        
        response = f"Here are the available slots for {date.strftime('%Y-%m-%d')}:\n\n"
        
        # Group slots by employee
        employee_slots = {}
        for slot in available_slots:
            emp_id = slot['employee_id']
            if emp_id not in employee_slots:
                employee_slots[emp_id] = {
                    'name': slot['employee_name'],
                    'slots': []
                }
            employee_slots[emp_id]['slots'].append(slot['time'])
        
        # Format response by employee
        for emp_id, data in employee_slots.items():
            response += f"With {data['name']}:\n"
            for slot in sorted(data['slots']):
                response += f"- {slot.strftime('%H:%M')}\n"
            response += "\n"
        
        response += "To book an appointment, please reply with your preferred time and include your name."
        return response

    def handle_booking_request(self, booking_data: Dict) -> str:
        return (
            f"Your appointment has been booked for {booking_data['appointment_time'].strftime('%Y-%m-%d %H:%M')} "
            f"with {booking_data['employee_name']}.\n\n"
            f"Booking details:\n"
            f"- Name: {booking_data['name']}\n"
            f"- Email: {booking_data['email']}\n"
            f"- Duration: {booking_data['duration_minutes']} minutes\n\n"
            f"If you need to make any changes, please reply to this email."
        )

    def handle_unknown_request(self) -> str:
        return (
            "I'm not sure how to help with that request. Please try one of the following:\n\n"
            "1. Check availability: 'What are the available slots for YYYY-MM-DD?'\n"
            "2. Book an appointment: 'I'd like to book an appointment for YYYY-MM-DD at HH:MM'\n\n"
            "Please make sure to include the date in YYYY-MM-DD format and time in HH:MM format."
        ) 