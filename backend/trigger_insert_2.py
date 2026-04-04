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
test_num = f'TRIGGER-TEST-{test_id}'

print(f"Inserting: {test_num}")
cur.execute("""
    INSERT INTO ap_invoices_all 
    (invoice_id, invoice_num, vendor_id, invoice_amount, payment_status, invoice_date)
    VALUES (%s, %s, %s, %s, %s, %s)
""", (test_id, test_num, 1, 100.00, 'PENDING', '2026-04-05'))

print("Done!")
cur.close()
conn.close()
