# -*- coding: utf-8 -*-
"""简单测试触发器是否触发"""

import psycopg2
import time

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='erp',
    user='postgres',
    password='postgres'
)
conn.autocommit = True

cur = conn.cursor()

# 插入测试
print("插入测试数据...")
cur.execute("""
    INSERT INTO ap_invoices_all 
    (invoice_id, invoice_num, vendor_id, invoice_amount, payment_status, invoice_date)
    VALUES (%s, %s, %s, %s, %s, %s)
""", (88888, 'TRIGGER-TEST-1', 1, 100.00, 'PENDING', '2026-04-05'))

print("已插入，等待 2 秒...")
time.sleep(2)

# 检查日志
cur.execute("""
    SELECT id, table_name, operation, status, sync_time 
    FROM rtr_sync_log 
    ORDER BY id DESC 
    LIMIT 5
""")

print("\n同步日志:")
for row in cur.fetchall():
    print(f"  {row}")

cur.close()
conn.close()
