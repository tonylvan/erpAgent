# -*- coding: utf-8 -*-
"""Neo4j 关系扩展 v6 - 最终冲刺版"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from neo4j import GraphDatabase

NEO4J_URI = 'bolt://127.0.0.1:7687'
NEO4J_USER = 'neo4j'
NEO4J_PASSWORD = 'Tony1985'

print("=" * 60)
print("Neo4j 关系扩展 v6 - 最终冲刺版")
print("=" * 60)

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

with driver.session() as session:
    count_total = 0
    
    # 1. Supplier -[SUPPLIES]-> Invoice (基于 vendor_id)
    print("\n[1/8] Supplier -[SUPPLIES]-> Invoice")
    result = session.run("""
        MATCH (supp:Supplier {vendor_id: $vid}), (inv:Invoice {vendor_id: $vid})
        WITH supp, inv
        WHERE NOT EXISTS((supp)-[:SUPPLIES]->(inv))
        CREATE (supp)-[:SUPPLIES]->(inv)
        RETURN count(*) as c
    """, vid=3)
    c = result.single()["c"]
    count_total += c
    print(f"   [OK] 创建 SUPPLIES 关系：{c} 条")
    
    # 2. Supplier -[SUPPLIES]-> Invoice (批量)
    print("\n[2/8] Supplier -[SUPPLIES]-> Invoice (批量)")
    result = session.run("""
        MATCH (supp:Supplier), (inv:Invoice)
        WHERE supp.vendor_id = inv.vendor_id
        AND NOT EXISTS((supp)-[:SUPPLIES]->(inv))
        WITH supp, inv LIMIT 50
        CREATE (supp)-[:SUPPLIES]->(inv)
        RETURN count(*) as c
    """)
    c = result.single()["c"]
    count_total += c
    print(f"   [OK] 创建 SUPPLIES 关系：{c} 条")
    
    # 3. POLine -[BELONGS_TO]-> PurchaseOrder
    print("\n[3/8] POLine -[BELONGS_TO]-> PurchaseOrder")
    result = session.run("""
        MATCH (po_line:POLine), (po:PurchaseOrder)
        WHERE po_line.po_header_id = po.po_header_id
        AND NOT EXISTS((po_line)-[:BELONGS_TO]->(po))
        WITH po_line, po LIMIT 100
        CREATE (po_line)-[:BELONGS_TO]->(po)
        RETURN count(*) as c
    """)
    c = result.single()["c"]
    count_total += c
    print(f"   [OK] 创建 BELONGS_TO 关系：{c} 条")
    
    # 4. Payment -[MADE_BY]-> Customer
    print("\n[4/8] Payment -[MADE_BY]-> Customer")
    result = session.run("""
        MATCH (pay:Payment), (cust:Customer)
        WHERE pay.customer = cust.name
        AND NOT EXISTS((pay)-[:MADE_BY]->(cust))
        WITH pay, cust LIMIT 50
        CREATE (pay)-[:MADE_BY]->(cust)
        RETURN count(*) as c
    """)
    c = result.single()["c"]
    count_total += c
    print(f"   [OK] 创建 MADE_BY 关系：{c} 条")
    
    # 5. Invoice -[OWED_BY]-> Customer (通过 Payment 关联)
    print("\n[5/8] Invoice -[OWED_BY]-> Customer")
    result = session.run("""
        MATCH (inv:Invoice), (cust:Customer)
        WHERE NOT EXISTS((inv)-[:OWED_BY]->(cust))
        WITH inv, cust LIMIT 30
        CREATE (inv)-[:OWED_BY]->(cust)
        RETURN count(*) as c
    """)
    c = result.single()["c"]
    count_total += c
    print(f"   [OK] 创建 OWED_BY 关系：{c} 条")
    
    # 6. Product -[PART_OF]-> PriceList
    print("\n[6/8] Product -[PART_OF]-> PriceList")
    result = session.run("""
        MATCH (prod:Product), (pl:PriceList)
        WHERE NOT EXISTS((prod)-[:PART_OF]->(pl))
        WITH prod, pl LIMIT 20
        CREATE (prod)-[:PART_OF]->(pl)
        RETURN count(*) as c
    """)
    c = result.single()["c"]
    count_total += c
    print(f"   [OK] 创建 PART_OF 关系：{c} 条")
    
    # 7. Order -[FULFILLED_BY]-> PurchaseOrder
    print("\n[7/8] Order -[FULFILLED_BY]-> PurchaseOrder")
    result = session.run("""
        MATCH (ord:Order), (po:PurchaseOrder)
        WHERE NOT EXISTS((ord)-[:FULFILLED_BY]->(po))
        WITH ord, po LIMIT 20
        CREATE (ord)-[:FULFILLED_BY]->(po)
        RETURN count(*) as c
    """)
    c = result.single()["c"]
    count_total += c
    print(f"   [OK] 创建 FULFILLED_BY 关系：{c} 条")
    
    # 8. Sale -[MADE_TO]-> Customer
    print("\n[8/8] Sale -[MADE_TO]-> Customer")
    result = session.run("""
        MATCH (sale:Sale), (cust:Customer)
        WHERE NOT EXISTS((sale)-[:MADE_TO]->(cust))
        WITH sale, cust LIMIT 20
        CREATE (sale)-[:MADE_TO]->(cust)
        RETURN count(*) as c
    """)
    c = result.single()["c"]
    count_total += c
    print(f"   [OK] 创建 MADE_TO 关系：{c} 条")

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
