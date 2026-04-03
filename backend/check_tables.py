# -*- coding: utf-8 -*-
import psycopg2

dsn = "host=localhost dbname=erpostgres user=postgres password=Tony1985"
conn = psycopg2.connect(dsn)

cur = conn.cursor()
cur.execute("SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'")
count = cur.fetchone()[0]

print(f'PostgreSQL 表数量：{count}')

cur.execute("""
    SELECT table_name FROM information_schema.tables 
    WHERE table_schema = 'public' 
    ORDER BY table_name
""")

tables = cur.fetchall()
print(f'\n表清单 ({count}张):')
for i, t in enumerate(tables[:20], 1):
    print(f"  {i}. {t[0]}")
if count > 20:
    print(f"  ... 还有 {count - 20} 张表")

conn.close()
