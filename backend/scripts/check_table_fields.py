# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv('POSTGRES_HOST', 'localhost'),
    port=os.getenv('POSTGRES_PORT', '5432'),
    database=os.getenv('POSTGRES_DB', 'erp'),
    user=os.getenv('POSTGRES_USER', 'postgres'),
    password=os.getenv('POSTGRES_PASSWORD', 'Tongtong2025!')
)
cur = conn.cursor()

print("=" * 60)
print("PostgreSQL 表结构查询")
print("=" * 60)

# 查询 ap_invoice_po_matches 表字段
print("\n[ap_invoice_po_matches] 表字段:")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'ap_invoice_po_matches' 
    ORDER BY ordinal_position
""")
for row in cur.fetchall():
    print(f"  - {row[0]} ({row[1]})")

# 查询 ap_payments_all 表字段
print("\n[ap_payments_all] 表字段:")
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'ap_payments_all' 
    ORDER BY ordinal_position
""")
for row in cur.fetchall():
    print(f"  - {row[0]} ({row[1]})")

cur.close()
conn.close()

print("\n" + "=" * 60)
