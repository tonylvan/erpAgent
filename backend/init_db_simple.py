"""
Initialize database tables for GSD Alert system
"""
import sys
sys.path.insert(0, 'D:\\erpAgent\\backend')

from app.db.database import engine, Base
from app.models.alert import Alert

def create_tables():
    """Create all database tables"""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("SUCCESS: Database tables created!")
    
    # Verify tables
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Tables: {tables}")

if __name__ == "__main__":
    create_tables()
