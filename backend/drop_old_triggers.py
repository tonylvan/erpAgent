# -*- coding: utf-8 -*-
"""删除旧触发器"""

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

with open('drop_old_triggers.sql', 'r', encoding='utf-8') as f:
    sql = f.read()

cur.execute(sql)
print("[OK] Old triggers dropped")

cur.close()
conn.close()
