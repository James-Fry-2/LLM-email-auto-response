import os
import sys
import pytest
from pathlib import Path
from datetime import datetime
import uuid

# Add the project root directory to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.insert(0, project_root)

# Import after path setup
from src.infrastructure.database import get_session
from src.core.models import Customer, Service
from src.services.ai_responder import AIResponder
from src.api.email_handler import EmailHandler

@pytest.fixture(scope="session")
def db_session():
    """Database session fixture"""
    session = get_session()
    yield session
    session.close()

@pytest.fixture(autouse=True)
def cleanup_database(db_session):
    """Clean up the database before each test"""
    # Delete all customers and services
    db_session.query(Customer).delete()
    db_session.query(Service).delete()
    db_session.commit()
    yield
    # Clean up after the test
    db_session.query(Customer).delete()
    db_session.query(Service).delete()
    db_session.commit()

@pytest.fixture(scope="function")
def test_customer(db_session):
    """Test customer fixture"""
    # Generate a unique email using UUID
    unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    customer = Customer(
        email=unique_email,
        first_name='Test',
        last_name='User',
        phone='555-0123',
        address='123 Test St',
        notes='Test customer for AI response testing'
    )
    db_session.add(customer)
    db_session.commit()
    yield customer
    db_session.delete(customer)
    db_session.commit()

@pytest.fixture(scope="session")
def test_service(db_session):
    """Test service fixture"""
    service = Service(
        id=1,
        name="Test Service",
        duration_minutes=60,
        description="A test service for availability checks"
    )
    db_session.add(service)
    db_session.commit()
    yield service
    db_session.delete(service)
    db_session.commit()

@pytest.fixture(scope="session")
def email_handler():
    """Email handler fixture"""
    return EmailHandler()

@pytest.fixture(scope="session")
def ai_responder():
    """AI responder fixture"""
    return AIResponder() 