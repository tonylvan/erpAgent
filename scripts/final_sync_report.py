# -*- coding: utf-8 -*-
"""
Final Sync Report - All Relationships
"""

from neo4j import GraphDatabase

driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'Tony1985'))
session = driver.session()

print("="*70)
print("Neo4j 最终关系统计报告")
print("="*70)

# Node count
print("\n【节点统计】")
result = session.run("MATCH (n) RETURN labels(n)[0] as label, count(*) as count ORDER BY count DESC")
nodes = {}
total_nodes = 0
for r in result:
    label = r['label'] or 'Unknown'
    count = r['count']
    nodes[label] = count
    total_nodes += count
    print(f"  {label:25s}: {count:5d}")

print(f"\n  {'TOTAL':25s}: {total_nodes:5d}")

# Relationship count
print("\n【关系统计】")
result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(*) as count ORDER BY count DESC")
rels = {}
total_rels = 0
for r in result:
    rel_type = r['type']
    count = r['count']
    rels[rel_type] = count
    total_rels += count
    print(f"  {rel_type:25s}: {count:5d}")

print(f"\n  {'TOTAL':25s}: {total_rels:5d}")

# Summary by category
print("\n【关系分类】")
print("\n显式关系 (已同步):")
explicit = ['HAS_LINE', 'SENDS_INVOICE', 'ORDERS_ITEM', 'HAS_SITE', 'HAS_CONTACT', 'SUPPLIES_VIA', 'HAS_BANK_ACCOUNT']
explicit_total = sum(rels.get(r, 0) for r in explicit)
for r in explicit:
    print(f"  {r:25s}: {rels.get(r, 0):5d}")
print(f"  {'小计':25s}: {explicit_total:5d}")

print("\n隐式关系 (待同步):")
implicit = ['CREATED_BY', 'APPROVED_BY', 'USES_CURRENCY', 'MATCHES_PO_LINE', 'HAS_PAYMENT', 'HAS_DISTRIBUTION', 'HAS_SHIPMENT']
implicit_total = sum(rels.get(r, 0) for r in implicit)
for r in implicit:
    count = rels.get(r, 0)
    if count > 0:
        print(f"  {r:25s}: {count:5d} ✓")
    else:
        print(f"  {r:25s}:     0 -")
print(f"  {'小计':25s}: {implicit_total:5d}")

print("\n【业务链路完整性】")
# P2P chain
result = session.run("""
    MATCH path = (sup:Supplier)-[:SUPPLIES_VIA]->(po:PurchaseOrder)-[:HAS_LINE]->(pol:POLine)
    RETURN count(path) as p2p_count
""")
p2p = result.single()['p2p_count']
print(f"  P2P (Supplier→PO→POLine): {p2p}")

# O2C chain
result = session.run("""
    MATCH path = (cust:Customer)-[:HAS_TRANSACTION]->(so:SalesOrder)-[:HAS_LINE]->(sol:SalesOrderLine)-[:ORDERS_ITEM]->(item:InventoryItem)
    RETURN count(path) as o2c_count
""")
o2c = result.single()['o2c_count']
print(f"  O2C (Customer→SO→SOL→Item): {o2c}")

# Supplier management
result = session.run("""
    MATCH path = (sup:Supplier)-[:HAS_SITE|HAS_CONTACT|HAS_BANK_ACCOUNT]->(info)
    RETURN count(path) as sup_count
""")
sup = result.single()['sup_count']
print(f"  供应商管理 (Supplier→Sites/Contacts/Banks): {sup}")

print("\n" + "="*70)
print(f"总结：{len(nodes)} 种节点，{len(rels)} 种关系，总计 {total_nodes} 节点 / {total_rels} 关系")
print("="*70)

driver.close()
