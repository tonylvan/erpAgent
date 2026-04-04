# -*- coding: utf-8 -*-
"""简单监听测试"""

import psycopg2
import time

print("Connecting to PostgreSQL...")
conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='erp',
    user='postgres',
    password='postgres'
)
conn.autocommit = True

cur = conn.cursor()

# 监听
print("Listening on neo4j_rtr_sync...")
cur.execute("LISTEN neo4j_rtr_sync;")
print("Listening!\n")

# 等待通知
start = time.time()
while time.time() - start < 10:
    conn.poll()
    while conn.notifies:
        notify = conn.notifies.pop(0)
        print(f"[RECV] Channel: {notify.channel}")
        print(f"       Payload: {notify.payload}\n")
    time.sleep(0.5)

print("Timeout. No notifications received.")

cur.close()
conn.close()
