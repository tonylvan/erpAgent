# -*- coding: utf-8 -*-
"""Neo4j 数据统计"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from neo4j import GraphDatabase

driver = GraphDatabase.driver('bolt://127.0.0.1:7687', auth=('neo4j', 'Tony1985'))

print("=" * 60)
print("Neo4j 数据统计 - RTR 检查")
print("=" * 60)

with driver.session() as session:
    print("\n【节点统计】")
    
    labels = ['Invoice', 'POLine', 'Payment', 'Customer', 'PurchaseOrder', 
              'PODistribution', 'ARTransaction', 'Supplier', 'Product', 'Order', 'Sale']
    
    for label in labels:
        result = session.run(f"MATCH (n:{label}) RETURN count(n) as c")
        count = result.single()['c']
        print(f"  {label}: {count} 个")
    
    print("\n【关系统计】")
    result = session.run("MATCH ()-[r]->() RETURN count(r) as c")
    print(f"  总关系数：{result.single()['c']} 条")
    
    result = session.run("CALL db.relationshipTypes()")
    types = [r['relationshipType'] for r in result]
    print(f"  关系类型：{len(types)} 种")

driver.close()

print("\n" + "=" * 60)
print("RTR 实时同步状态：❌ 未启用")
print("当前为离线批量同步模式")
print("=" * 60)
