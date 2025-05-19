from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from src.core.models import Base
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta
import schedule
import time
import threading

load_dotenv()

def init_db():
    """Initialize the database connection and create tables"""
    database_url = os.getenv('DATABASE_URL', 'sqlite:///appointments.db')
    engine = create_engine(database_url)
    
    # Create tables
    Base.metadata.create_all(engine)
    
    # Set up partitioning for bookings if using PostgreSQL
    if 'postgresql' in database_url:
        with engine.connect() as conn:
            # Create partitioned table for historical bookings
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS historical_bookings (
                    LIKE bookings INCLUDING ALL
                ) INHERITS (bookings);
            """))
            
            # Create indexes on the partitioned table
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_historical_booking_appointment 
                ON historical_bookings (appointment_time);
                
                CREATE INDEX IF NOT EXISTS idx_historical_booking_status 
                ON historical_bookings (status);
            """))
            
            # Create function to move old bookings to historical table
            conn.execute(text("""
                CREATE OR REPLACE FUNCTION move_old_bookings()
                RETURNS void AS $$
                BEGIN
                    -- Use a transaction to ensure atomicity
                    BEGIN
                        -- Move old bookings to historical table
                        INSERT INTO historical_bookings 
                        SELECT * FROM bookings 
                        WHERE appointment_time < NOW() - INTERVAL '3 months'
                        AND status IN ('completed', 'cancelled');
                        
                        -- Delete moved bookings from main table
                        DELETE FROM bookings 
                        WHERE appointment_time < NOW() - INTERVAL '3 months'
                        AND status IN ('completed', 'cancelled');
                        
                        -- Log the operation
                        INSERT INTO archive_log (operation_date, records_moved)
                        SELECT NOW(), COUNT(*)
                        FROM historical_bookings
                        WHERE created_at >= NOW() - INTERVAL '1 day';
                    EXCEPTION
                        WHEN OTHERS THEN
                            -- Log the error
                            INSERT INTO archive_log (operation_date, error_message)
                            VALUES (NOW(), SQLERRM);
                            RAISE;
                    END;
                END;
                $$ LANGUAGE plpgsql;
            """))
            
            # Create archive log table
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS archive_log (
                    id SERIAL PRIMARY KEY,
                    operation_date TIMESTAMP NOT NULL,
                    records_moved INTEGER,
                    error_message TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_archive_log_date 
                ON archive_log (operation_date);
            """))
    
    return engine

def get_session():
    """Get a new database session"""
    engine = init_db()
    Session = sessionmaker(bind=engine)
    return Session()

def archive_old_bookings(session):
    """Manually trigger archiving of old bookings"""
    if 'postgresql' in os.getenv('DATABASE_URL', ''):
        session.execute(text("SELECT move_old_bookings();"))
        session.commit()

def start_archive_scheduler():
    """Start the background scheduler for archiving old bookings"""
    def run_scheduler():
        schedule.every().day.at("02:00").do(lambda: archive_old_bookings(get_session()))
        
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every minute
    
    # Start scheduler in a background thread
    scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
    scheduler_thread.start()
    return scheduler_thread 