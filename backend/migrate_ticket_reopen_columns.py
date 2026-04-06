"""
Database migration script to add reopen columns to tickets table
"""
from sqlalchemy import create_engine, text
from app.db.database import DATABASE_URL

def migrate():
    """Add reopen columns to tickets table"""
    engine = create_engine(DATABASE_URL)
    conn = engine.connect()
    
    # Add reopen_reason column
    conn.execute(text('ALTER TABLE tickets ADD COLUMN IF NOT EXISTS reopen_reason TEXT'))
    
    # Add reopened_at column
    conn.execute(text('ALTER TABLE tickets ADD COLUMN IF NOT EXISTS reopened_at TIMESTAMP'))
    
    # Add reopened_by column
    conn.execute(text('ALTER TABLE tickets ADD COLUMN IF NOT EXISTS reopened_by VARCHAR(100)'))
    
    conn.commit()
    conn.close()
    
    print('Database migration completed successfully')
    print('Added columns: reopen_reason (TEXT), reopened_at (TIMESTAMP), reopened_by (VARCHAR(100))')

if __name__ == '__main__':
    migrate()
