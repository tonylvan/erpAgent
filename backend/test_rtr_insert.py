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

# 使用唯一 ID
test_id = int(time.time() * 1000) % 1000000
test_num = f'RTR-FIXED-{test_id}'

print(f"Inserting test invoice: {test_num} (ID={test_id})")

cur.execute("""
    INSERT INTO ap_invoices_all 
    (invoice_id, invoice_num, vendor_id, invoice_amount, payment_status, invoice_date)
    VALUES (%s, %s, %s, %s, %s, %s)
""", (test_id, test_num, 1, 999.99, 'PENDING', '2026-04-05'))

print("Inserted! Waiting 3 seconds for sync...")
time.sleep(3)

# 检查日志
cur.execute("""
    SELECT id, table_name, operation, status, sync_time 
    FROM rtr_sync_log 
    ORDER BY id DESC 
    LIMIT 3
""")

print("\nSync Log:")
for row in cur.fetchall():
    print(f"  {row}")

cur.close()
conn.close()
