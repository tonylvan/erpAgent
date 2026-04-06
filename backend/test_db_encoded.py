"""
Test PostgreSQL database connection with URL encoding
"""
import sys
sys.path.insert(0, 'D:\\erpAgent\\backend')

from app.db.database import test_connection, engine
from sqlalchemy import text

print("Testing PostgreSQL connection...")
print("=" * 60)

# Test connection
if test_connection():
    print("✅ Database connection: SUCCESS")
    
    # Test query
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            print(f"✅ Test query result: {row.test}")
            
            # Check if erpagent database exists
            result = conn.execute(text("""
                SELECT datname FROM pg_database WHERE datname = 'erpagent'
            """))
            databases = [row[0] for row in result.fetchall()]
            
            if 'erpagent' in databases:
                print("✅ Database 'erpagent': EXISTS")
                
                # Check tables
                result = conn.execute(text("""
                    SELECT COUNT(*) FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """))
                table_count = result.fetchone()[0]
                print(f"✅ Tables in database: {table_count}")
                
                # Check alerts table
                result = conn.execute(text("""
                    SELECT EXISTS(SELECT 1 FROM information_schema.tables 
                    WHERE table_name = 'alerts')
                """))
                has_alerts = result.fetchone()[0]
                print(f"{'✅' if has_alerts else '⚠️'} Alerts table: {'EXISTS' if has_alerts else 'NOT FOUND'}")
                
                if has_alerts:
                    result = conn.execute(text("SELECT COUNT(*) FROM alerts"))
                    alert_count = result.fetchone()[0]
                    print(f"✅ Alerts in database: {alert_count}")
            else:
                print("⚠️ Database 'erpagent': NOT FOUND")
                print("Creating database 'erpagent'...")
                
                # Need to connect to postgres database to create new database
                conn.execute(text("COMMIT"))  # Close any transaction
                conn.execute(text("CREATE DATABASE erpagent"))
                print("✅ Database 'erpagent' created!")
                
    except Exception as e:
        print(f"❌ Query failed: {e}")
else:
    print("❌ Database connection: FAILED")

print("=" * 60)
