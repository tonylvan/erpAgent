from neo4j import GraphDatabase

d = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'Tony1985'))
s = d.session()

print("="*70)
print("检查 Neo4j 中的事件数据")
print("="*70)

# 检查所有节点类型
print("\n[1] 所有节点类型:")
print("-"*70)
r = s.run("MATCH (n) RETURN labels(n)[0] as label, count(n) as count ORDER BY count DESC")
for rec in r:
    label = rec['label'] if rec['label'] else 'Unknown'
    has_event = 'Event' in label if label else False
    marker = " [Event]" if has_event else ""
    print(f"  {label:30s}: {rec['count']}{marker}")

# 检查 XLA 事件
print("\n[2] XLA 事件:")
print("-"*70)
r = s.run("MATCH (n:XLAEvent) RETURN count(n) as count")
xla_count = r.single()['count']
print(f"  XLAEvent: {xla_count}")

# 检查审计
print("\n[3] 审计/日志:")
print("-"*70)
r = s.run("MATCH (n:AuditTrail) RETURN count(n) as count")
audit_count = r.single()['count']
print(f"  AuditTrail: {audit_count}")

print("\n" + "="*70)
print(f"XLA Events: {xla_count}")
print(f"Audit Trails: {audit_count}")
print("="*70)

d.close()
