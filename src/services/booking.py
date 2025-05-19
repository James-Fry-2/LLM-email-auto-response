from datetime import datetime
from typing import Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy import text
from src.core.models import Booking, Service, EmployeeSchedule
from availability import AvailabilityService
import time
import random

class BookingService:
    def __init__(self, session: Session):
        self.session = session
        self.availability_service = AvailabilityService(session)
        self.max_retries = 3
        self.retry_delay = 0.1  # seconds

    def _acquire_lock(self, employee_id: int, appointment_time: datetime) -> bool:
        """Try to acquire a lock for the time slot"""
        try:
            # Use advisory lock for PostgreSQL
            if 'postgresql' in str(self.session.get_bind().url):
                lock_id = hash(f"{employee_id}_{appointment_time.isoformat()}")
                result = self.session.execute(
                    text("SELECT pg_try_advisory_xact_lock(:lock_id)"),
                    {"lock_id": lock_id}
                ).scalar()
                return result
            return True
        except Exception:
            return False

    def _wait_for_lock(self, employee_id: int, appointment_time: datetime) -> bool:
        """Wait for lock with exponential backoff"""
        for attempt in range(self.max_retries):
            if self._acquire_lock(employee_id, appointment_time):
                return True
            # Exponential backoff with jitter
            delay = (self.retry_delay * (2 ** attempt)) + (random.random() * 0.1)
            time.sleep(delay)
        return False

    def create_booking(
        self,
        customer_id: int,
        employee_id: int,
        service_id: int,
        appointment_time: datetime,
        notes: Optional[str] = None
    ) -> Dict:
        """
        Create a new booking with transaction handling, validation, and lock management.
        Returns the created booking or raises an exception if validation fails.
        """
        if not self._wait_for_lock(employee_id, appointment_time):
            raise ValueError("Could not acquire lock for the time slot")

        try:
            # Start transaction
            self.session.begin_nested()

            # Validate service exists and is active
            service = self.session.query(Service).get(service_id)
            if not service or not service.is_active:
                raise ValueError("Invalid or inactive service")

            # Validate employee schedule
            schedule = self.session.query(EmployeeSchedule).filter(
                EmployeeSchedule.employee_id == employee_id,
                EmployeeSchedule.day_of_week == appointment_time.weekday(),
                EmployeeSchedule.start_date <= appointment_time.date(),
                EmployeeSchedule.end_date >= appointment_time.date()
            ).first()

            if not schedule:
                raise ValueError("No valid schedule found for the specified time")

            # Check if the time slot is still available
            available_slots = self.availability_service.get_available_slots(
                appointment_time,
                service_id,
                employee_id
            )

            slot_available = False
            for slot in available_slots:
                if (slot['start_time'] <= appointment_time and 
                    slot['end_time'] >= appointment_time + service.duration_minutes):
                    slot_available = True
                    break

            if not slot_available:
                raise ValueError("Requested time slot is no longer available")

            # Create the booking
            booking = Booking(
                customer_id=customer_id,
                employee_id=employee_id,
                service_id=service_id,
                schedule_id=schedule.id,
                appointment_time=appointment_time,
                status='confirmed',
                notes=notes
            )

            self.session.add(booking)
            self.session.flush()  # Flush to get the booking ID

            # Clear availability cache for this date
            self.availability_service.clear_cache()

            # Commit the transaction
            self.session.commit()

            return {
                'id': booking.id,
                'customer_id': booking.customer_id,
                'employee_id': booking.employee_id,
                'service_id': booking.service_id,
                'appointment_time': booking.appointment_time,
                'status': booking.status,
                'notes': booking.notes
            }

        except IntegrityError as e:
            self.session.rollback()
            raise ValueError(f"Database integrity error: {str(e)}")
        except OperationalError as e:
            self.session.rollback()
            raise ValueError(f"Database operation error: {str(e)}")
        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Error creating booking: {str(e)}")

    def update_booking_status(self, booking_id: int, status: str) -> Dict:
        """
        Update booking status with transaction handling and lock management.
        Returns the updated booking or raises an exception if update fails.
        """
        try:
            # Start transaction
            self.session.begin_nested()

            booking = self.session.query(Booking).get(booking_id)
            if not booking:
                raise ValueError("Booking not found")

            # Acquire lock for the booking
            if not self._wait_for_lock(booking.employee_id, booking.appointment_time):
                raise ValueError("Could not acquire lock for the booking")

            booking.status = status
            self.session.flush()

            # Clear availability cache for this date
            self.availability_service.clear_cache()

            # Commit the transaction
            self.session.commit()

            return {
                'id': booking.id,
                'status': booking.status,
                'appointment_time': booking.appointment_time
            }

        except Exception as e:
            self.session.rollback()
            raise ValueError(f"Error updating booking status: {str(e)}")

    def cancel_booking(self, booking_id: int) -> Dict:
        """
        Cancel a booking with transaction handling and lock management.
        Returns the cancelled booking or raises an exception if cancellation fails.
        """
        return self.update_booking_status(booking_id, 'cancelled') 