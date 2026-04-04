# -*- coding: utf-8 -*-
"""检查表结构"""
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    database='erp',
    user='postgres',
    password='postgres'
)
cur = conn.cursor()

tables = ['ap_invoices_all', 'po_lines_all', 'ap_payments_all']

for table in tables:
    print(f'\n{table}:')
    cur.execute(f"""
        SELECT column_name, data_type 
        FROM information_schema.columns 
        WHERE table_name = '{table}'
        ORDER BY ordinal_position
        LIMIT 20
    """)
    cols = cur.fetchall()
    for col, dtype in cols:
        print(f'  - {col} ({dtype})')

cur.close()
conn.close()
print('\n检查完成！')
