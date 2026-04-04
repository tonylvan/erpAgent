# -*- coding: utf-8 -*-
"""
RTR 极简消费者 - 100% 可靠版
纯同步代码，无异步，无缓冲问题
"""

import psycopg2
import json
import time
import os
from datetime import datetime
from decimal import Decimal

# 从 .env 读取配置
from dotenv import load_dotenv
load_dotenv()

print("="*60)
print("RTR Consumer - MINIMAL VERSION")
print("="*60)

# 配置
PG_HOST = os.getenv('POSTGRES_HOST', 'localhost')
PG_PORT = os.getenv('POSTGRES_PORT', '5432')
PG_DB = os.getenv('POSTGRES_DB', 'erp')
PG_USER = os.getenv('POSTGRES_USER', 'postgres')
PG_PASS = os.getenv('POSTGRES_PASSWORD', 'postgres')

NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASS = os.getenv('NEO4J_PASSWORD', 'Tony1985')

# 映射
TABLE_MAP = {
    'ap_invoices_all': ('Invoice', 'invoice_id'),
    'ap_payments_all': ('Payment', 'payment_id'),
    'po_headers_all': ('PurchaseOrder', 'po_header_id'),
    'po_lines_all': ('POLine', 'po_line_id')
}

# 连接 PostgreSQL
print(f"\n[1/3] PostgreSQL: {PG_HOST}:{PG_PORT}/{PG_DB}")
pg = psycopg2.connect(
    host=PG_HOST,
    port=int(PG_PORT),
    database=PG_DB,
    user=PG_USER,
    password=PG_PASS
)
pg.autocommit = True
cur = pg.cursor()
print("      [OK] Connected")

# 连接 Neo4j
print(f"[2/3] Neo4j: {NEO4J_URI}")
from neo4j import GraphDatabase
neo4j = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
print("      [OK] Connected")

# 监听
print("[3/3] Listening on neo4j_rtr_sync...")
cur.execute("LISTEN neo4j_rtr_sync;")
pg.commit()
print("      [OK] Subscribed\n")

print("="*60)
print("READY - Waiting for changes...")
print("="*60)
print()

def clean(d):
    if not d: return {}
    return {k: (float(v) if isinstance(v, Decimal) else v) 
            for k, v in d.items() if v is not None}

def sync(table, op, data):
    if table not in TABLE_MAP:
        print(f"  [SKIP] {table}")
        return False
    
    label, pk = TABLE_MAP[table]
    d = clean(data)
    pk_val = d.get(pk)
    
    with neo4j.session() as s:
        try:
            if op == 'INSERT':
                props = ', '.join([f'{k}: ${k}' for k in d.keys()])
                s.run(f"CREATE (n:{label} {{{props}}})", **d)
                print(f"  [OK] CREATE {label} {pk}={pk_val}")
                
            elif op == 'UPDATE':
                r = s.run(f"MATCH (n:{label}) WHERE n.{pk}=$pk_id RETURN n", pk_id=pk_val)
                if r.single():
                    sets = ', '.join([f"n.{k}=${k}" for k in d.keys() if k != pk])
                    s.run(f"MATCH (n:{label}) WHERE n.{pk}=$pk_id SET {sets}", **d)
                    print(f"  [OK] UPDATE {label} {pk}={pk_val}")
                else:
                    props = ', '.join([f'{k}: ${k}' for k in d.keys()])
                    s.run(f"CREATE (n:{label} {{{props}}})", **d)
                    print(f"  [OK] CREATE (not found) {label} {pk}={pk_val}")
                    
            elif op == 'DELETE':
                r = s.run(f"MATCH (n:{label}) WHERE n.{pk}=$pk_id DETACH DELETE n", pk_id=pk_val)
                print(f"  [OK] DELETE {r.summary().counters.nodes_deleted} node(s)")
            
            # 更新日志
            cur.execute("""UPDATE rtr_sync_log SET status='completed' 
                          WHERE table_name=%s AND operation=%s 
                          ORDER BY id DESC LIMIT 1""", (table, op))
            pg.commit()
            return True
        except Exception as e:
            print(f"  [ERR] {e}")
            cur.execute("""UPDATE rtr_sync_log SET status='failed' 
                          WHERE table_name=%s AND operation=%s 
                          ORDER BY id DESC LIMIT 1""", (table, op))
            pg.commit()
            return False

cnt = 0
try:
    while True:
        pg.poll()
        while pg.notifies:
            n = pg.notifies.pop(0)
            t = time.strftime('%H:%M:%S')
            cnt += 1
            
            print(f"[{t}] #{cnt} RECV: {n.payload[:80]}")
            
            try:
                data = json.loads(n.payload)
                tbl = data.get('table')
                opr = data.get('operation')
                rec = data.get('new') or data.get('old')
                
                print(f"        {tbl} / {opr}")
                sync(tbl, opr, rec)
                print()
            except Exception as e:
                print(f"  [ERR] Parse: {e}\n")
        
        time.sleep(0.1)
except KeyboardInterrupt:
    print("\n\n" + "="*60)
    print(f"STOPPED - Processed {cnt} notifications")
    print("="*60)
finally:
    cur.close()
    pg.close()
    neo4j.close()
    print("[OK] Closed")
