"""
Test PostgreSQL database connection with URL encoding
"""
import sys
import os
sys.path.insert(0, 'D:\\erpAgent\\backend')

# Set console encoding to UTF-8
os.system('chcp 65001 >nul')

from urllib.parse import quote_plus
from sqlalchemy import create_engine, text

# Database credentials
DB_USER = "postgres"
DB_PASSWORD = quote_plus("Tony1985")
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "erpagent"

# Create database URL with encoded password
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

print(f"Database URL: postgresql://{DB_USER}:***@{DB_HOST}:{DB_PORT}/{DB_NAME}")
print("=" * 60)

try:
    # Create engine
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    
    # Test connection
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1 as test"))
        row = result.fetchone()
        print(f"[OK] Test query result: {row.test}")
        
        # Check if erpagent database exists
        result = conn.execute(text("""
            SELECT datname FROM pg_database WHERE datname = 'erpagent'
        """))
        databases = [row[0] for row in result.fetchall()]
        
        if 'erpagent' in databases:
            print(f"[OK] Database 'erpagent': EXISTS")
            
            # Check tables
            result = conn.execute(text("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public'
            """))
            table_count = result.fetchone()[0]
            print(f"[OK] Tables in database: {table_count}")
            
            # Check alerts table
            result = conn.execute(text("""
                SELECT EXISTS(SELECT 1 FROM information_schema.tables 
                WHERE table_name = 'alerts')
            """))
            has_alerts = result.fetchone()[0]
            status = "EXISTS" if has_alerts else "NOT FOUND"
            symbol = "[OK]" if has_alerts else "[WARN]"
            print(f"{symbol} Alerts table: {status}")
            
            if has_alerts:
                result = conn.execute(text("SELECT COUNT(*) FROM alerts"))
                alert_count = result.fetchone()[0]
                print(f"[OK] Alerts in database: {alert_count}")
        else:
            print(f"[WARN] Database 'erpagent': NOT FOUND")
            print("Creating database 'erpagent'...")
            
            # Close connection and create database
            conn.execute(text("COMMIT"))
            conn.execute(text("CREATE DATABASE erpagent"))
            print("[OK] Database 'erpagent' created!")
    
    print("=" * 60)
    print("[SUCCESS] Database connection test completed!")
    
except Exception as e:
    print("=" * 60)
    print(f"[ERROR] Connection failed: {e}")
    print("\nPossible solutions:")
    print("1. Check if PostgreSQL service is running")
    print("2. Verify password is correct")
    print("3. Check if database 'erpagent' exists")
    print("4. Use pgAdmin to verify connection")
