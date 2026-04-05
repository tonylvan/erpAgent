#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""检查 OTC/PTP 表结构"""

import psycopg2

PG_CONFIG = {
    'host': 'localhost',
    'database': 'erp',
    'user': 'postgres',
    'password': 'postgres'
}

# 需要检查的表
tables = [
    'po_headers_all',
    'ap_suppliers',
    'ar_customers',
    'oe_order_headers_all'
]

conn = psycopg2.connect(**PG_CONFIG)
cur = conn.cursor()

for table in tables:
    print(f"\n{'='*60}")
    print(f"表：{table}")
    print('='*60)
    
    cur.execute("""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = %s 
        ORDER BY ordinal_position
    """, (table,))
    
    columns = cur.fetchall()
    for col_name, data_type in columns[:20]:  # 只显示前 20 个字段
        print(f"  {col_name:30} {data_type}")
    
    if len(columns) > 20:
        print(f"  ... 共 {len(columns)} 个字段")

cur.close()
conn.close()

print("\n✅ 检查完成")
