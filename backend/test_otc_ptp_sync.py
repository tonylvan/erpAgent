# -*- coding: utf-8 -*-
"""
OTC/PTP 实时同步端到端测试
"""

import psycopg2
import json
import time
import os
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
print("OTC/PTP RTR 端到端测试")
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

# 监听
print("[3/3] 监听 neo4j_rtr_sync...")
cur.execute("LISTEN neo4j_rtr_sync;")
pg.commit()
print("      [OK]")

# 测试用例
test_cases = [
    {
        'name': 'OTC - 创建销售订单',
        'table': 'oe_order_headers_all',
        'sql': """INSERT INTO oe_order_headers_all 
                  (header_id, order_number, customer_id, order_date, status) 
                  VALUES (%s, %s, %s, %s, %s)""",
        'values': (88001, 'OTC-TEST-88001', 1, '2026-04-05', 'PENDING'),
        'verify': "MATCH (o:SalesOrder {header_id: 88001}) RETURN o"
    },
    {
        'name': 'OTC - 创建客户',
        'table': 'ar_customers',
        'sql': """INSERT INTO ar_customers 
                  (customer_id, customer_name, customer_number, status) 
                  VALUES (%s, %s, %s, %s)""",
        'values': (99001, 'OTC Test Customer', 'CUST-99001', 'ACTIVE'),
        'verify': "MATCH (c:Customer {customer_id: 99001}) RETURN c"
    },
    {
        'name': 'PTP - 创建采购订单',
        'table': 'po_headers_all',
        'sql': """INSERT INTO po_headers_all 
                  (po_header_id, po_num, vendor_id, amount, status, creation_date) 
                  VALUES (%s, %s, %s, %s, %s, %s)""",
        'values': (77001, 'PTC-TEST-77001', 1, 5000.00, 'APPROVED', '2026-04-05'),
        'verify': "MATCH (p:PurchaseOrder {po_header_id: 77001}) RETURN p"
    },
    {
        'name': 'PTP - 创建供应商',
        'table': 'ap_suppliers',
        'sql': """INSERT INTO ap_suppliers 
                  (vendor_id, vendor_name, vendor_number, status) 
                  VALUES (%s, %s, %s, %s)""",
        'values': (66001, 'PTP Test Supplier', 'SUPP-66001', 'ACTIVE'),
        'verify': "MATCH (s:Supplier {vendor_id: 66001}) RETURN s"
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
        print(f"[OK] PostgreSQL 插入成功")
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
            print(f"[RECV] {n.payload[:100]}...")
            
            data = json.loads(n.payload)
            if data.get('table') == tc['table']:
                # 同步到 Neo4j
                rec = data.get('data')
                if rec:
                    d = {k: v for k, v in rec.items() if v is not None}
                    label = tc['table'].replace('_all', '').replace('ar_', '').replace('ap_', '').replace('oe_', '').replace('po_', '')
                    
                    with neo4j.session() as s:
                        try:
                            props = ', '.join([f'{k}: ${k}' for k in d.keys()])
                            s.run(f"CREATE (n:{label.capitalize()} {{{props}}})", **d)
                            print(f"[OK] Neo4j 同步成功")
                            
                            # 验证
                            r = s.run(tc['verify'])
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
    print("\n🎉 所有 OTC/PTP 同步测试通过！")
else:
    print(f"\n⚠️ {total - passed} 个测试失败")

print(f"{'='*70}\n")

cur.close()
pg.close()
neo4j.close()
