# -*- coding: utf-8 -*-
"""Neo4j 关系同步 - 使用正确的外键字段"""
import psycopg2
from neo4j import GraphDatabase

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
print('Neo4j 关系同步（使用正确外键）')
print('=' * 60)

pg_conn = psycopg2.connect(**PG_CONFIG)
pg_cur = pg_conn.cursor()
neo4j_driver = GraphDatabase.driver(NEO4J_CONFIG['uri'], auth=(NEO4J_CONFIG['user'], NEO4J_CONFIG['password']))

# 1. 同步供应商相关
print('\n[1/6] 同步 Supplier 节点...')
with neo4j_driver.session() as session:
    pg_cur.execute("""
        SELECT vendor_id, vendor_name, vendor_type_lookup_code
        FROM ap_suppliers
        LIMIT 50
    """)
    suppliers = pg_cur.fetchall()
    
    count = 0
    for sup in suppliers:
        session.run("""
            MERGE (sup:Supplier {vendor_id: $vendor_id})
            SET sup.vendor_name = $vendor_name,
                sup.vendor_type = $vendor_type
        """, {
            'vendor_id': sup[0],
            'vendor_name': sup[1],
            'vendor_type': sup[2]
        })
        count += 1
    
    print(f'  OK 同步 {count} 个 Supplier 节点')

# 2. 同步 Invoice 节点（带 vendor_id 外键）
print('\n[2/6] 同步 Invoice 节点...')
with neo4j_driver.session() as session:
    pg_cur.execute("""
        SELECT invoice_id, invoice_num, vendor_id, invoice_amount, payment_status
        FROM ap_invoices_all
        LIMIT 100
    """)
    invoices = pg_cur.fetchall()
    
    count = 0
    for inv in invoices:
        session.run("""
            MERGE (inv:Invoice {invoice_id: $invoice_id})
            SET inv.invoice_num = $invoice_num,
                inv.vendor_id = $vendor_id,
                inv.amount = $amount,
                inv.status = $status
        """, {
            'invoice_id': inv[0],
            'invoice_num': inv[1],
            'vendor_id': inv[2],
            'amount': float(inv[3]) if inv[3] else 0,
            'status': inv[4]
        })
        count += 1
    
    print(f'  OK 同步 {count} 个 Invoice 节点（带 vendor_id 外键）')

# 3. 同步 POLine 节点
print('\n[3/6] 同步 POLine 节点...')
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
            'po_line_id': int(line[0]),
            'po_header_id': int(line[1]) if line[1] else 0,
            'line_num': float(line[2]) if line[2] else 0,
            'amount': float(line[3]) if line[3] else 0
        })
        count += 1
    
    print(f'  OK 同步 {count} 个 POLine 节点（带 po_header_id 外键）')

# 4. 同步 Payment 节点
print('\n[4/6] 同步 Payment 节点...')
with neo4j_driver.session() as session:
    pg_cur.execute("""
        SELECT check_id, check_number, amount, status
        FROM ap_payments_all
        LIMIT 100
    """)
    payments = pg_cur.fetchall()
    
    count = 0
    for pay in payments:
        session.run("""
            MERGE (pay:Payment {payment_id: $check_id})
            SET pay.check_number = $check_number,
                pay.amount = $amount,
                pay.status = $status
        """, {
            'check_id': pay[0],
            'check_number': pay[1],
            'amount': float(pay[2]) if pay[2] else 0,
            'status': pay[3]
        })
        count += 1
    
    print(f'  OK 同步 {count} 个 Payment 节点')

# 5. 建立关系
print('\n[5/6] 建立关系...')
with neo4j_driver.session() as session:
    # Supplier - SUPPLIES_INVOICE -> Invoice
    result = session.run("""
        MATCH (sup:Supplier), (inv:Invoice)
        WHERE sup.vendor_id = inv.vendor_id
        AND NOT EXISTS((sup)-[:SUPPLIES_INVOICE]->(inv))
        WITH sup, inv LIMIT 100
        CREATE (sup)-[:SUPPLIES_INVOICE]->(inv)
        RETURN count(*) as count
    """)
    count = result.single()['count']
    print(f'  OK Supplier-SUPPLIES_INVOICE->Invoice: {count} 条')
    
    # POLine - HAS_HEADER -> PurchaseOrder (临时创建 PO 节点)
    result = session.run("""
        MATCH (line:POLine)
        WHERE line.po_header_id IS NOT NULL
        AND NOT EXISTS((line)-[:HAS_HEADER]->(:PurchaseOrder))
        WITH line LIMIT 100
        MERGE (po:PurchaseOrder {po_header_id: line.po_header_id})
        CREATE (line)-[:HAS_HEADER]->(po)
        RETURN count(*) as count
    """)
    count = result.single()['count']
    print(f'  OK POLine-HAS_HEADER->PurchaseOrder: {count} 条')

# 6. 验证结果
print('\n[6/6] 验证结果...')
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
