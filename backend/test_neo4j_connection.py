from neo4j import GraphDatabase
import os

# Neo4j 配置
NEO4J_URI = "bolt://localhost:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "Tony1985"  # 从.env 读取

print("=" * 60)
print("Neo4j 连接测试")
print("=" * 60)

try:
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    print(f"[OK] 已连接：{NEO4J_URI}")
    
    with driver.session() as session:
        # 测试查询
        result = session.run("MATCH (n) RETURN count(n) as total")
        total = result.single()["total"]
        print(f"[OK] 节点总数：{total}")
        
        # 检查是否有数据
        if total == 0:
            print("[WARN] 数据库为空，需要初始化数据")
        else:
            print(f"[OK] 数据库中有 {total} 个节点")
        
        # 检查标签
        result = session.run("CALL db.labels()")
        labels = [record["label"] for record in result]
        print(f"[OK] 标签列表：{labels}")
    
    driver.close()
    print("\n[SUCCESS] Neo4j 连接正常！")
    
except Exception as e:
    print(f"[ERROR] 连接失败：{e}")
    print("\n可能的原因:")
    print("1. Neo4j 服务未启动")
    print("2. 密码错误（默认密码：neo4j/neo4j 或 admin123）")
    print("3. 防火墙阻止连接")
