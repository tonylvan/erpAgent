"""
Database migration script to add closed_at and closed_by columns to tickets table
"""
from sqlalchemy import create_engine, text
from app.db.database import DATABASE_URL

def migrate():
    """Add new columns to tickets table"""
    engine = create_engine(DATABASE_URL)
    conn = engine.connect()
    
    # Add closed_at column
    conn.execute(text('ALTER TABLE tickets ADD COLUMN IF NOT EXISTS closed_at TIMESTAMP'))
    
    # Add closed_by column
    conn.execute(text('ALTER TABLE tickets ADD COLUMN IF NOT EXISTS closed_by VARCHAR(100)'))
    
    conn.commit()
    conn.close()
    
    print('Database migration completed successfully')
    print('Added columns: closed_at (TIMESTAMP), closed_by (VARCHAR(100))')

if __name__ == '__main__':
    migrate()
