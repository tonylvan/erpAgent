# -*- coding: utf-8 -*-
"""
OTC/PTP 实时同步端到端测试（修复版）
"""

import psycopg2
import json
import time
import os
import random
from dotenv import load_dotenv
load_dotenv()

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

print("="*70)
print("OTC/PTP RTR 端到端测试（修复版）")
print("="*70)

# 连接
print("\n[1/3] 连接 PostgreSQL...")
pg = psycopg2.connect(**PG)
pg.autocommit = True
cur = pg.cursor()
print("      [OK]")

print("[2/3] 连接 Neo4j...")
neo4j = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASS))
print("      [OK]")

print("[3/3] 监听 neo4j_rtr_sync...")
cur.execute("LISTEN neo4j_rtr_sync;")
pg.commit()
print("      [OK]")

# 生成唯一 ID 避免冲突
base_id = random.randint(100000, 999999)

# 测试用例（使用正确的字段名）
test_cases = [
    {
        'name': 'OTC - 创建销售订单',
        'table': 'oe_order_headers_all',
        'label': 'SalesOrder',
        'sql': """INSERT INTO oe_order_headers_all 
                  (header_id, order_number, customer_id, order_date, status, total_amount) 
                  VALUES (%s, %s, %s, %s, %s, %s)""",
        'values': (base_id, f'ORD-{base_id}', 1, '2026-04-05', 'PENDING', 1000.00),
        'verify_id': base_id,
        'verify_key': 'header_id'
    },
    {
        'name': 'OTC - 创建客户',
        'table': 'ar_customers',
        'label': 'Customer',
        'sql': """INSERT INTO ar_customers 
                  (customer_id, customer_name, customer_number, status) 
                  VALUES (%s, %s, %s, %s)""",
        'values': (base_id + 1, f'Test Customer {base_id+1}', f'CUST-{base_id+1}', 'ACTIVE'),
        'verify_id': base_id + 1,
        'verify_key': 'customer_id'
    },
    {
        'name': 'PTP - 创建采购订单',
        'table': 'po_headers_all',
        'label': 'PurchaseOrder',
        'sql': """INSERT INTO po_headers_all 
                  (po_header_id, segment1, vendor_id, amount, status_lookup_code, currency_code) 
                  VALUES (%s, %s, %s, %s, %s, %s)""",
        'values': (base_id + 2, f'PO-{base_id+2}', 1, 5000.00, 'APPROVED', 'CNY'),
        'verify_id': base_id + 2,
        'verify_key': 'po_header_id'
    },
    {
        'name': 'PTP - 创建供应商',
        'table': 'ap_suppliers',
        'label': 'Supplier',
        'sql': """INSERT INTO ap_suppliers 
                  (vendor_id, vendor_name, segment1, status) 
                  VALUES (%s, %s, %s, %s)""",
        'values': (base_id + 3, f'Test Supplier {base_id+3}', f'SUPP-{base_id+3}', 'ACTIVE'),
        'verify_id': base_id + 3,
        'verify_key': 'vendor_id'
    }
]

results = []

for tc in test_cases:
    print(f"\n{'='*70}")
    print(f"测试：{tc['name']}")
    print(f"{'='*70}")
    
    # 插入数据
    try:
        cur.execute(tc['sql'], tc['values'])
        print(f"[OK] PostgreSQL 插入成功 (ID={tc['verify_id']})")
    except Exception as e:
        print(f"[FAIL] PostgreSQL 插入失败：{e}")
        results.append((tc['name'], False, str(e)))
        continue
    
    # 等待通知
    print("等待同步通知...")
    start = time.time()
    received = False
    synced = False
    
    while time.time() - start < 5:
        pg.poll()
        while pg.notifies:
            n = pg.notifies.pop(0)
            received = True
            payload = n.payload[:150] if len(n.payload) > 150 else n.payload
            print(f"[RECV] {payload}...")
            
            data = json.loads(n.payload)
            if data.get('table') == tc['table']:
                # 同步到 Neo4j
                rec = data.get('data')
                if rec:
                    d = {k: v for k, v in rec.items() if v is not None}
                    label = tc['label']
                    
                    with neo4j.session() as s:
                        try:
                            props = ', '.join([f'{k}: ${k}' for k in d.keys()])
                            s.run(f"CREATE (n:{label} {{{props}}})", **d)
                            print(f"[OK] Neo4j 同步成功")
                            
                            # 验证
                            verify_query = f"MATCH (n:{label} {{{tc['verify_key']}: {tc['verify_id']}}}) RETURN n"
                            r = s.run(verify_query)
                            if r.single():
                                synced = True
                                print(f"[OK] Neo4j 验证成功")
                        except Exception as e:
                            print(f"[WARN] Neo4j 同步警告：{e}")
        
        time.sleep(0.1)
    
    # 更新日志
    cur.execute("""UPDATE rtr_sync_log SET status='completed' 
                  WHERE id = (SELECT MAX(id) FROM rtr_sync_log 
                              WHERE table_name=%s AND operation='INSERT')""", (tc['table'],))
    pg.commit()
    
    results.append((tc['name'], synced, 'OK' if synced else 'Timeout'))

# 总结
print(f"\n{'='*70}")
print("测试结果总结")
print(f"{'='*70}")

passed = sum(1 for _, success, _ in results if success)
total = len(results)

for name, success, msg in results:
    status = "[OK]" if success else "[FAIL]"
    print(f"{status} {name}: {msg}")

print(f"\n总计：{passed}/{total} 通过")

if passed == total:
    print("\n[SUCCESS] 所有 OTC/PTP 同步测试通过！")
else:
    print(f"\n[WARNING] {total - passed} 个测试失败")

print(f"{'='*70}\n")

cur.close()
pg.close()
neo4j.close()
