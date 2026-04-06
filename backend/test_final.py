"""
Test PostgreSQL connection after password reset
"""
import sys
import os

# Set console encoding
os.system('chcp 65001 >nul')

sys.path.insert(0, 'D:\\erpAgent\\backend')

from sqlalchemy import create_engine, text

# Database credentials
DB_USER = "postgres"
DB_PASSWORD = "Tony1985"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "postgres"

# Create database URL
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

print("Testing PostgreSQL connection...")
print("=" * 60)

try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1 as test"))
        row = result.fetchone()
        print(f"[OK] Connection successful!")
        print(f"[OK] Test query: {row.test}")
        
        # Check erpagent database
        result = conn.execute(text("""
            SELECT datname FROM pg_database WHERE datname = 'erpagent'
        """))
        databases = [row[0] for row in result.fetchall()]
        
        if 'erpagent' in databases:
            print(f"[OK] Database 'erpagent': EXISTS")
        else:
            print(f"[INFO] Creating database 'erpagent'...")
            conn.execute(text("COMMIT"))
            conn.execute(text("CREATE DATABASE erpagent"))
            print(f"[OK] Database 'erpagent' created!")
    
    print("=" * 60)
    print("[SUCCESS] Password reset successful!")
    
except Exception as e:
    print("=" * 60)
    print(f"[ERROR] Connection failed: {e}")
