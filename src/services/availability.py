from datetime import datetime, timedelta, time
from typing import List, Dict, Optional
from functools import lru_cache
from sqlalchemy.orm import Session
from src.core.models import EmployeeSchedule, Booking, Service
from src.infrastructure.repositories import SQLAlchemyScheduleRepository, SQLAlchemyBookingRepository

class AvailabilityService:
    def __init__(self, session: Session):
        self.session = session
        self.schedule_repo = SQLAlchemyScheduleRepository(session)
        self.booking_repo = SQLAlchemyBookingRepository(session)
        self._cache = {}
        self._cache_ttl = timedelta(minutes=5)  # Cache time-to-live

    def _get_cache_key(self, date: datetime, employee_id: Optional[int] = None) -> str:
        """Generate a cache key for availability checks"""
        # Handle both datetime and date objects
        date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
        return f"{date_str}_{employee_id if employee_id else 'all'}"

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached data is still valid"""
        if cache_key not in self._cache:
            return False
        cache_time, _ = self._cache[cache_key]
        return datetime.now() - cache_time < self._cache_ttl

    def _update_cache(self, cache_key: str, data: List[Dict]):
        """Update the cache with new data"""
        self._cache[cache_key] = (datetime.now(), data)

    def _get_cached_availability(self, cache_key: str) -> Optional[List[Dict]]:
        """Get availability data from cache if valid"""
        if self._is_cache_valid(cache_key):
            return self._cache[cache_key][1]
        return None

    @lru_cache(maxsize=100)
    def _get_employee_schedule(self, employee_id: int, date: datetime) -> List[Dict]:
        """Get employee schedule with caching"""
        return self.schedule_repo.get_employee_schedule(employee_id, date.weekday())

    @lru_cache(maxsize=100)
    def _get_bookings_for_date(self, date: datetime, employee_id: Optional[int] = None) -> List[Dict]:
        """Get bookings for a date with caching"""
        return self.booking_repo.get_bookings_for_employee(employee_id, date) if employee_id else []

    def _find_available_slots(
        self,
        schedule: Dict,
        existing_bookings: List[Dict],
        service_duration: int,
        date: datetime
    ) -> List[Dict]:
        """Find available time slots within a schedule"""
        available_slots = []
        start_time = datetime.combine(date.date(), schedule['start_time'])
        end_time = datetime.combine(date.date(), schedule['end_time'])
        
        # Convert existing bookings to time ranges
        booked_ranges = []
        for booking in existing_bookings:
            booking_time = booking['appointment_time']
            service = self.session.get(Service, booking['service_id'])
            if service:
                booking_end = booking_time + timedelta(minutes=service.duration_minutes)
                booked_ranges.append((booking_time, booking_end))

        # Find available slots
        current_time = start_time
        while current_time + timedelta(minutes=service_duration) <= end_time:
            slot_available = True
            slot_end = current_time + timedelta(minutes=service_duration)
            
            # Check if slot overlaps with any existing booking
            for booking_start, booking_end in booked_ranges:
                if (current_time < booking_end and slot_end > booking_start):
                    slot_available = False
                    break
            
            if slot_available:
                available_slots.append({
                    'start_time': current_time,
                    'end_time': slot_end,
                    'duration_minutes': service_duration
                })
            
            # Move to next 15-minute slot
            current_time += timedelta(minutes=15)
        
        return available_slots

    def get_available_slots(
        self,
        date: datetime,
        service_id: int,
        employee_id: Optional[int] = None
    ) -> List[Dict]:
        """Get available time slots for a specific date and service"""
        cache_key = self._get_cache_key(date, employee_id)
        
        # Check cache first
        cached_slots = self._get_cached_availability(cache_key)
        if cached_slots is not None:
            return cached_slots

        # Get service duration
        service = self.session.get(Service, service_id)
        if not service:
            return []
        
        # Get employee schedules
        if employee_id:
            schedules = [self._get_employee_schedule(employee_id, date)]
        else:
            schedules = self.schedule_repo.get_all_schedules_for_day(date.weekday())

        # Get existing bookings
        existing_bookings = self._get_bookings_for_date(date, employee_id)

        # Find available slots
        available_slots = []
        for schedule in schedules:
            slots = self._find_available_slots(
                schedule,
                existing_bookings,
                service.duration_minutes,
                date
            )
            available_slots.extend(slots)

        # Sort slots by start time
        available_slots.sort(key=lambda x: x['start_time'])

        # Update cache
        self._update_cache(cache_key, available_slots)

        return available_slots

    def clear_cache(self):
        """Clear the availability cache"""
        self._cache.clear()
        self._get_employee_schedule.cache_clear()
        self._get_bookings_for_date.cache_clear() 