"""
Check if erpagent database exists in PostgreSQL
"""
import psycopg2

try:
    # Connect to default postgres database
    print("Connecting to PostgreSQL (postgres database)...")
    conn = psycopg2.connect(
        host='localhost',
        user='postgres',
        password='Tony1985',
        dbname='postgres'
    )
    print("Connection: OK")
    
    # Check if erpagent database exists
    cur = conn.cursor()
    cur.execute("SELECT datname FROM pg_database WHERE datname = 'erpagent'")
    result = cur.fetchone()
    
    if result:
        print("Database 'erpagent' EXISTS")
    else:
        print("Database 'erpagent' NOT FOUND")
        print("\nCreating database 'erpagent'...")
        cur.execute("CREATE DATABASE erpagent")
        conn.commit()
        print("Database created!")
    
    conn.close()
    
except Exception as e:
    print(f"Error: {e}")
    print("\nTrying with different password encoding...")
