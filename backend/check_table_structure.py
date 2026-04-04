# -*- coding: utf-8 -*-
"""检查 ap_invoices_all 表结构"""

import psycopg2
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='erp',
    user='postgres',
    password='postgres'
)

cur = conn.cursor()

# 检查表结构
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'ap_invoices_all'
    ORDER BY ordinal_position
""")

print("ap_invoices_all 表结构:")
print("-" * 50)
for row in cur.fetchall():
    print(f"  {row[0]:<30} {row[1]}")

cur.close()
conn.close()
