# -*- coding: utf-8 -*-
"""
Neo4j 性能优化脚本
"""

from neo4j import GraphDatabase
import time

uri = 'bolt://localhost:7687'
auth = ('neo4j', 'Tony1985')

driver = GraphDatabase.driver(uri, auth=auth)

print('='*70)
print('Neo4j 性能优化')
print('='*70)

with driver.session() as session:
    
    # 1. 创建复合索引（针对常用查询模式）
    print('\n[1/5] 创建复合索引...')
    
    indexes_to_create = [
        # 发票查询优化
        ("CREATE INDEX IF NOT EXISTS FOR (i:Invoice) ON (i.vendor_id, i.payment_status)", "发票 - 供应商 + 状态"),
        
        # 采购订单查询优化
        ("CREATE INDEX IF NOT EXISTS FOR (p:PurchaseOrder) ON (p.vendor_id, p.status)", "采购单 - 供应商 + 状态"),
        
        # 客户查询优化
        ("CREATE INDEX IF NOT EXISTS FOR (c:Customer) ON (c.status)", "客户 - 状态"),
        
        # 供应商查询优化
        ("CREATE INDEX IF NOT EXISTS FOR (s:Supplier) ON (s.status)", "供应商 - 状态"),
        
        # 付款查询优化
        ("CREATE INDEX IF NOT EXISTS FOR (p:Payment) ON (p.payment_status)", "付款 - 状态"),
        
        # 销售订单查询优化
        ("CREATE INDEX IF NOT EXISTS FOR (s:SalesOrder) ON (s.customer_id, s.status)", "销售单 - 客户 + 状态"),
        
        # 应收交易查询优化
        ("CREATE INDEX IF NOT EXISTS FOR (t:ARTransaction) ON (t.customer_id, t.status)", "应收交易 - 客户 + 状态"),
    ]
    
    created_count = 0
    for index_sql, desc in indexes_to_create:
        try:
            session.run(index_sql)
            print(f'  [OK] {desc}')
            created_count += 1
        except Exception as e:
            print(f'  [WARN] {desc}: {str(e)[:50]}')
    
    print(f'  新建索引：{created_count}/{len(indexes_to_create)}')
    
    # 2. 创建全文索引（针对文本搜索）
    print('\n[2/5] 创建全文索引...')
    
    fulltext_indexes = [
        ("CREATE FULLTEXT INDEX supplier_name_fulltext IF NOT EXISTS FOR (s:Supplier) ON EACH [s.vendor_name, s.segment1]", "供应商名称搜索"),
        ("CREATE FULLTEXT INDEX customer_name_fulltext IF NOT EXISTS FOR (c:Customer) ON EACH [c.customer_name, c.customer_number]", "客户名称搜索"),
        ("CREATE FULLTEXT INDEX invoice_num_fulltext IF NOT EXISTS FOR (i:Invoice) ON EACH [i.invoice_num]", "发票号搜索"),
        ("CREATE FULLTEXT INDEX po_number_fulltext IF NOT EXISTS FOR (p:PurchaseOrder) ON EACH [p.segment1]", "采购单号搜索"),
    ]
    
    for index_sql, desc in fulltext_indexes:
        try:
            session.run(index_sql)
            print(f'  [OK] {desc}')
        except Exception as e:
            print(f'  [WARN] {desc}: {str(e)[:50]}')
    
    # 3. 优化数据库配置
    print('\n[3/5] 优化数据库配置...')
    
    config_queries = [
        ("CALL dbms.setConfigValue('dbms.memory.heap.initial_size', '512M')", "堆内存初始大小"),
        ("CALL dbms.setConfigValue('dbms.memory.heap.max_size', '2G')", "堆内存最大值"),
        ("CALL dbms.setConfigValue('dbms.memory.pagecache.size', '1G')", "页面缓存大小"),
    ]
    
    for config_sql, desc in config_queries:
        try:
            session.run(config_sql)
            print(f'  [OK] {desc}')
        except Exception as e:
            print(f'  [WARN] {desc}: 需要 Neo4j 管理员权限')
    
    # 4. 性能基准测试
    print('\n[4/5] 性能基准测试...')
    
    test_queries = [
        ("MATCH (i:Invoice) WHERE i.invoice_id = 1 RETURN i", "单节点查询"),
        ("MATCH (i:Invoice) WHERE i.payment_status = 'PENDING' RETURN i LIMIT 100", "状态过滤"),
        ("MATCH (s:Supplier)-[:SUPPLIES_INVOICE]->(i:Invoice) RETURN s, i LIMIT 100", "关系查询"),
        ("MATCH path = (s:Supplier)-[*2]-(i:Invoice) RETURN path LIMIT 50", "多跳查询"),
        ("MATCH (i:Invoice) RETURN i ORDER BY i.invoice_amount DESC LIMIT 100", "排序查询"),
    ]
    
    print('\n  查询性能测试:')
    for query, desc in test_queries:
        start = time.time()
        result = session.run(query)
        _ = list(result)
        elapsed = (time.time() - start) * 1000
        status = '[OK]' if elapsed < 100 else '[WARN]'
        print(f'  {status} {desc}: {elapsed:.1f}ms')
    
    # 5. 统计信息
    print('\n[5/5] 优化后统计...')
    
    # 索引总数
    indexes = session.run('SHOW INDEXES')
    index_count = len(list(indexes))
    
    # 节点和关系数
    stats = session.run('MATCH (n) RETURN count(n) as nodes')
    node_count = stats.single()['nodes']
    
    stats = session.run('MATCH ()-[r]->() RETURN count(r) as rels')
    rel_count = stats.single()['rels']
    
    print(f'  总索引数：{index_count}')
    print(f'  节点总数：{node_count:,}')
    print(f'  关系总数：{rel_count:,}')

print('\n' + '='*70)
print('Neo4j 性能优化完成！')
print('='*70)

driver.close()
