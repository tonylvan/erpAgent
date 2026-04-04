# -*- coding: utf-8 -*-
"""PostgreSQL 数据同步到 Neo4j - 带外键字段"""
import psycopg2
from neo4j import GraphDatabase

# 连接配置
PG_CONFIG = {
    'host': 'localhost',
    'database': 'erp',
    'user': 'postgres',
    'password': 'postgres'
}

NEO4J_CONFIG = {
    'uri': 'bolt://127.0.0.1:7687',
    'user': 'neo4j',
    'password': 'Tony1985'
}

print('=' * 60)
print('PostgreSQL → Neo4j 数据同步（带外键）')
print('=' * 60)

# 连接数据库
pg_conn = psycopg2.connect(**PG_CONFIG)
pg_cur = pg_conn.cursor()
neo4j_driver = GraphDatabase.driver(NEO4J_CONFIG['uri'], auth=(NEO4J_CONFIG['user'], NEO4J_CONFIG['password']))

print('\n[1/4] 同步 Invoice 节点...')
with neo4j_driver.session() as session:
    pg_cur.execute("""
        SELECT invoice_id, invoice_num, po_header_id, accounting_batch_id, amount
        FROM ap_invoices_all
        LIMIT 100
    """)
    invoices = pg_cur.fetchall()
    
    count = 0
    for inv in invoices:
        session.run("""
            MERGE (inv:Invoice {invoice_id: $invoice_id})
            SET inv.invoice_num = $invoice_num,
                inv.po_header_id = $po_header_id,
                inv.accounting_batch_id = $accounting_batch_id,
                inv.amount = $amount
        """, {
            'invoice_id': inv[0],
            'invoice_num': inv[1],
            'po_header_id': inv[2],
            'accounting_batch_id': inv[3],
            'amount': float(inv[4]) if inv[4] else 0
        })
        count += 1
    
    print(f'  OK 同步 {count} 个 Invoice 节点（带外键）')

print('\n[2/4] 同步 POLine 节点...')
with neo4j_driver.session() as session:
    pg_cur.execute("""
        SELECT po_line_id, po_header_id, line_num, amount
        FROM po_lines_all
        LIMIT 200
    """)
    po_lines = pg_cur.fetchall()
    
    count = 0
    for line in po_lines:
        session.run("""
            MERGE (line:POLine {po_line_id: $po_line_id})
            SET line.po_header_id = $po_header_id,
                line.line_num = $line_num,
                line.amount = $amount
        """, {
            'po_line_id': line[0],
            'po_header_id': line[1],
            'line_num': line[2],
            'amount': float(line[3]) if line[3] else 0
        })
        count += 1
    
    print(f'  OK 同步 {count} 个 POLine 节点（带外键）')

print('\n[3/4] 同步 Payment 节点...')
with neo4j_driver.session() as session:
    pg_cur.execute("""
        SELECT payment_id, invoice_id, amount, payment_date
        FROM ap_payments_all
        LIMIT 100
    """)
    payments = pg_cur.fetchall()
    
    count = 0
    for pay in payments:
        session.run("""
            MERGE (pay:Payment {payment_id: $payment_id})
            SET pay.invoice_id = $invoice_id,
                pay.amount = $amount,
                pay.payment_date = $payment_date
        """, {
            'payment_id': pay[0],
            'invoice_id': pay[1],
            'amount': float(pay[2]) if pay[2] else 0,
            'payment_date': str(pay[3]) if pay[3] else None
        })
        count += 1
    
    print(f'  OK 同步 {count} 个 Payment 节点（带外键）')

print('\n[4/4] 建立关系...')
with neo4j_driver.session() as session:
    # Invoice - MATCHES_PO_LINE -> POLine
    result = session.run("""
        MATCH (inv:Invoice), (line:POLine)
        WHERE inv.po_header_id = line.po_header_id
        AND NOT EXISTS((inv)-[:MATCHES_PO_LINE]->(line))
        WITH inv, line LIMIT 100
        CREATE (inv)-[:MATCHES_PO_LINE {match_type: 'PO'}]->(line)
        RETURN count(*) as count
    """)
    count = result.single()['count']
    print(f'  OK 建立 Invoice-MATCHES_PO_LINE->POLine: {count} 条')
    
    # Payment - APPLIED_TO -> Invoice
    result = session.run("""
        MATCH (pay:Payment), (inv:Invoice)
        WHERE pay.invoice_id = inv.invoice_id
        AND NOT EXISTS((pay)-[:APPLIED_TO]->(inv))
        WITH pay, inv LIMIT 100
        CREATE (pay)-[:APPLIED_TO]->(inv)
        RETURN count(*) as count
    """)
    count = result.single()['count']
    print(f'  OK 建立 Payment-APPLIED_TO->Invoice: {count} 条')

# 验证结果
print('\n' + '=' * 60)
print('验证结果')
print('=' * 60)

with neo4j_driver.session() as session:
    # 关系类型统计
    result = session.run("""
        MATCH ()-[r]->()
        RETURN type(r) as type, count(*) as count
        ORDER BY count DESC
    """)
    
    print('\n关系类型分布:')
    for record in result:
        print(f'  {record["type"]}: {record["count"]} 条')
    
    # 总关系类型数量
    result = session.run('CALL db.relationshipTypes()')
    types = [r['relationshipType'] for r in result]
    print(f'\n总关系类型数：{len(types)}')
    print('关系类型列表:')
    for i, t in enumerate(types, 1):
        print(f'  {i}. {t}')
    
    # 节点总数
    result = session.run('MATCH (n) RETURN count(n) as total')
    total = result.single()['total']
    print(f'\n总节点数：{total}')

pg_cur.close()
pg_conn.close()
neo4j_driver.close()

print('\n同步完成！')
