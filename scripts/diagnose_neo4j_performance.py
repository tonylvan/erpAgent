from neo4j import GraphDatabase

d = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'Tony1985'))
s = d.session()

print("="*70)
print("Neo4j 性能诊断报告")
print("="*70)

# 1. 检查索引
print("\n[1] 现有索引:")
print("-"*70)
r = s.run("SHOW INDEXES")
indexes = list(r)
if indexes:
    for idx in indexes:
        print(f"  {idx['type']:15s} | {idx['entityType']:10s} | {idx['name']:30s}")
        print(f"                 | Labels/Types: {idx['labelsOrTypes']}")
        print(f"                 | Properties: {idx['properties']}")
else:
    print("  ⚠️ 未找到索引！")

# 2. 检查约束
print("\n[2] 现有约束:")
print("-"*70)
r = s.run("SHOW CONSTRAINTS")
constraints = list(r)
if constraints:
    for c in constraints:
        print(f"  {c['type']:20s} | {c['name']:30s}")
        print(f"                   | Entity: {c['entityType']} - {c['labelsOrTypes']}")
        print(f"                   | Properties: {c['properties']}")
else:
    print("  ⚠️ 未找到约束！")

# 3. 节点统计
print("\n[3] 节点统计:")
print("-"*70)
r = s.run("MATCH (n) RETURN labels(n)[0] as label, count(n) as count ORDER BY count DESC")
for rec in r:
    label = rec['label'] if rec['label'] else 'Unknown'
    print(f"  {label:30s}: {rec['count']:6d}")

# 4. 关系统计
print("\n[4] 关系统计:")
print("-"*70)
r = s.run("MATCH ()-[r]->() RETURN type(r) as type, count(r) as count ORDER BY count DESC")
for rec in r:
    print(f"  {rec['type']:30s}: {rec['count']:6d}")

# 5. 检查是否有 Label 的节点没有索引
print("\n[5] 性能建议:")
print("-"*70)

# 检查常用查询
print("\n  建议创建以下索引:")
print("  - Invoice.invoiceNum (发票号查询)")
print("  - PurchaseOrder.poNumber (PO 号查询)")
print("  - Employee.name (员工姓名查询)")
print("  - Supplier.code (供应商编码查询)")

print("\n  查询优化建议:")
print("  - 避免 SELECT *，只返回需要的字段")
print("  - 使用 EXPLAIN 分析查询计划")
print("  - 为 WHERE 条件字段创建索引")
print("  - 使用 PROFILE 识别性能瓶颈")

print("\n" + "="*70)

d.close()
