import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='erp',
    user='postgres',
    password='postgres'
)
conn.autocommit = True
cur = conn.cursor()

# 临时禁用触发器
print("临时禁用触发器...")
cur.execute("ALTER TABLE ap_payments_all DISABLE TRIGGER ap_payments_rtr")
cur.execute("ALTER TABLE ap_invoices_all DISABLE TRIGGER ap_invoices_rtr")
cur.execute("ALTER TABLE po_headers_all DISABLE TRIGGER po_headers_rtr")
cur.execute("ALTER TABLE po_lines_all DISABLE TRIGGER po_lines_rtr")

print("[OK] 触发器已禁用")

cur.close()
conn.close()
