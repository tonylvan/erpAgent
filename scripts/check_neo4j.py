from neo4j import GraphDatabase

driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'Tony1985'))
session = driver.session()

print("=== Neo4j 节点统计 ===")
result = session.run("MATCH (n) RETURN labels(n)[0] as label, count(*) as count ORDER BY count DESC")
for r in result:
    print(f"{r['label']}: {r['count']}")

result = session.run("MATCH ()-[r]->() RETURN count(r) as c")
print(f"\n总关系数：{result.single()['c']}")

result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(*) as count ORDER BY count DESC")
print("\n关系统计:")
for r in result:
    print(f"  {r['type']}: {r['count']}")

driver.close()
