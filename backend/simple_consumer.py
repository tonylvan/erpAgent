# -*- coding: utf-8 -*-
"""
RTR 简单消费者 - 测试版
"""

import psycopg2
import time
import sys
import io

if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

print("="*60)
print("RTR 简单消费者启动")
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

# 监听
cur.execute("LISTEN neo4j_rtr_sync;")
print("已订阅频道：neo4j_rtr_sync")
print("开始监听...\n")

while True:
    conn.poll()
    while conn.notifies:
        notify = conn.notifies.pop(0)
        print(f"[RECV] Channel: {notify.channel}")
        print(f"       Payload: {notify.payload}")
        print()
    time.sleep(0.5)
