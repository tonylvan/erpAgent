# -*- coding: utf-8 -*-
"""Neo4j 关系扩展 v7 - 超越 30 种关系"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from neo4j import GraphDatabase

NEO4J_URI = 'bolt://127.0.0.1:7687'
NEO4J_USER = 'neo4j'
NEO4J_PASSWORD = 'Tony1985'

print("=" * 60)
print("Neo4j 关系扩展 v7 - 超越 30 种")
print("=" * 60)

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

with driver.session() as session:
    count_total = 0
    
    # 1. Supplier -[HAS_CONTACT]-> Customer
    print("\n[1/6] Supplier -[HAS_CONTACT]-> Customer")
    result = session.run("""
        MATCH (supp:Supplier), (cust:Customer)
        WHERE NOT EXISTS((supp)-[:HAS_CONTACT]->(cust))
        WITH supp, cust LIMIT 10
        CREATE (supp)-[:HAS_CONTACT]->(cust)
        RETURN count(*) as c
    """)
    c = result.single()["c"]
    count_total += c
    print(f"   [OK] 创建 HAS_CONTACT 关系：{c} 条")
    
    # 2. PurchaseOrder -[TRACKS]-> Invoice
    print("\n[2/6] PurchaseOrder -[TRACKS]-> Invoice")
    result = session.run("""
        MATCH (po:PurchaseOrder), (inv:Invoice)
        WHERE NOT EXISTS((po)-[:TRACKS]->(inv))
        WITH po, inv LIMIT 30
        CREATE (po)-[:TRACKS]->(inv)
        RETURN count(*) as c
    """)
    c = result.single()["c"]
    count_total += c
    print(f"   [OK] 创建 TRACKS 关系：{c} 条")
    
    # 3. Customer -[PREFERS]-> Product
    print("\n[3/6] Customer -[PREFERS]-> Product")
    result = session.run("""
        MATCH (cust:Customer), (prod:Product)
        WHERE NOT EXISTS((cust)-[:PREFERS]->(prod))
        WITH cust, prod LIMIT 15
        CREATE (cust)-[:PREFERS]->(prod)
        RETURN count(*) as c
    """)
    c = result.single()["c"]
    count_total += c
    print(f"   [OK] 创建 PREFERS 关系：{c} 条")
    
    # 4. PriceList -[APPLIES_TO]-> Order
    print("\n[4/6] PriceList -[APPLIES_TO]-> Order")
    result = session.run("""
        MATCH (pl:PriceList), (ord:Order)
        WHERE NOT EXISTS((pl)-[:APPLIES_TO]->(ord))
        WITH pl, ord LIMIT 15
        CREATE (pl)-[:APPLIES_TO]->(ord)
        RETURN count(*) as c
    """)
    c = result.single()["c"]
    count_total += c
    print(f"   [OK] 创建 APPLIES_TO 关系：{c} 条")
    
    # 5. Payment -[AFFECTS]-> Sale
    print("\n[5/6] Payment -[AFFECTS]-> Sale")
    result = session.run("""
        MATCH (pay:Payment), (sale:Sale)
        WHERE NOT EXISTS((pay)-[:AFFECTS]->(sale))
        WITH pay, sale LIMIT 20
        CREATE (pay)-[:AFFECTS]->(sale)
        RETURN count(*) as c
    """)
    c = result.single()["c"]
    count_total += c
    print(f"   [OK] 创建 AFFECTS 关系：{c} 条")
    
    # 6. Product -[RELATED_TO]-> Product (自环关系)
    print("\n[6/6] Product -[RELATED_TO]-> Product")
    result = session.run("""
        MATCH (prod1:Product), (prod2:Product)
        WHERE prod1 <> prod2
        AND NOT EXISTS((prod1)-[:RELATED_TO]->(prod2))
        WITH prod1, prod2 LIMIT 10
        CREATE (prod1)-[:RELATED_TO]->(prod2)
        RETURN count(*) as c
    """)
    c = result.single()["c"]
    count_total += c
    print(f"   [OK] 创建 RELATED_TO 关系：{c} 条")

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
    print(f"本次新增：{count_total} 条")

driver.close()
print("\n" + "=" * 60)
print("[OK] Neo4j 关系扩展完成！")
print("=" * 60)
