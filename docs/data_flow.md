# System Data Flow and Schema

## Database Schema

```mermaid
erDiagram
    CUSTOMERS {
        string email PK
        string name
        string info
    }
    
    EMPLOYEE_SCHEDULES {
        int id PK
        int employee_id
        string employee_name
        int day_of_week
        time start_time
        time end_time
        datetime created_at
    }
    
    BOOKINGS {
        int id PK
        string email
        string name
        int employee_id FK
        datetime appointment_time
        int duration_minutes
        string status
        datetime created_at
    }

    EMPLOYEE_SCHEDULES ||--o{ BOOKINGS : "has"
```

## Data Flow Diagram

```mermaid
graph TD
    subgraph "Email Input"
        A[Incoming Email] --> B[Email Handler]
        B --> C[Email Parser]
    end

    subgraph "Processing"
        C -->|Availability Request| D[Availability Service]
        C -->|Booking Request| E[Booking Service]
        
        D --> F[Schedule Repository]
        D --> G[Booking Repository]
        
        E --> F
        E --> G
    end

    subgraph "Database"
        F --> H[(Employee Schedules)]
        G --> I[(Bookings)]
        G --> J[(Customers)]
    end

    subgraph "Response"
        D --> K[Response Handler]
        E --> K
        K --> L[Outgoing Email]
    end

    style A fill:#f9f,stroke:#333,stroke-width:2px
    style L fill:#f9f,stroke:#333,stroke-width:2px
    style H fill:#bbf,stroke:#333,stroke-width:2px
    style I fill:#bbf,stroke:#333,stroke-width:2px
    style J fill:#bbf,stroke:#333,stroke-width:2px
```

## Process Flow Description

1. **Email Input**
   - System receives incoming emails
   - Email Handler processes the raw email
   - Email Parser extracts intent and data

2. **Processing**
   - For Availability Requests:
     - Checks employee schedules
     - Checks existing bookings
     - Generates available time slots
   
   - For Booking Requests:
     - Validates requested time slot
     - Checks employee availability
     - Creates new booking
     - Updates customer information

3. **Database**
   - Employee Schedules: Stores working hours for each employee
   - Bookings: Records all appointments
   - Customers: Maintains customer information

4. **Response**
   - Generates appropriate email response
   - Includes booking confirmation or availability information
   - Sends response back to customer

## Key Components

- **Email Handler**: Manages email communication
- **Email Parser**: Extracts booking/availability requests
- **Availability Service**: Manages time slot availability
- **Booking Service**: Handles appointment creation
- **Response Handler**: Generates email responses
- **Repositories**: Interface with database tables 