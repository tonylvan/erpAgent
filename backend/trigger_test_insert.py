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
cur.execute("""
    INSERT INTO ap_invoices_all 
    (invoice_id, invoice_num, vendor_id, invoice_amount, payment_status, invoice_date)
    VALUES (77777, 'TEST999', 1, 50.00, 'PENDING', '2026-04-05')
""")
print("Inserted test invoice 77777")

cur.close()
conn.close()
