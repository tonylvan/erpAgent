# -*- coding: utf-8 -*-
"""最小化消费者 - 直接打印"""

import psycopg2
import json
import time

print("="*60)
print("Mini RTR Consumer")
print("="*60)

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='erp',
    user='postgres',
    password='postgres'
)
conn.autocommit = True

cur = conn.cursor()
cur.execute("LISTEN neo4j_rtr_sync;")

print("Listening on neo4j_rtr_sync...\n")

while True:
    conn.poll()
    while conn.notifies:
        notify = conn.notifies.pop(0)
        print(f"[{time.strftime('%H:%M:%S')}] RECV: {notify.payload}")
        
        # 尝试解析并打印
        try:
            data = json.loads(notify.payload)
            print(f"           Table={data.get('table')}, Op={data.get('operation')}, ID={data.get('record_id')}")
        except:
            pass
    
    time.sleep(0.5)
