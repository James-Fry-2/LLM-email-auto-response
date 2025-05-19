from sqlalchemy import Column, Integer, String, DateTime, Time, ForeignKey, Date, Text, Boolean, Numeric, Index
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime, timezone

Base = declarative_base()

class Employee(Base):
    __tablename__ = 'employees'
    
    id = Column(Integer, primary_key=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(100), unique=True, nullable=False, index=True)
    phone = Column(String(20))
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    schedules = relationship("EmployeeSchedule", back_populates="employee")
    services = relationship("EmployeeService", back_populates="employee")

    # Indexes
    __table_args__ = (
        Index('idx_employee_name', 'first_name', 'last_name'),
        Index('idx_employee_active', 'is_active', 'email'),
    )

class Service(Base):
    __tablename__ = 'services'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    duration_minutes = Column(Integer, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    employee_services = relationship("EmployeeService", back_populates="service")
    bookings = relationship("Booking", back_populates="service")

    # Indexes
    __table_args__ = (
        Index('idx_service_active', 'is_active', 'name'),
    )

class EmployeeService(Base):
    __tablename__ = 'employee_services'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey('services.id'), nullable=False, index=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    employee = relationship("Employee", back_populates="services")
    service = relationship("Service", back_populates="employee_services")

    # Indexes
    __table_args__ = (
        Index('idx_employee_service', 'employee_id', 'service_id', unique=True),
    )

class Customer(Base):
    __tablename__ = 'customers'
    
    id = Column(Integer, primary_key=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    phone = Column(String(20))
    address = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    bookings = relationship("Booking", back_populates="customer")

    # Indexes
    __table_args__ = (
        Index('idx_customer_name', 'first_name', 'last_name'),
        Index('idx_customer_email', 'email'),
    )

class EmployeeSchedule(Base):
    __tablename__ = 'employee_schedules'
    
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False, index=True)
    day_of_week = Column(Integer, nullable=False, index=True)  # 0-6 for Monday-Sunday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    start_date = Column(Date, nullable=False, index=True)  # For temporary schedule changes
    end_date = Column(Date, nullable=False, index=True)    # For temporary schedule changes
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    employee = relationship("Employee", back_populates="schedules")
    bookings = relationship("Booking", back_populates="schedule")

    # Indexes
    __table_args__ = (
        Index('idx_schedule_employee_date', 'employee_id', 'day_of_week', 'start_date', 'end_date'),
        Index('idx_schedule_dates', 'start_date', 'end_date'),
    )

class Booking(Base):
    __tablename__ = 'bookings'
    
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id'), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey('employees.id'), nullable=False, index=True)
    service_id = Column(Integer, ForeignKey('services.id'), nullable=False, index=True)
    schedule_id = Column(Integer, ForeignKey('employee_schedules.id'), nullable=False, index=True)
    appointment_time = Column(DateTime, nullable=False, index=True)
    status = Column(String(20), default='confirmed', index=True)  # confirmed, cancelled, completed
    notes = Column(Text)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
    
    # Relationships
    customer = relationship("Customer", back_populates="bookings")
    employee = relationship("Employee")
    service = relationship("Service", back_populates="bookings")
    schedule = relationship("EmployeeSchedule", back_populates="bookings")

    # Indexes
    __table_args__ = (
        Index('idx_booking_appointment', 'appointment_time', 'status'),
        Index('idx_booking_employee_date', 'employee_id', 'appointment_time'),
        Index('idx_booking_customer', 'customer_id', 'appointment_time'),
    ) 