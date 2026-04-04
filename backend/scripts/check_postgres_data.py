# -*- coding: utf-8 -*-
"""检查 PostgreSQL 实际数据"""
import psycopg2

conn = psycopg2.connect(
    host='localhost',
    database='erp',
    user='postgres',
    password='postgres'
)
cur = conn.cursor()

# 表列表
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    ORDER BY table_name
""")
tables = [t[0] for t in cur.fetchall()]
print(f'PostgreSQL 表数量：{len(tables)}')
print('\n前 30 个表:')
for i, t in enumerate(tables[:30], 1):
    print(f'  {i}. {t}')

# 检查关键表的数据和外键字段
print('\n' + '=' * 60)
print('检查关键表的外键字段')
print('=' * 60)

key_tables = [
    ('ap_invoice_po_matches', ['invoice_id', 'po_line_id']),
    ('payment', ['invoice_id']),
    ('po_lines', ['po_header_id']),
    ('po_distributions', ['po_line_id']),
    ('ar_transactions', ['customer_id']),
    ('accounting_entries', ['batch_id', 'event_id'])
]

for table, fields in key_tables:
    try:
        cur.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = '{table}' 
            AND column_name IN ({','.join([f"'{f}'" for f in fields])})
            ORDER BY column_name
        """)
        cols = cur.fetchall()
        if cols:
            print(f'\n{table}:')
            for col, dtype in cols:
                print(f'  - {col} ({dtype})')
        else:
            print(f'\n{table}: 未找到外键字段')
    except Exception as e:
        print(f'\n{table}: 错误 - {e}')

# 检查数据量
print('\n' + '=' * 60)
print('检查数据量')
print('=' * 60)

for table in ['ap_invoice_po_matches', 'payment', 'po_lines', 'ar_transactions']:
    try:
        cur.execute(f'SELECT COUNT(*) FROM {table}')
        count = cur.fetchone()[0]
        print(f'  {table}: {count} 条')
    except:
        print(f'  {table}: 不存在')

cur.close()
conn.close()
print('\n检查完成！')
