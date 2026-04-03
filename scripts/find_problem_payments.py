import psycopg2

PG_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'erp',
    'user': 'postgres',
    'password': 'postgres'
}

conn = psycopg2.connect(**PG_CONFIG)
cur = conn.cursor()

print("="*70)
print("检查问题数据 ID 范围")
print("="*70)

tables = [
    ('ap_invoices_all', 'invoice_id', '发票'),
    ('ap_payments_all', 'check_id', '付款单'),
    ('po_headers_all', 'po_header_id', 'PO'),
    ('hr_employees', 'employee_id', '员工'),
    ('ap_suppliers', 'supplier_id', '供应商'),
]

for table, id_col, name in tables:
    print(f"\n{name} ({table}):")
    cur.execute(f"""
        SELECT min({id_col}), max({id_col}), count(*) 
        FROM {table}
    """)
    row = cur.fetchone()
    print(f"  ID 范围：{row[0]} - {row[1]} (共{row[2]}条)")

# 查找带 problem 或 noisy 的表
print("\n" + "="*70)
print("查找问题数据表:")
print("-"*70)
cur.execute("""
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND (table_name ILIKE '%problem%' OR table_name ILIKE '%noisy%')
""")
tables = cur.fetchall()
if tables:
    for row in tables:
        print(f"  {row[0]}")
else:
    print("  未找到问题数据表")
    print("  问题数据可能还没生成或已删除")

cur.close()
conn.close()
