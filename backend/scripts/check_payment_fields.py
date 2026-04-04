# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

conn = psycopg2.connect(
    host='localhost',
    port='5432',
    database='erp',
    user='postgres',
    password='Tongtong2025!'
)
cur = conn.cursor()

print("ap_payments_all 表字段:")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'ap_payments_all' 
    ORDER BY ordinal_position
""")
for row in cur.fetchall():
    print(f"  - {row[0]} ({row[1]})")

print("\npo_distributions_all 表字段:")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'po_distributions_all' 
    ORDER BY ordinal_position
    LIMIT 20
""")
for row in cur.fetchall():
    print(f"  - {row[0]} ({row[1]})")

print("\nar_transactions_all 表字段:")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'ar_transactions_all' 
    ORDER BY ordinal_position
    LIMIT 20
""")
for row in cur.fetchall():
    print(f"  - {row[0]} ({row[1]})")

print("\ninv_system_items_b 表字段:")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'inv_system_items_b' 
    ORDER BY ordinal_position
    LIMIT 20
""")
for row in cur.fetchall():
    print(f"  - {row[0]} ({row[1]})")

cur.close()
conn.close()
