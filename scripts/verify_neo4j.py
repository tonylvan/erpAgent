# -*- coding: utf-8 -*-
"""Verify Neo4j data sync"""

from neo4j import GraphDatabase

driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'Tony1985'))

with driver.session() as session:
    print("=" * 60)
    print("=== Neo4j 节点统计 ===")
    print("=" * 60)
    result = session.run("MATCH (n) RETURN labels(n)[0] as label, count(*) as count ORDER BY count DESC")
    total_nodes = 0
    for record in result:
        label = record['label'] or 'Unknown'
        count = record['count']
        total_nodes += count
        print(f"{label:25s}: {count:5d} 个节点")
    
    print("\n" + "=" * 60)
    print(f"节点总数：{total_nodes}")
    print("=" * 60)
    
    print("\n=== Neo4j 关系统计 ===")
    print("=" * 60)
    result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(*) as count ORDER BY count DESC")
    total_rels = 0
    for record in result:
        rel_type = record['type']
        count = record['count']
        total_rels += count
        print(f"{rel_type:25s}: {count:5d} 条关系")
    
    print("\n" + "=" * 60)
    print(f"关系总数：{total_rels}")
    print("=" * 60)
    
    # Sample relationships
    print("\n=== 关系示例 ===")
    result = session.run("""
        MATCH (n)-[r]->(m) 
        RETURN labels(n)[0] as from, type(r) as rel, labels(m)[0] as to, count(*) as count
        ORDER BY count DESC
        LIMIT 10
    """)
    for record in result:
        print(f"({record['from']})-[:{record['rel']}]->({record['to']}): {record['count']} 条")

driver.close()
print("\n验证完成！")
