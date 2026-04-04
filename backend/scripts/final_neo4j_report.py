# -*- coding: utf-8 -*-
"""Neo4j 最终统计报告"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from neo4j import GraphDatabase

driver = GraphDatabase.driver('bolt://127.0.0.1:7687', auth=('neo4j', 'Tony1985'))

print("=" * 60)
print("Neo4j 知识图谱 - 最终统计报告")
print("=" * 60)

with driver.session() as session:
    # 节点统计
    result = session.run("MATCH (n) RETURN count(n) as count")
    total_nodes = result.single()["count"]
    print(f"\n【节点统计】")
    print(f"  总节点数：{total_nodes} 个")
    
    result = session.run("CALL db.labels()")
    labels = [r["label"] for r in result]
    print(f"  节点标签：{len(labels)} 种")
    
    # 关系统计
    result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
    total_rels = result.single()["count"]
    print(f"\n【关系统计】")
    print(f"  总关系数：{total_rels} 条")
    
    result = session.run("CALL db.relationshipTypes()")
    types = [r["relationshipType"] for r in result]
    print(f"  关系类型：{len(types)} 种 ⭐")
    
    # 关系类型列表
    print(f"\n【关系类型列表】({len(types)}种)")
    for i, t in enumerate(sorted(types), 1):
        print(f"  {i:2d}. {t}")
    
    # 每个关系类型的数量
    print(f"\n【关系分布 Top 10】")
    result = session.run("""
        MATCH ()-[r]->()
        RETURN type(r) as type, count(*) as count
        ORDER BY count DESC
        LIMIT 10
    """)
    for record in result:
        print(f"  {record['type']}: {record['count']} 条")

driver.close()
print("\n" + "=" * 60)
print("✅ 统计完成！")
print("=" * 60)
