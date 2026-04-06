"""
Initialize database tables for GSD Alert system
Run this script once to create tables
"""
import sys
sys.path.insert(0, 'D:\\erpAgent\\backend')

from app.db.database import engine, Base
from app.models.alert import Alert

def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database tables created successfully!")
    
    # Verify tables
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Tables created: {tables}")

if __name__ == "__main__":
    create_tables()
