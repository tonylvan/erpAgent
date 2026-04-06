"""
Test PostgreSQL connection after password reset
"""
import sys
import os

sys.path.insert(0, 'D:\\erpAgent\\backend')

from sqlalchemy import create_engine, text

# Database credentials
DB_USER = "postgres"
DB_PASSWORD = "Tony1985"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "postgres"  # Connect to default database first

# Create database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

print(f"Testing connection to: postgresql://{DB_USER}:***@{DB_HOST}:{DB_PORT}/{DB_NAME}")
print("=" * 60)

try:
    # Create engine
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1 as test"))
        row = result.fetchone()
        print(f"[OK] Test query result: {row.test}")
        print("[OK] Password 'Tony1985' is CORRECT!")
        
        # Check if erpagent database exists
        result = conn.execute(text("""
            SELECT datname FROM pg_database WHERE datname = 'erpagent'
        """))
        databases = [row[0] for row in result.fetchall()]
        
        if 'erpagent' in databases:
            print(f"[OK] Database 'erpagent': EXISTS")
        else:
            print(f"[WARN] Database 'erpagent': NOT FOUND")
            print("Creating database 'erpagent'...")
            conn.execute(text("COMMIT"))
            conn.execute(text("CREATE DATABASE erpagent"))
            print("[OK] Database 'erpagent' created!")
    
    print("=" * 60)
    print("[SUCCESS] Database connection test completed!")
    
except Exception as e:
    print("=" * 60)
    print(f"[ERROR] Connection failed: {e}")
    print("\nPossible causes:")
    print("1. PostgreSQL service not running")
    print("2. Password is still incorrect")
    print("3. Network connection issue")
