"""
Database migration script to add all missing columns to tickets table
"""
from sqlalchemy import create_engine, text
from app.db.database import DATABASE_URL

def migrate():
    """Add all missing columns to tickets table"""
    engine = create_engine(DATABASE_URL)
    conn = engine.connect()
    
    # Add closed_at column
    conn.execute(text('ALTER TABLE tickets ADD COLUMN IF NOT EXISTS closed_at TIMESTAMP'))
    
    # Add closed_by column
    conn.execute(text('ALTER TABLE tickets ADD COLUMN IF NOT EXISTS closed_by VARCHAR(100)'))
    
    # Add close_reason column
    conn.execute(text('ALTER TABLE tickets ADD COLUMN IF NOT EXISTS close_reason TEXT'))
    
    # Add satisfaction column
    conn.execute(text('ALTER TABLE tickets ADD COLUMN IF NOT EXISTS satisfaction VARCHAR(20)'))
    
    # Add reopen_reason column
    conn.execute(text('ALTER TABLE tickets ADD COLUMN IF NOT EXISTS reopen_reason TEXT'))
    
    # Add reopened_at column
    conn.execute(text('ALTER TABLE tickets ADD COLUMN IF NOT EXISTS reopened_at TIMESTAMP'))
    
    # Add reopened_by column
    conn.execute(text('ALTER TABLE tickets ADD COLUMN IF NOT EXISTS reopened_by VARCHAR(100)'))
    
    conn.commit()
    conn.close()
    
    print('Database migration completed successfully')
    print('Added columns:')
    print('  - closed_at (TIMESTAMP)')
    print('  - closed_by (VARCHAR(100))')
    print('  - close_reason (TEXT)')
    print('  - satisfaction (VARCHAR(20))')
    print('  - reopen_reason (TEXT)')
    print('  - reopened_at (TIMESTAMP)')
    print('  - reopened_by (VARCHAR(100))')

if __name__ == '__main__':
    migrate()
