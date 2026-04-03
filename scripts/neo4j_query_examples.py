# -*- coding: utf-8 -*-
"""
Neo4j Business Relationship Query Examples
"""

from neo4j import GraphDatabase

driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'Tony1985'))

def run_query(session, query, params=None):
    """Helper to run query and print results"""
    result = session.run(query, params or {})
    records = list(result)
    if records:
        print(f"\n返回 {len(records)} 条记录:")
        for i, record in enumerate(records[:5], 1):  # Show first 5
            print(f"  {i}. {dict(record)}")
        if len(records) > 5:
            print(f"  ... 还有 {len(records) - 5} 条记录")
    else:
        print("  无结果")
    return len(records)

with driver.session() as session:
    print("=" * 70)
    print("Neo4j 业务关系查询示例")
    print("=" * 70)
    
    # Query 1: 供应商完整供应链
    print("\n" + "=" * 70)
    print("1. 查询供应商的完整供应链 (Supplier -> PO)")
    print("=" * 70)
    query = """
    MATCH (sup:Supplier)-[:SUPPLIES_VIA]->(po:PurchaseOrder)
    RETURN sup.id as supplier_id, sup.segment1 as supplier_code, 
           po.id as po_id, po.segment1 as po_number, 
           po.amount, po.status_lookup_code as status
    ORDER BY po.amount DESC
    LIMIT 10
    """
    run_query(session, query)
    
    # Query 2: 发票及其行项目
    print("\n" + "=" * 70)
    print("2. 查询发票及其行项目 (Invoice -> InvoiceLine)")
    print("=" * 70)
    query = """
    MATCH (inv:Invoice)-[:HAS_LINE]->(line:InvoiceLine)
    RETURN inv.id as invoice_id, inv.invoice_num, inv.invoice_amount,
           line.id as line_id, line.description, line.amount
    ORDER BY inv.invoice_amount DESC
    LIMIT 10
    """
    run_query(session, query)
    
    # Query 3: 销售订单物料链
    print("\n" + "=" * 70)
    print("3. 查询销售订单的物料明细 (SO -> SOLine -> Item)")
    print("=" * 70)
    query = """
    MATCH (so:SalesOrder)-[:HAS_LINE]->(line:SalesOrderLine)-[:ORDERS_ITEM]->(item:InventoryItem)
    RETURN so.segment1 as order_number, line.line_number, 
           item.segment1 as item_code, item.description,
           line.quantity, line.price
    LIMIT 10
    """
    run_query(session, query)
    
    # Query 4: 供应商所有联系信息
    print("\n" + "=" * 70)
    print("4. 查询供应商的所有联系信息 (Site, Contact, Bank)")
    print("=" * 70)
    query = """
    MATCH (sup:Supplier {segment1: 'SUP001'})-[r]->(info)
    RETURN labels(sup)[0] as supplier, type(r) as relationship, 
           labels(info)[0] as info_type, info.id as info_id
    ORDER BY type(r)
    """
    run_query(session, query)
    
    # Query 5: 采购订单统计
    print("\n" + "=" * 70)
    print("5. 统计各状态采购订单数量")
    print("=" * 70)
    query = """
    MATCH (po:PurchaseOrder)
    RETURN po.status_lookup_code as status, count(*) as count
    ORDER BY count DESC
    """
    run_query(session, query)
    
    # Query 6: 金额前 10 的发票
    print("\n" + "=" * 70)
    print("6. 查询金额前 10 的发票")
    print("=" * 70)
    query = """
    MATCH (inv:Invoice)
    RETURN inv.invoice_num as invoice_number, inv.vendor_id as supplier_id, 
           inv.invoice_amount as amount
    ORDER BY amount DESC
    LIMIT 10
    """
    run_query(session, query)
    
    # Query 7: 完整 P2P 链路
    print("\n" + "=" * 70)
    print("7. 查询完整采购到付款链路 (P2P Full Path)")
    print("=" * 70)
    query = """
    MATCH path = (sup:Supplier)-[:SUPPLIES_VIA]->(po:PurchaseOrder)-[:HAS_LINE]->(pol:POLine)
    RETURN sup.segment1 as supplier_code, po.segment1 as po_number, 
           pol.line_number, pol.amount as line_amount
    LIMIT 5
    """
    run_query(session, query)
    
    # Query 8: 图统计
    print("\n" + "=" * 70)
    print("8. 图数据库统计信息")
    print("=" * 70)
    
    # Node count
    result = session.run("MATCH (n) RETURN count(n) as total")
    total_nodes = result.single()['total']
    print(f"\n  总节点数：{total_nodes}")
    
    # Relationship count
    result = session.run("MATCH ()-[r]->() RETURN count(r) as total")
    total_rels = result.single()['total']
    print(f"  总关系数：{total_rels}")
    
    # Label distribution
    print("\n  节点类型分布:")
    result = session.run("""
        MATCH (n) 
        RETURN labels(n)[0] as label, count(*) as count 
        ORDER BY count DESC
    """)
    for record in result:
        print(f"    {record['label']:25s}: {record['count']:5d}")
    
    # Relationship type distribution
    print("\n  关系类型分布:")
    result = session.run("""
        MATCH ()-[r]->() 
        RETURN type(r) as type, count(*) as count 
        ORDER BY count DESC
    """)
    for record in result:
        print(f"    {record['type']:25s}: {record['count']:5d}")

print("\n" + "=" * 70)
print("查询完成！")
print("=" * 70)

driver.close()
