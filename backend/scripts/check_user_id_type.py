import psycopg2

conn = psycopg2.connect('postgresql://erp:erp@localhost:5432/erp')
cur = conn.cursor()
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'query_history' 
    AND column_name = 'user_id'
""")
print(cur.fetchone())

cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'sys_users' 
    AND column_name = 'user_id'
""")
print(cur.fetchone())

cur.close()
conn.close()
