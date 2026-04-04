# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
from neo4j import GraphDatabase

driver = GraphDatabase.driver('bolt://127.0.0.1:7687', auth=('neo4j', 'Tony1985'))

print("=" * 60)
print("Neo4j 节点属性检查")
print("=" * 60)

with driver.session() as session:
    # 检查 Invoice 节点
    print("\n[Invoice] 节点样例:")
    result = session.run("""
        MATCH (inv:Invoice) 
        RETURN inv LIMIT 1
    """)
    record = result.single()
    if record:
        node = record["inv"]
        print(f"  ID: {node.id}")
        print(f"  Labels: {node.labels}")
        print(f"  Properties: {dict(node)}")
    
    # 检查 POLine 节点
    print("\n[POLine] 节点样例:")
    result = session.run("""
        MATCH (po:POLine) 
        RETURN po LIMIT 1
    """)
    record = result.single()
    if record:
        node = record["po"]
        print(f"  Properties: {dict(node)}")
    
    # 检查 Payment 节点
    print("\n[Payment] 节点样例:")
    result = session.run("""
        MATCH (pay:Payment) 
        RETURN pay LIMIT 1
    """)
    record = result.single()
    if record:
        node = record["pay"]
        print(f"  Properties: {dict(node)}")
    
    # 检查 Customer 节点
    print("\n[Customer] 节点样例:")
    result = session.run("""
        MATCH (cust:Customer) 
        RETURN cust LIMIT 1
    """)
    record = result.single()
    if record:
        node = record["cust"]
        print(f"  Properties: {dict(node)}")
    
    # 检查 PurchaseOrder 节点
    print("\n[PurchaseOrder] 节点样例:")
    result = session.run("""
        MATCH (po:PurchaseOrder) 
        RETURN po LIMIT 1
    """)
    record = result.single()
    if record:
        node = record["po"]
        print(f"  Properties: {dict(node)}")

driver.close()
print("\n" + "=" * 60)
