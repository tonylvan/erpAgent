"""
Initialize ticket database table
Run this script once to create the tickets table
"""
import sys
sys.path.insert(0, 'D:\\erpAgent\\backend')

from app.db.database import engine, Base
from app.models.ticket import Ticket

def create_tables():
    """Create tickets table"""
    print("Creating tickets table...")
    Base.metadata.create_all(bind=engine)
    print("SUCCESS: Tickets table created!")
    
    # Verify table
    from sqlalchemy import inspect
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    print(f"Tables: {tables}")

if __name__ == "__main__":
    create_tables()
