import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='erp',
    user='postgres',
    password='postgres'
)
cur = conn.cursor()

print('ap_payments_all 表结构:')
cur.execute("""SELECT column_name, data_type FROM information_schema.columns 
WHERE table_name='ap_payments_all' ORDER BY ordinal_position LIMIT 30""")
for row in cur.fetchall():
    print(f'  {row[0]:<30} {row[1]}')

cur.close()
conn.close()
