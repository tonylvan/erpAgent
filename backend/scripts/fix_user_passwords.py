import psycopg2

conn = psycopg2.connect('postgresql://erp:erp@localhost:5432/erp')
cur = conn.cursor()
cur.execute("""
    UPDATE sys_users 
    SET password_hash = '49c92bf417203a0011bf7d996d82a031625f96274c2630987342de2e5b2cee25'
    WHERE username IN ('finance_user', 'procurement_user', 'sales_user')
""")
conn.commit()
print(f'Updated {cur.rowcount} users')
cur.close()
conn.close()
