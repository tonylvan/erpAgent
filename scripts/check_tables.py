# -*- coding: utf-8 -*-
import psycopg2

conn = psycopg2.connect(
    host='localhost', port=5432, database='erpagent',
    user='postgres', password='Tony1985'
)
cur = conn.cursor()

# Get all tables
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema='public' 
    ORDER BY table_name
""")
tables = cur.fetchall()

print("=" * 60)
print("PostgreSQL Tables in 'erpagent' database:")
print("=" * 60)
for t in tables:
    print(f"  - {t[0]}")

print(f"\nTotal: {len(tables)} tables")

# Get row counts for main tables
print("\n" + "=" * 60)
print("Row counts for main tables:")
print("=" * 60)

main_tables = ['sales', 'orders', 'customers', 'products', 'payments', 
               'purchase_orders', 'suppliers', 'employees', 'departments']

for table in main_tables:
    try:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        count = cur.fetchone()[0]
        print(f"  - {table}: {count} rows")
    except Exception as e:
        print(f"  - {table}: not found")

cur.close()
conn.close()