# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
from neo4j import GraphDatabase

driver = GraphDatabase.driver('bolt://127.0.0.1:7687', auth=('neo4j', 'Tony1985'))

print("=" * 60)
print("Neo4j 节点标签统计")
print("=" * 60)

with driver.session() as session:
    # 获取所有标签及其数量
    result = session.run("""
        CALL db.labels() YIELD label
        MATCH (n) WHERE label IN labels(n)
        RETURN label, count(n) as count
        ORDER BY count DESC
    """)
    
    print("\n节点标签分布:")
    for record in result:
        print(f"  {record['label']}: {record['count']} 个")
    
    # 检查还有哪些节点没有关系
    result = session.run("""
        MATCH (n)
        WHERE NOT (n)-->()
        RETURN labels(n)[0] as label, count(n) as count
        ORDER BY count DESC
        LIMIT 10
    """)
    
    print("\n孤立节点 (没有出边):")
    for record in result:
        print(f"  {record['label']}: {record['count']} 个")

driver.close()
print("\n" + "=" * 60)
