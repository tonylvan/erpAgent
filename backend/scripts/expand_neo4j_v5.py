# -*- coding: utf-8 -*-
"""Neo4j 关系扩展 v5 - 终极扩展版"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from neo4j import GraphDatabase

NEO4J_URI = 'bolt://127.0.0.1:7687'
NEO4J_USER = 'neo4j'
NEO4J_PASSWORD = 'Tony1985'

print("=" * 60)
print("Neo4j 关系扩展 v5 - 终极扩展版")
print("=" * 60)

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

with driver.session() as session:
    count_total = 0
    
    # ===== AP 模块 =====
    print("\n【AP 模块】")
    
    # 1. Supplier -[SUPPLIES]-> Invoice
    result = session.run("""
        MATCH (supp:Supplier), (inv:Invoice)
        WHERE supp.id = inv.vendor_id
        AND NOT EXISTS((supp)-[:SUPPLIES]->(inv))
        WITH supp, inv LIMIT 50
        CREATE (supp)-[:SUPPLIES]->(inv)
        RETURN count(*) as c
    """)
    c = result.single()["c"]
    count_total += c
    print(f"  [OK] Supplier -[SUPPLIES]-> Invoice: {c} 条")
    
    # 2. Invoice -[HAS_STATUS]-> Payment (基于状态)
    result = session.run("""
        MATCH (inv:Invoice), (pay:Payment)
        WHERE inv.status = 'PARTIALLY PAID' OR inv.status = 'FULLY PAID'
        AND NOT EXISTS((inv)-[:HAS_STATUS]->(pay))
        WITH inv, pay LIMIT 30
        CREATE (inv)-[:HAS_STATUS]->(pay)
        RETURN count(*) as c
    """)
    c = result.single()["c"]
    count_total += c
    print(f"  [OK] Invoice -[HAS_STATUS]-> Payment: {c} 条")
    
    # ===== PO 模块 =====
    print("\n【PO 模块】")
    
    # 3. Supplier -[FULFILLS]-> PurchaseOrder
    result = session.run("""
        MATCH (supp:Supplier), (po:PurchaseOrder)
        WHERE NOT EXISTS((supp)-[:FULFILLS]->(po))
        WITH supp, po LIMIT 30
        CREATE (supp)-[:FULFILLS]->(po)
        RETURN count(*) as c
    """)
    c = result.single()["c"]
    count_total += c
    print(f"  [OK] Supplier -[FULFILLS]-> PurchaseOrder: {c} 条")
    
    # 4. POLine -[HAS_PRICE]-> PriceList
    result = session.run("""
        MATCH (po_line:POLine), (pl:PriceList)
        WHERE NOT EXISTS((po_line)-[:HAS_PRICE]->(pl))
        WITH po_line, pl LIMIT 50
        CREATE (po_line)-[:HAS_PRICE]->(pl)
        RETURN count(*) as c
    """)
    c = result.single()["c"]
    count_total += c
    print(f"  [OK] POLine -[HAS_PRICE]-> PriceList: {c} 条")
    
    # ===== AR 模块 =====
    print("\n【AR 模块】")
    
    # 5. Customer -[PLACES]-> Order
    result = session.run("""
        MATCH (cust:Customer), (ord:Order)
        WHERE NOT EXISTS((cust)-[:PLACES]->(ord))
        WITH cust, ord LIMIT 20
        CREATE (cust)-[:PLACES]->(ord)
        RETURN count(*) as c
    """)
    c = result.single()["c"]
    count_total += c
    print(f"  [OK] Customer -[PLACES]-> Order: {c} 条")
    
    # 6. Order -[CONTAINS]-> Product
    result = session.run("""
        MATCH (ord:Order), (prod:Product)
        WHERE NOT EXISTS((ord)-[:CONTAINS]->(prod))
        WITH ord, prod LIMIT 30
        CREATE (ord)-[:CONTAINS]->(prod)
        RETURN count(*) as c
    """)
    c = result.single()["c"]
    count_total += c
    print(f"  [OK] Order -[CONTAINS]-> Product: {c} 条")
    
    # 7. Customer -[BUYS]-> Product
    result = session.run("""
        MATCH (cust:Customer), (prod:Product)
        WHERE NOT EXISTS((cust)-[:BUYS]->(prod))
        WITH cust, prod LIMIT 20
        CREATE (cust)-[:BUYS]->(prod)
        RETURN count(*) as c
    """)
    c = result.single()["c"]
    count_total += c
    print(f"  [OK] Customer -[BUYS]-> Product: {c} 条")
    
    # ===== INV 模块 =====
    print("\n【INV 模块】")
    
    # 8. Product -[STORED_IN]-> PurchaseOrder
    result = session.run("""
        MATCH (prod:Product), (po:PurchaseOrder)
        WHERE NOT EXISTS((prod)-[:STORED_IN]->(po))
        WITH prod, po LIMIT 20
        CREATE (prod)-[:STORED_IN]->(po)
        RETURN count(*) as c
    """)
    c = result.single()["c"]
    count_total += c
    print(f"  [OK] Product -[STORED_IN]-> PurchaseOrder: {c} 条")
    
    # ===== 时间关系 =====
    print("\n【时间关系】")
    
    # 9. Payment -[OCCURS_ON]-> Time
    result = session.run("""
        MATCH (pay:Payment), (t:Time)
        WHERE NOT EXISTS((pay)-[:OCCURS_ON]->(t))
        WITH pay, t LIMIT 30
        CREATE (pay)-[:OCCURS_ON]->(t)
        RETURN count(*) as c
    """)
    c = result.single()["c"]
    count_total += c
    print(f"  [OK] Payment -[OCCURS_ON]-> Time: {c} 条")
    
    # 10. Invoice -[OCCURS_ON]-> Time
    result = session.run("""
        MATCH (inv:Invoice), (t:Time)
        WHERE NOT EXISTS((inv)-[:OCCURS_ON]->(t))
        WITH inv, t LIMIT 30
        CREATE (inv)-[:OCCURS_ON]->(t)
        RETURN count(*) as c
    """)
    c = result.single()["c"]
    count_total += c
    print(f"  [OK] Invoice -[OCCURS_ON]-> Time: {c} 条")
    
    # 11. PurchaseOrder -[OCCURS_ON]-> Time
    result = session.run("""
        MATCH (po:PurchaseOrder), (t:Time)
        WHERE NOT EXISTS((po)-[:OCCURS_ON]->(t))
        WITH po, t LIMIT 20
        CREATE (po)-[:OCCURS_ON]->(t)
        RETURN count(*) as c
    """)
    c = result.single()["c"]
    count_total += c
    print(f"  [OK] PurchaseOrder -[OCCURS_ON]-> Time: {c} 条")
    
    # ===== 销售模块 =====
    print("\n【销售模块】")
    
    # 12. Customer -[GENERATES]-> Sale
    result = session.run("""
        MATCH (cust:Customer), (sale:Sale)
        WHERE NOT EXISTS((cust)-[:GENERATES]->(sale))
        WITH cust, sale LIMIT 20
        CREATE (cust)-[:GENERATES]->(sale)
        RETURN count(*) as c
    """)
    c = result.single()["c"]
    count_total += c
    print(f"  [OK] Customer -[GENERATES]-> Sale: {c} 条")
    
    # 13. Product -[SOLD_IN]-> Sale
    result = session.run("""
        MATCH (prod:Product), (sale:Sale)
        WHERE NOT EXISTS((prod)-[:SOLD_IN]->(sale))
        WITH prod, sale LIMIT 20
        CREATE (prod)-[:SOLD_IN]->(sale)
        RETURN count(*) as c
    """)
    c = result.single()["c"]
    count_total += c
    print(f"  [OK] Product -[SOLD_IN]-> Sale: {c} 条")
    
    # 14. Sale -[CONTAINS]-> Product
    result = session.run("""
        MATCH (sale:Sale), (prod:Product)
        WHERE NOT EXISTS((sale)-[:CONTAINS]->(prod))
        WITH sale, prod LIMIT 20
        CREATE (sale)-[:CONTAINS]->(prod)
        RETURN count(*) as c
    """)
    c = result.single()["c"]
    count_total += c
    print(f"  [OK] Sale -[CONTAINS]-> Product: {c} 条")
    
    # ===== 财务模块 =====
    print("\n【财务模块】")
    
    # 15. Payment -[USES]-> PriceList
    result = session.run("""
        MATCH (pay:Payment), (pl:PriceList)
        WHERE NOT EXISTS((pay)-[:USES]->(pl))
        WITH pay, pl LIMIT 20
        CREATE (pay)-[:USES]->(pl)
        RETURN count(*) as c
    """)
    c = result.single()["c"]
    count_total += c
    print(f"  [OK] Payment -[USES]-> PriceList: {c} 条")

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
