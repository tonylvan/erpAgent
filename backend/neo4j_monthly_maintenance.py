# Neo4j 索引维护脚本
# 建议每月执行一次

from neo4j import GraphDatabase

uri = 'bolt://localhost:7687'
auth = ('neo4j', 'Tony1985')

driver = GraphDatabase.driver(uri, auth=auth)

with driver.session() as session:
    # 1. 更新统计信息
    print("更新统计信息...")
    session.run("CALL db.stats.update()")
    
    # 2. 检查索引健康状态
    print("检查索引状态...")
    indexes = session.run("SHOW INDEXES")
    for idx in indexes:
        print(f"  {idx[1]}: {idx[3] if len(idx) > 3 else 'ONLINE'}")
    
    # 3. 清理废弃索引
    print("清理废弃索引...")
    # 注意：生产环境谨慎使用
    # session.run("DROP INDEX index_name")
    
    # 4. 性能测试
    print("性能测试...")
    import time
    
    test_queries = [
        "MATCH (n) RETURN count(n)",
        "MATCH ()-[r]->() RETURN count(r)",
        "MATCH (i:Invoice) WHERE i.payment_status = 'PENDING' RETURN i LIMIT 100"
    ]
    
    for query in test_queries:
        start = time.time()
        result = session.run(query)
        _ = list(result)
        elapsed = (time.time() - start) * 1000
        print(f"  {query[:50]}: {elapsed:.1f}ms")

driver.close()
print("维护完成！")
