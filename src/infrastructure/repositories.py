from datetime import datetime
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from src.core.models import EmployeeSchedule, Booking
from src.core.interfaces import ScheduleRepository, BookingRepository

class SQLAlchemyScheduleRepository(ScheduleRepository):
    def __init__(self, session: Session):
        self.session = session

    def get_employee_schedule(self, employee_id: int, day_of_week: int) -> Optional[Dict]:
        schedule = self.session.query(EmployeeSchedule).filter(
            EmployeeSchedule.employee_id == employee_id,
            EmployeeSchedule.day_of_week == day_of_week
        ).first()
        
        if schedule:
            return {
                'id': schedule.id,
                'employee_id': schedule.employee_id,
                'employee_name': schedule.employee_name,
                'start_time': schedule.start_time,
                'end_time': schedule.end_time
            }
        return None

    def get_all_schedules_for_day(self, day_of_week: int) -> List[Dict]:
        schedules = self.session.query(EmployeeSchedule).filter(
            EmployeeSchedule.day_of_week == day_of_week
        ).all()
        
        return [{
            'id': schedule.id,
            'employee_id': schedule.employee_id,
            'employee_name': schedule.employee_name,
            'start_time': schedule.start_time,
            'end_time': schedule.end_time
        } for schedule in schedules]

class SQLAlchemyBookingRepository(BookingRepository):
    def __init__(self, session: Session):
        self.session = session

    def create_booking(self, booking_data: Dict) -> Dict:
        booking = Booking(
            email=booking_data['email'],
            name=booking_data['name'],
            employee_id=booking_data['employee_id'],
            appointment_time=booking_data['appointment_time'],
            duration_minutes=booking_data.get('duration_minutes', 30)
        )
        self.session.add(booking)
        self.session.commit()
        
        return {
            'id': booking.id,
            'email': booking.email,
            'name': booking.name,
            'employee_id': booking.employee_id,
            'appointment_time': booking.appointment_time,
            'duration_minutes': booking.duration_minutes,
            'status': booking.status
        }

    def get_bookings_for_employee(self, employee_id: int, date: datetime) -> List[Dict]:
        start_of_day = datetime.combine(date, datetime.min.time())
        end_of_day = datetime.combine(date, datetime.max.time())
        
        bookings = self.session.query(Booking).filter(
            Booking.employee_id == employee_id,
            Booking.appointment_time >= start_of_day,
            Booking.appointment_time <= end_of_day,
            Booking.status == 'confirmed'
        ).all()
        
        return [{
            'id': booking.id,
            'appointment_time': booking.appointment_time,
            'duration_minutes': booking.duration_minutes
        } for booking in bookings] 