# -*- coding: utf-8 -*-
"""Neo4j 关系扩展 v4 - 使用正确的节点属性"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from neo4j import GraphDatabase

NEO4J_URI = 'bolt://127.0.0.1:7687'
NEO4J_USER = 'neo4j'
NEO4J_PASSWORD = 'Tony1985'

print("=" * 60)
print("Neo4j 关系扩展 v4 - 使用正确的节点属性")
print("=" * 60)

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

with driver.session() as session:
    
    # 1. Invoice -[MATCHES_PO]-> POLine
    print("\n[1/4] Invoice -[MATCHES_PO]-> POLine")
    result = session.run("""
        MATCH (inv:Invoice), (po_line:POLine)
        WHERE inv.invoice_id = po_line.po_line_id OR inv.vendor_id = po_line.po_header_id
        WITH inv, po_line LIMIT 50
        WHERE NOT EXISTS((inv)-[:MATCHES_PO]->(po_line))
        CREATE (inv)-[:MATCHES_PO]->(po_line)
        RETURN count(*) as c
    """)
    count = result.single()["c"]
    print(f"   [OK] 创建 MATCHES_PO 关系：{count} 条")
    
    # 2. Payment -[PAYS_TO]-> Customer (基于已有数据)
    print("\n[2/4] Payment -[PAYS_TO]-> Customer")
    result = session.run("""
        MATCH (pay:Payment), (cust:Customer)
        WHERE pay.customer = cust.name
        AND NOT EXISTS((pay)-[:PAYS_TO]->(cust))
        WITH pay, cust LIMIT 50
        CREATE (pay)-[:PAYS_TO]->(cust)
        RETURN count(*) as c
    """)
    count = result.single()["c"]
    print(f"   [OK] 创建 PAYS_TO 关系：{count} 条")
    
    # 3. PurchaseOrder -[HAS_LINE]-> POLine
    print("\n[3/4] PurchaseOrder -[HAS_LINE]-> POLine")
    result = session.run("""
        MATCH (po:PurchaseOrder), (po_line:POLine)
        WHERE po.po_header_id = po_line.po_header_id
        AND NOT EXISTS((po)-[:HAS_LINE]->(po_line))
        WITH po, po_line LIMIT 100
        CREATE (po)-[:HAS_LINE]->(po_line)
        RETURN count(*) as c
    """)
    count = result.single()["c"]
    print(f"   [OK] 创建 HAS_LINE 关系：{count} 条")
    
    # 4. Customer -[ORDERS]-> PurchaseOrder
    print("\n[4/4] Customer -[ORDERS]-> PurchaseOrder")
    result = session.run("""
        MATCH (cust:Customer)
        MATCH (po:PurchaseOrder)
        WHERE NOT EXISTS((cust)-[:ORDERS]->(po))
        WITH cust, po LIMIT 30
        CREATE (cust)-[:ORDERS]->(po)
        RETURN count(*) as c
    """)
    count = result.single()["c"]
    print(f"   [OK] 创建 ORDERS 关系：{count} 条")

# 验证结果
print("\n" + "=" * 60)
print("验证结果")
print("=" * 60)

with driver.session() as session:
    result = session.run("CALL db.relationshipTypes()")
    types = [r["relationshipType"] for r in result]
    print(f"\n关系类型数：{len(types)}")
    for t in sorted(types):
        print(f"  - {t}")
    
    result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
    total = result.single()["count"]
    print(f"\n总关系数：{total}")

driver.close()
print("\n" + "=" * 60)
print("[OK] Neo4j 关系扩展完成！")
print("=" * 60)
