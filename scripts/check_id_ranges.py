from neo4j import GraphDatabase

d = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'Tony1985'))
s = d.session()

print("Checking ID ranges in Neo4j:")
print("="*60)

# Check Invoice IDs
r = s.run('MATCH (inv:Invoice) RETURN min(inv.id) as min, max(inv.id) as max, count(inv) as count')
rec = r.single()
print(f"Invoice:        ID {rec['min']} - {rec['max']} (count: {rec['count']})")

# Check PO IDs
r = s.run('MATCH (po:PurchaseOrder) RETURN min(po.id) as min, max(po.id) as max, count(po) as count')
rec = r.single()
print(f"PurchaseOrder:  ID {rec['min']} - {rec['max']} (count: {rec['count']})")

# Check Employee IDs
r = s.run('MATCH (emp:Employee) RETURN min(emp.id) as min, max(emp.id) as max, count(emp) as count')
rec = r.single()
print(f"Employee:       ID {rec['min']} - {rec['max']} (count: {rec['count']})")

# Check Supplier IDs
r = s.run('MATCH (sup:Supplier) RETURN min(sup.id) as min, max(sup.id) as max, count(sup) as count')
rec = r.single()
print(f"Supplier:       ID {rec['min']} - {rec['max']} (count: {rec['count']})")

# Check Project IDs
r = s.run('MATCH (proj:Project) RETURN min(proj.id) as min, max(proj.id) as max, count(proj) as count')
rec = r.single()
print(f"Project:        ID {rec['min']} - {rec['max']} (count: {rec['count']})")

# Check Asset IDs
r = s.run('MATCH (asset:FixedAsset) RETURN min(asset.id) as min, max(asset.id) as max, count(asset) as count')
rec = r.single()
print(f"FixedAsset:     ID {rec['min']} - {rec['max']} (count: {rec['count']})")

d.close()
