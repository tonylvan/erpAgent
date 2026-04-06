"""
Test PostgreSQL database connection
"""
import psycopg2

try:
    # Connect to PostgreSQL
    print("Connecting to PostgreSQL...")
    conn = psycopg2.connect(
        host='localhost',
        user='postgres',
        password='Tony1985',
        dbname='erpagent'
    )
    print("Database connection: OK")
    
    # Check tables
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
    tables = cur.fetchone()[0]
    print(f"Tables in database: {tables}")
    
    # Check alerts table
    cur.execute("SELECT EXISTS(SELECT 1 FROM information_schema.tables WHERE table_name = 'alerts')")
    has_alerts = cur.fetchone()[0]
    print(f"Alerts table exists: {has_alerts}")
    
    if has_alerts:
        cur.execute("SELECT COUNT(*) FROM alerts")
        alert_count = cur.fetchone()[0]
        print(f"Alerts in database: {alert_count}")
    
    conn.close()
    print("Connection closed")
    
except Exception as e:
    print(f"Error: {e}")
