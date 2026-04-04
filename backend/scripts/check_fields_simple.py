# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port='5432',
    database='erp',
    user='postgres',
    password='Tongtong2025!'
)
cur = conn.cursor()

tables_fields = [
    'ap_payments_all',
    'po_distributions_all', 
    'ar_transactions_all',
    'inv_system_items_b'
]

for table in tables_fields:
    print(f"\n{table} 表字段:")
    cur.execute(f"""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = '{table}' 
        ORDER BY ordinal_position
        LIMIT 15
    """)
    for (col,) in cur.fetchall():
        print(f"  - {col}")

cur.close()
conn.close()
