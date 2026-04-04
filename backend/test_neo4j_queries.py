from neo4j import GraphDatabase

NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "Tony1985"

print("=" * 60)
print("Neo4j 智能问数查询测试")
print("=" * 60)

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

with driver.session() as session:
    # 测试 1: 销售趋势查询
    print("\n[测试 1] 销售趋势查询...")
    try:
        result = session.run("""
        MATCH (s:Sale)-[:HAS_TIME]->(t:Time)
        WHERE t.week = date().week
        RETURN t.day as day, sum(s.amount) as amount
        ORDER BY t.day
        """)
        records = [record.data() for record in result]
        if records:
            print(f"[OK] 查询到 {len(records)} 条销售记录")
            for r in records[:3]:
                print(f"  - {r}")
        else:
            print("[WARN] 没有本周销售数据")
    except Exception as e:
        print(f"[ERROR] 销售趋势查询失败：{e}")
    
    # 测试 2: 客户排行查询
    print("\n[测试 2] 客户排行查询...")
    try:
        result = session.run("""
        MATCH (c:Customer)-[:PURCHASED]->(o:Order)
        RETURN c.name as customer, sum(o.amount) as total
        ORDER BY total DESC
        LIMIT 10
        """)
        records = [record.data() for record in result]
        if records:
            print(f"[OK] 查询到 {len(records)} 个客户")
            for r in records[:3]:
                print(f"  - {r}")
        else:
            print("[WARN] 没有客户数据")
    except Exception as e:
        print(f"[ERROR] 客户排行查询失败：{e}")
    
    # 测试 3: 库存查询
    print("\n[测试 3] 库存预警查询...")
    try:
        result = session.run("""
        MATCH (p:Product)
        WHERE p.stock < p.threshold
        RETURN p.code as code, p.name as name, p.stock as stock, p.threshold as threshold
        ORDER BY p.stock ASC
        """)
        records = [record.data() for record in result]
        if records:
            print(f"[OK] 查询到 {len(records)} 个预警商品")
            for r in records[:3]:
                print(f"  - {r}")
        else:
            print("[WARN] 没有库存预警数据")
    except Exception as e:
        print(f"[ERROR] 库存查询失败：{e}")
    
    # 测试 4: 付款单查询
    print("\n[测试 4] 付款单查询...")
    try:
        result = session.run("""
        MATCH (pay:Payment)
        WHERE pay.date >= date() - duration({days: 7})
        RETURN pay.id as id, pay.customer as customer, pay.amount as amount, pay.date as date
        ORDER BY pay.amount DESC
        """)
        records = [record.data() for record in result]
        if records:
            print(f"[OK] 查询到 {len(records)} 条付款记录")
            for r in records[:3]:
                print(f"  - {r}")
        else:
            print("[WARN] 没有本周付款数据")
    except Exception as e:
        print(f"[ERROR] 付款单查询失败：{e}")

driver.close()
print("\n[SUCCESS] Neo4j 查询测试完成！")
