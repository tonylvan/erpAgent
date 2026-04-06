"""
Initialize database with sample alert data
"""
import sys
sys.path.insert(0, 'D:\\erpAgent\\backend')

from app.db.database import engine, SessionLocal
from app.models.alert import Alert, AlertLevel, AlertStatus
from datetime import datetime

def create_sample_data():
    """Create sample alert data"""
    print("Creating database tables and sample data...")
    
    # Create tables
    from app.db.database import Base
    Base.metadata.create_all(bind=engine)
    print("Database tables created!")
    
    # Create session
    db = SessionLocal()
    
    try:
        # Check if data already exists
        existing = db.query(Alert).count()
        if existing > 0:
            print(f"Database already has {existing} alerts. Skipping sample data.")
            return
        
        # Sample alerts
        sample_alert = Alert(
            title="Critical sales anomaly detected",
            level=AlertLevel.CRITICAL,
            status=AlertStatus.UNREAD,
            business_module="Sales",
            description="Sales dropped 45% compared to last week"
        )
        
        db.add(sample_alert)
        db.commit()
        
        print("Sample data created successfully!")
        print(f"Total alerts in database: {db.query(Alert).count()}")
        
    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_sample_data()
