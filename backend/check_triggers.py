# -*- coding: utf-8 -*-
"""检查现有触发器"""

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

# 检查所有触发器
cur.execute("""
    SELECT tgname, tgrelid::regclass, proname
    FROM pg_trigger t
    JOIN pg_proc p ON t.tgfoid = p.oid
    WHERE tgname LIKE '%_rtr' OR tgname LIKE '%kg%'
    ORDER BY tgrelid::regclass::text, tgname
""")

print("触发器列表:")
print("-" * 60)
for row in cur.fetchall():
    print(f"  {row[0]:<30} on {row[1]:<30} -> {row[2]}")

cur.close()
conn.close()
