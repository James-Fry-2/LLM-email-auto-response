from datetime import datetime
from typing import List, Dict
from src.core.interfaces import ResponseHandler

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