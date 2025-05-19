from src.infrastructure.database import get_session
from src.core.models import Employee, Service, Customer, Booking, EmployeeSchedule
from tabulate import tabulate
from sqlalchemy import text
import argparse

def view_table_data(session, model, title):
    """View data from a table in a formatted way"""
    data = session.query(model).all()
    if not data:
        print(f"\nNo data in {title}")
        return
    
    # Get column names from the first row
    columns = data[0].__table__.columns.keys()
    
    # Convert rows to list of lists
    rows = []
    for row in data:
        row_data = []
        for col in columns:
            value = getattr(row, col)
            # Format datetime objects
            if hasattr(value, 'strftime'):
                value = value.strftime('%Y-%m-%d %H:%M:%S')
            row_data.append(value)
        rows.append(row_data)
    
    print(f"\n{title}:")
    print(tabulate(rows, headers=columns, tablefmt='grid'))

def execute_sql_query(session, query):
    """Execute a raw SQL query and display results"""
    try:
        result = session.execute(text(query))
        if result.returns_rows:
            # Get column names
            columns = result.keys()
            # Get all rows
            rows = [list(row) for row in result]
            
            print("\nQuery Results:")
            print(tabulate(rows, headers=columns, tablefmt='grid'))
        else:
            print("\nQuery executed successfully (no rows returned)")
    except Exception as e:
        print(f"\nError executing query: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description='View database data or execute SQL queries')
    parser.add_argument('--query', '-q', help='SQL query to execute')
    parser.add_argument('--all', '-a', action='store_true', help='Show all tables')
    args = parser.parse_args()

    session = get_session()
    try:
        if args.query:
            execute_sql_query(session, args.query)
        elif args.all:
            # View data from each table
            view_table_data(session, Employee, "Employees")
            view_table_data(session, Service, "Services")
            view_table_data(session, Customer, "Customers")
            view_table_data(session, EmployeeSchedule, "Employee Schedules")
            view_table_data(session, Booking, "Bookings")
        else:
            print("Please provide either --query or --all argument")
            print("Example: python view_data.py --query 'SELECT * FROM employees'")
            print("Example: python view_data.py --all")
    finally:
        session.close()

if __name__ == "__main__":
    main() 