from neo4j import GraphDatabase

d = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'Tony1985'))
s = d.session()

print("查询最高金额的付款单 (Invoice):")
print("="*60)

# 查询所有发票（包括正常和问题）按金额排序
r = s.run("""
    MATCH (inv)
    WHERE (inv:Invoice OR inv:ProblemInvoice) AND inv.amount IS NOT NULL
    RETURN inv.id as id, 
           inv.invoiceNum as num, 
           inv.amount as amount,
           CASE WHEN inv:ProblemInvoice THEN 'Problem' ELSE 'Normal' END as type
    ORDER BY inv.amount DESC
    LIMIT 10
""")

print("\nTop 10 最高金额发票:")
print("-"*60)
for rec in r:
    type_marker = "[问题]" if rec['type'] == 'Problem' else "[正常]"
    print(f"  {type_marker} ID={rec['id']!s:5s} | {rec['num']:20s} | ${rec['amount']:>15,.2f}")

# 分别统计
r = s.run("""
    MATCH (inv:Invoice)
    WHERE inv.amount IS NOT NULL AND NOT inv:ProblemInvoice
    RETURN max(inv.amount) as max_amount
""")
max_normal = r.single()['max_amount']

r = s.run("""
    MATCH (inv:ProblemInvoice)
    WHERE inv.amount IS NOT NULL
    RETURN max(inv.amount) as max_amount
""")
max_problem = r.single()['max_amount']

print("\n" + "="*60)
print(f"最高金额 (正常发票): ${max_normal:,.2f}" if max_normal else "最高金额 (正常发票): 无数据")
print(f"最高金额 (问题发票): ${max_problem:,.2f}" if max_problem else "最高金额 (问题发票): 无数据")
print("="*60)

d.close()
