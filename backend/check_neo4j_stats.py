# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "admin123")

print("🔍 Neo4j 统计查询")
print("=" * 60)
print(f"URI: {NEO4J_URI}")
print(f"User: {NEO4J_USER}")

try:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    session = driver.session()
    
    # 节点标签
    result = session.run("CALL db.labels()")
    labels = [r["label"] for r in result]
    print(f"\n✅ 节点标签数：{len(labels)}")
    print(f"   标签列表：{labels[:10]}{'...' if len(labels) > 10 else ''}")
    
    # 关系类型
    result = session.run("CALL db.relationshipTypes()")
    types = [r["relationshipType"] for r in result]
    print(f"\n✅ 关系类型数：{len(types)}")
    print(f"   关系列表：{types}")
    
    # 总关系数
    result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
    count = result.single()["count"]
    print(f"\n✅ 总关系数：{count}")
    
    # 总节点数
    result = session.run("MATCH (n) RETURN count(n) as count")
    count = result.single()["count"]
    print(f"\n✅ 总节点数：{count}")
    
    driver.close()
    
except Exception as e:
    print(f"\n❌ 错误：{e}")

print("\n" + "=" * 60)
