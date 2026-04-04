# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
from neo4j import GraphDatabase

driver = GraphDatabase.driver('bolt://127.0.0.1:7687', auth=('neo4j', 'Tony1985'))

print("=" * 60)
print("Neo4j 节点属性检查 v2")
print("=" * 60)

with driver.session() as session:
    # 检查 Supplier 节点
    print("\n[Supplier] 节点样例 (前 3 个):")
    result = session.run("""
        MATCH (supp:Supplier) 
        RETURN supp LIMIT 3
    """)
    for record in result:
        node = record["supp"]
        print(f"  Properties: {dict(node)}")
    
    # 检查 Invoice 节点
    print("\n[Invoice] 节点样例 (前 3 个):")
    result = session.run("""
        MATCH (inv:Invoice) 
        RETURN inv LIMIT 3
    """)
    for record in result:
        node = record["inv"]
        print(f"  Properties: {dict(node)}")

driver.close()
print("\n" + "=" * 60)
