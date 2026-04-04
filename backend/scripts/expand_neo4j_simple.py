# -*- coding: utf-8 -*-
"""Neo4j 关系扩展脚本 - 简化版"""
from neo4j import GraphDatabase

driver = GraphDatabase.driver('bolt://127.0.0.1:7687', auth=('neo4j', 'Tony1985'))

print('=' * 60)
print('Neo4j 关系扩展')
print('=' * 60)

with driver.session() as session:
    # AP 模块
    print('\n[AP 模块]')
    
    result = session.run("""
        MATCH (inv:Invoice), (po_line:POLine)
        WHERE inv.po_header_id = po_line.po_header_id
        AND NOT EXISTS((inv)-[:MATCHES_PO_LINE]->(po_line))
        WITH inv, po_line LIMIT 100
        CREATE (inv)-[:MATCHES_PO_LINE {match_type: 'PO'}]->(po_line)
        RETURN count(*) as count
    """)
    print(f'  OK Invoice-MATCHES_PO_LINE->POLine: {result.single()["count"]} 条')
    
    result = session.run("""
        MATCH (pay:Payment), (inv:Invoice)
        WHERE pay.invoice_id = inv.invoice_id
        AND NOT EXISTS((pay)-[:APPLIED_TO]->(inv))
        WITH pay, inv LIMIT 100
        CREATE (pay)-[:APPLIED_TO]->(inv)
        RETURN count(*) as count
    """)
    print(f'  OK Payment-APPLIED_TO->Invoice: {result.single()["count"]} 条')
    
    # PO 模块
    print('\n[PO 模块]')
    
    result = session.run("""
        MATCH (po_line:POLine), (po_dist:PODistribution)
        WHERE po_line.po_line_id = po_dist.po_line_id
        AND NOT EXISTS((po_line)-[:CONTAINS]->(po_dist))
        WITH po_line, po_dist LIMIT 200
        CREATE (po_line)-[:CONTAINS]->(po_dist)
        RETURN count(*) as count
    """)
    print(f'  OK POLine-CONTAINS->PODistribution: {result.single()["count"]} 条')
    
    # AR 模块
    print('\n[AR 模块]')
    
    result = session.run("""
        MATCH (cust:Customer), (trans:ARTransaction)
        WHERE cust.customer_id = trans.customer_id
        AND NOT EXISTS((cust)-[:HAS_TRANSACTION]->(trans))
        WITH cust, trans LIMIT 100
        CREATE (cust)-[:HAS_TRANSACTION]->(trans)
        RETURN count(*) as count
    """)
    print(f'  OK Customer-HAS_TRANSACTION->ARTransaction: {result.single()["count"]} 条')

# 验证
print('\n' + '=' * 60)
print('验证结果')
print('=' * 60)

with driver.session() as session:
    result = session.run('CALL db.relationshipTypes()')
    types = [r['relationshipType'] for r in result]
    print(f'\n关系类型数：{len(types)}')
    for t in types:
        print(f'  - {t}')

driver.close()
print('\nOK!')
