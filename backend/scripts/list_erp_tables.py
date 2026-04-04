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
    database=os.getenv('POSTGRES_DB', 'gsd_erp'),
    user=os.getenv('POSTGRES_USER', 'postgres'),
    password=os.getenv('POSTGRES_PASSWORD', 'Tongtong2025!')
)
cur = conn.cursor()

print("=" * 60)
print("PostgreSQL 表列表 (AP/PO/AR/INV 相关)")
print("=" * 60)

cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public'
    AND (table_name LIKE 'ap_%' OR table_name LIKE 'po_%' OR table_name LIKE 'ar_%' OR table_name LIKE 'inv_%' OR table_name LIKE 'item_%')
    ORDER BY table_name
""")

tables = cur.fetchall()
print(f"\n找到 {len(tables)} 张相关表:")
for (table_name,) in tables:
    print(f"  - {table_name}")

cur.close()
conn.close()

print("\n" + "=" * 60)
