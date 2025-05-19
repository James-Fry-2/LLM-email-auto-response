from sqlalchemy.orm import Session
from src.core.models import Customer, Employee, Service, Booking, EmployeeSchedule
from datetime import datetime, date

class DBHandler:
    def __init__(self, session: Session):
        self.session = session

    def get_customer_info(self, email: str) -> tuple:
        """Get customer information by email"""
        customer = self.session.query(Customer).filter_by(email=email).first()
        if customer:
            return (
                f"{customer.first_name} {customer.last_name}",
                f"Phone: {customer.phone}, Address: {customer.address}, Notes: {customer.notes}"
            )
        return None

    def add_customer(self, email: str, first_name: str, last_name: str, phone: str = None, address: str = None, notes: str = None) -> Customer:
        """Add a new customer"""
        customer = Customer(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            address=address,
            notes=notes
        )
        self.session.add(customer)
        self.session.commit()
        return customer

    def get_employee_schedule(self, employee_id: int, date: date) -> list:
        """Get employee schedule for a specific date"""
        day_of_week = date.weekday()
        return self.session.query(EmployeeSchedule).filter(
            EmployeeSchedule.employee_id == employee_id,
            EmployeeSchedule.day_of_week == day_of_week,
            EmployeeSchedule.start_date <= date,
            EmployeeSchedule.end_date >= date
        ).all()

    def get_available_services(self, employee_id: int) -> list:
        """Get services available for a specific employee"""
        employee = self.session.query(Employee).get(employee_id)
        if employee:
            return [es.service for es in employee.services]
        return []

    def create_booking(self, customer_email: str, employee_id: int, service_id: int, appointment_time: datetime) -> Booking:
        """Create a new booking"""
        customer = self.session.query(Customer).filter_by(email=customer_email).first()
        if not customer:
            raise ValueError(f"Customer with email {customer_email} not found")

        # Get the schedule for the appointment date
        schedule = self.session.query(EmployeeSchedule).filter(
            EmployeeSchedule.employee_id == employee_id,
            EmployeeSchedule.day_of_week == appointment_time.weekday(),
            EmployeeSchedule.start_date <= appointment_time.date(),
            EmployeeSchedule.end_date >= appointment_time.date()
        ).first()

        if not schedule:
            raise ValueError("No schedule found for the specified time")

        booking = Booking(
            customer_id=customer.id,
            employee_id=employee_id,
            service_id=service_id,
            schedule_id=schedule.id,
            appointment_time=appointment_time,
            status='confirmed'
        )
        self.session.add(booking)
        self.session.commit()
        return booking

    def get_customer_bookings(self, email: str) -> list:
        """Get all bookings for a customer"""
        customer = self.session.query(Customer).filter_by(email=email).first()
        if customer:
            return self.session.query(Booking).filter_by(customer_id=customer.id).all()
        return []

    def update_booking_status(self, booking_id: int, status: str) -> Booking:
        """Update booking status"""
        booking = self.session.query(Booking).get(booking_id)
        if booking:
            booking.status = status
            self.session.commit()
        return booking 