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

test_id = int(time.time() * 1000) % 1000000
test_num = f'FINAL-TEST-{test_id}'

print(f"Inserting: {test_num} (ID={test_id})")

cur.execute("""
    INSERT INTO ap_invoices_all 
    (invoice_id, invoice_num, vendor_id, invoice_amount, payment_status, invoice_date)
    VALUES (%s, %s, %s, %s, %s, %s)
""", (test_id, test_num, 1, 777.77, 'PENDING', '2026-04-05'))

print("Inserted! Waiting 3 seconds...")
time.sleep(3)

# Check sync log
cur.execute("""
    SELECT id, table_name, operation, record_id, status, sync_time 
    FROM rtr_sync_log 
    ORDER BY id DESC 
    LIMIT 3
""")

print("\nSync Log:")
for row in cur.fetchall():
    status_icon = "OK" if row[4] == 'completed' else "PENDING"
    print(f"  [{status_icon}] ID={row[0]} | {row[1]} | {row[2]} | record={row[3]}")

cur.close()
conn.close()
