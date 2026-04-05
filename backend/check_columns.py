import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='erp',
    user='postgres',
    password='postgres'
)
cur = conn.cursor()

print('mtl_material_transactions 表结构:')
cur.execute("""SELECT column_name, data_type FROM information_schema.columns 
WHERE table_name='mtl_material_transactions' ORDER BY ordinal_position LIMIT 20""")
for row in cur.fetchall():
    print(f'  {row[0]:<30} {row[1]}')

print('\nmtl_system_items_b 表结构:')
cur.execute("""SELECT column_name, data_type FROM information_schema.columns 
WHERE table_name='mtl_system_items_b' ORDER BY ordinal_position LIMIT 20""")
for row in cur.fetchall():
    print(f'  {row[0]:<30} {row[1]}')

print('\npo_headers_all 表结构:')
cur.execute("""SELECT column_name, data_type FROM information_schema.columns 
WHERE table_name='po_headers_all' ORDER BY ordinal_position LIMIT 20""")
for row in cur.fetchall():
    print(f'  {row[0]:<30} {row[1]}')

print('\nap_invoices_all 表结构:')
cur.execute("""SELECT column_name, data_type FROM information_schema.columns 
WHERE table_name='ap_invoices_all' ORDER BY ordinal_position LIMIT 20""")
for row in cur.fetchall():
    print(f'  {row[0]:<30} {row[1]}')

print('\nap_payments_all 表结构:')
cur.execute("""SELECT column_name, data_type FROM information_schema.columns 
WHERE table_name='ap_payments_all' ORDER BY ordinal_position LIMIT 20""")
for row in cur.fetchall():
    print(f'  {row[0]:<30} {row[1]}')

cur.close()
conn.close()
