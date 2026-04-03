#!/usr/bin/env python
import psycopg2

conn = psycopg2.connect(host='localhost', database='erp', user='postgres', password='postgres')
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE'")
total = cur.fetchone()[0]
print(f"Total tables: {total}")

cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema='public' ORDER BY table_name")
tables = cur.fetchall()
print(f"\nTable list ({len(tables)} tables):")
for t in tables:
    print(f"  - {t[0]}")

conn.close()
