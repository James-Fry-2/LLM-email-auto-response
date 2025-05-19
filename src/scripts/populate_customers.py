from datetime import datetime, time, date, timedelta
from src.infrastructure.database import init_db, get_session
from src.core.models import Employee, Service, EmployeeService, Customer, EmployeeSchedule, Booking

def populate_employees(session):
    employees = [
        Employee(
            first_name='John',
            last_name='Doe',
            email='john.doe@example.com',
            phone='555-0101',
            is_active=True
        ),
        Employee(
            first_name='Jane',
            last_name='Smith',
            email='jane.smith@example.com',
            phone='555-0102',
            is_active=True
        ),
        Employee(
            first_name='Mike',
            last_name='Johnson',
            email='mike.johnson@example.com',
            phone='555-0103',
            is_active=True
        )
    ]
    session.add_all(employees)
    session.commit()
    print('Sample employees added.')

def populate_services(session):
    services = [
        Service(
            name='Haircut',
            description='Standard haircut service',
            duration_minutes=30,
            price=35.00,
            is_active=True
        ),
        Service(
            name='Hair Coloring',
            description='Full hair coloring service',
            duration_minutes=120,
            price=85.00,
            is_active=True
        ),
        Service(
            name='Manicure',
            description='Basic manicure service',
            duration_minutes=45,
            price=25.00,
            is_active=True
        )
    ]
    session.add_all(services)
    session.commit()
    print('Sample services added.')

def populate_employee_services(session):
    # Get all employees and services
    employees = session.query(Employee).all()
    services = session.query(Service).all()
    
    # Assign all services to all employees
    employee_services = []
    for employee in employees:
        for service in services:
            employee_services.append(
                EmployeeService(
                    employee_id=employee.id,
                    service_id=service.id
                )
            )
    
    session.add_all(employee_services)
    session.commit()
    print('Employee services assigned.')

def populate_customers(session):
    customers = [
        Customer(
            email='alice@example.com',
            first_name='Alice',
            last_name='Smith',
            phone='555-0201',
            address='123 Main St, City, State',
            notes='VIP customer, prefers email contact.'
        ),
        Customer(
            email='bob@example.com',
            first_name='Bob',
            last_name='Johnson',
            phone='555-0202',
            address='456 Oak Ave, City, State',
            notes='Has a pending support ticket.'
        ),
        Customer(
            email='carol@example.com',
            first_name='Carol',
            last_name='Lee',
            phone='555-0203',
            address='789 Pine Rd, City, State',
            notes='Interested in product updates.'
        )
    ]
    session.add_all(customers)
    session.commit()
    print('Sample customers added.')

def populate_employee_schedules(session):
    # Get all employees
    employees = session.query(Employee).all()
    
    # Create schedules for the next 30 days
    today = date.today()
    end_date = today + timedelta(days=30)  # Use timedelta instead of direct day addition
    schedules = []
    
    for employee in employees:
        # Create regular weekly schedule
        for day in range(7):  # Monday to Sunday
            if day < 5:  # Monday to Friday
                schedules.append(
                    EmployeeSchedule(
                        employee_id=employee.id,
                        day_of_week=day,
                        start_time=time(9, 0),
                        end_time=time(17, 0),
                        start_date=today,
                        end_date=end_date
                    )
                )
    
    session.add_all(schedules)
    session.commit()
    print('Employee schedules added.')

def populate_bookings(session):
    # Get today's date
    today = datetime.now().date()
    
    # Get sample data
    customer = session.query(Customer).filter_by(email='alice@example.com').first()
    employee = session.query(Employee).filter_by(email='john.doe@example.com').first()
    service = session.query(Service).filter_by(name='Haircut').first()
    schedule = session.query(EmployeeSchedule).filter_by(employee_id=employee.id).first()
    
    # Create sample bookings
    bookings = [
        Booking(
            customer_id=customer.id,
            employee_id=employee.id,
            service_id=service.id,
            schedule_id=schedule.id,
            appointment_time=datetime.combine(today, time(10, 0)),
            status='confirmed',
            notes='Regular monthly haircut'
        )
    ]
    
    session.add_all(bookings)
    session.commit()
    print('Sample bookings added.')

def main():
    # Initialize database
    init_db()
    session = get_session()
    
    try:
        # Populate all tables
        populate_employees(session)
        populate_services(session)
        populate_employee_services(session)
        populate_customers(session)
        populate_employee_schedules(session)
        populate_bookings(session)
        print('All test data has been populated successfully!')
    except Exception as e:
        print(f'Error populating test data: {str(e)}')
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    main() 