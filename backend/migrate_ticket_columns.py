"""
Database migration script to add solution and resolution_type columns to tickets table
"""
from sqlalchemy import create_engine, text
from app.db.database import DATABASE_URL

def migrate():
    """Add new columns to tickets table"""
    engine = create_engine(DATABASE_URL)
    conn = engine.connect()
    
    # Add solution column
    conn.execute(text('ALTER TABLE tickets ADD COLUMN IF NOT EXISTS solution TEXT'))
    
    # Add resolution_type column
    conn.execute(text('ALTER TABLE tickets ADD COLUMN IF NOT EXISTS resolution_type VARCHAR(50)'))
    
    conn.commit()
    conn.close()
    
    print('Database migration completed successfully')
    print('Added columns: solution (TEXT), resolution_type (VARCHAR(50))')

if __name__ == '__main__':
    migrate()
