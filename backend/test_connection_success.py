"""
Test PostgreSQL connection after successful password reset
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
DB_NAME = "postgres"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

print("Testing PostgreSQL connection...")
print("=" * 60)

try:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
    
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1 as test"))
        row = result.fetchone()
        print(f"[OK] Connection successful!")
        print(f"[OK] Test query result: {row.test}")
        
        # Check erpagent database
        result = conn.execute(text("""
            SELECT datname FROM pg_database WHERE datname = 'erpagent'
        """))
        databases = [row[0] for row in result.fetchall()]
        
        if 'erpagent' in databases:
            print(f"[OK] Database 'erpagent': EXISTS")
            
            # Create alerts table if not exists
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS alerts (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    level VARCHAR(20) NOT NULL,
                    status VARCHAR(20) NOT NULL,
                    business_module VARCHAR(100) NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
            print(f"[OK] Alerts table: CREATED/EXISTS")
            
            # Insert sample data
            conn.execute(text("""
                INSERT INTO alerts (title, level, status, business_module, description)
                VALUES 
                ('Critical sales anomaly', 'CRITICAL', 'UNREAD', 'Sales', 'Sales dropped 45%'),
                ('Inventory low', 'HIGH', 'UNREAD', 'Warehouse', 'SKU-1234 below safety stock'),
                ('Payment overdue', 'MEDIUM', 'READ', 'Finance', 'ABC Corp payment overdue')
            """))
            conn.commit()
            
            result = conn.execute(text("SELECT COUNT(*) FROM alerts"))
            alert_count = result.fetchone()[0]
            print(f"[OK] Alerts in database: {alert_count}")
        else:
            print(f"[INFO] Creating database 'erpagent'...")
            conn.execute(text("COMMIT"))
            conn.execute(text("CREATE DATABASE erpagent"))
            print(f"[OK] Database 'erpagent' created!")
    
    print("=" * 60)
    print("[SUCCESS] Database connection test completed!")
    print("[SUCCESS] PostgreSQL is ready to use!")
    
except Exception as e:
    print("=" * 60)
    print(f"[ERROR] Connection failed: {e}")
