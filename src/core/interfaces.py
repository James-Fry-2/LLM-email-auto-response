from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Optional

class ScheduleRepository(ABC):
    @abstractmethod
    def get_employee_schedule(self, employee_id: int, day_of_week: int) -> Optional[Dict]:
        pass

    @abstractmethod
    def get_all_schedules_for_day(self, day_of_week: int) -> List[Dict]:
        pass

class BookingRepository(ABC):
    @abstractmethod
    def create_booking(self, booking_data: Dict) -> Dict:
        pass

    @abstractmethod
    def get_bookings_for_employee(self, employee_id: int, date: datetime) -> List[Dict]:
        pass

class EmailParser(ABC):
    @abstractmethod
    def parse_availability_request(self, email_body: str) -> Optional[Dict]:
        pass

    @abstractmethod
    def parse_booking_request(self, email_body: str) -> Optional[Dict]:
        pass

class AvailabilityService(ABC):
    @abstractmethod
    def get_available_slots(self, date: datetime, employee_id: Optional[int] = None) -> List[Dict]:
        pass

class ResponseHandler(ABC):
    @abstractmethod
    def handle_availability_request(self, date: datetime, available_slots: List[Dict]) -> str:
        pass

    @abstractmethod
    def handle_booking_request(self, booking_data: Dict) -> str:
        pass

    @abstractmethod
    def handle_unknown_request(self) -> str:
        pass 