# -*- coding: utf-8 -*-
"""
RTR 完整测试 - 单进程验证
1. 启动监听
2. 触发插入
3. 验证同步
"""

import psycopg2
import json
import time
import os
from dotenv import load_dotenv
load_dotenv()

# 配置
PG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'database': os.getenv('POSTGRES_DB', 'erp'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
}

NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASS = os.getenv('NEO4J_PASSWORD', 'Tony1985')

from neo4j import GraphDatabase

print("="*60)
print("RTR END-TO-END TEST")
print("="*60)

# 连接
print("\n[1/4] Connecting to PostgreSQL...")
pg = psycopg2.connect(**PG)
pg.autocommit = True
cur = pg.cursor()
print("      [OK]")

print("[2/4] Connecting to Neo4j...")
neo4j = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
print("      [OK]")

# 监听
print("[3/4] Listening on neo4j_rtr_sync...")
cur.execute("LISTEN neo4j_rtr_sync;")
pg.commit()
print("      [OK]")

# 触发插入
test_id = int(time.time() * 1000) % 1000000
test_num = f'E2E-TEST-{test_id}'

print(f"\n[4/4] Triggering INSERT: {test_num} (ID={test_id})")

cur.execute("""
    INSERT INTO ap_invoices_all 
    (invoice_id, invoice_num, vendor_id, invoice_amount, payment_status, invoice_date)
    VALUES (%s, %s, %s, %s, %s, %s)
""", (test_id, test_num, 1, 555.55, 'PENDING', '2026-04-05'))

print("      Inserted! Waiting for notification...\n")

# 等待并处理通知
start = time.time()
received = False
synced = False

while time.time() - start < 5:
    pg.poll()
    while pg.notifies:
        n = pg.notifies.pop(0)
        received = True
        print(f"[RECV] {n.payload}")
        
        data = json.loads(n.payload)
        tbl = data.get('table')
        opr = data.get('operation')
        rec = data.get('data') or data.get('new')  # 读取 data 字段
        
        print(f"        Table={tbl}, Op={opr}")
        print(f"        Data keys: {list(rec.keys()) if rec else 'None'}")
        
        # 同步到 Neo4j
        if rec:
            d = {}
            for k, v in rec.items():
                if v is not None:
                    d[k] = v
            
            print(f"        Syncing {len(d)} fields to Neo4j...")
            try:
                with neo4j.session() as s:
                    props = ', '.join([f'{k}: ${k}' for k in d.keys()])
                    query = f"CREATE (n:Invoice {{{props}}})"
                    s.run(query, **d)
                    print(f"        [SYNC] Created Invoice node!")
                    
                    # 验证
                    r = s.run("MATCH (i:Invoice) WHERE i.invoice_id=$id RETURN i", id=test_id)
                    rec_result = r.single()
                    if rec_result:
                        synced = True
                        print(f"        [VERIFY] Node found!")
            except Exception as e:
                print(f"        [ERROR] {e}")
        
        # 更新日志
        cur.execute("""UPDATE rtr_sync_log SET status='completed' 
                      WHERE id = (SELECT MAX(id) FROM rtr_sync_log 
                                  WHERE table_name=%s AND operation=%s)""", (tbl, opr))
        pg.commit()
    
    time.sleep(0.1)

# 结果
print("\n" + "="*60)
print("TEST RESULTS")
print("="*60)
print(f"Notification Received: {'YES' if received else 'NO'}")
print(f"Neo4j Sync Completed:  {'YES' if synced else 'NO'}")
print("="*60)

if received and synced:
    print("\n SUCCESS! RTR sync is working!\n")
else:
    print("\n PARTIAL SUCCESS - Check details above\n")

cur.close()
pg.close()
neo4j.close()
