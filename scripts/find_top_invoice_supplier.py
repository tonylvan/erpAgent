from neo4j import GraphDatabase

d = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'Tony1985'))
s = d.session()

print("="*70)
print("查询最高金额发票的供应商")
print("="*70)

# 查询最高金额发票
print("\n[1] 最高金额发票 Top 5:")
print("-"*70)
r = s.run("""
    MATCH (inv:Invoice)
    WHERE inv.amount IS NOT NULL
    RETURN inv.id, inv.invoiceNum, inv.amount, inv.vendorId
    ORDER BY inv.amount DESC
    LIMIT 5
""")
for rec in r:
    inv_id = int(rec['inv.id'])
    marker = "[问题]" if inv_id >= 2000 else "[正常]"
    amt = float(rec['inv.amount']) if rec['inv.amount'] else 0
    print(f"{marker} ID={inv_id:>5d} | {rec['inv.invoiceNum']:<20s} | ${amt:>15,.2f} | vendorId={rec['inv.vendorId']}")

# 检查供应商
print("\n" + "="*70)
print("[2] 供应商信息:")
print("-"*70)
r = s.run("""
    MATCH (sup:Supplier)
    RETURN sup.id, sup.name, sup.code
    ORDER BY sup.id
    LIMIT 5
""")
for rec in r:
    print(f"  ID={rec['sup.id']!s:>10s} | {rec['sup.name']:<30s} | {rec['sup.code']}")

# 查询最高发票的供应商
print("\n" + "="*70)
print("[3] 最高发票 (ID=2004) 的供应商:")
print("-"*70)

r = s.run("""
    MATCH (inv:Invoice {id: 2004})
    RETURN inv
""")
inv = r.single()['inv']
print(f"发票：{inv['invoiceNum']}")
print(f"金额：${inv['amount']:,.2f}")
print(f"vendorId: {inv.get('vendorId', 'N/A')}")

# 尝试通过 vendorId 查找供应商
vendor_id = inv.get('vendorId')
if vendor_id:
    print(f"\n查找 vendorId={vendor_id} 的供应商:")
    
    # 尝试数字 ID
    r = s.run("""
        MATCH (sup:Supplier)
        WHERE sup.id = $vid OR sup.id = toString($vid)
        RETURN sup
    """, vid=int(vendor_id))
    if r.peek():
        sup = r.single()['sup']
        print(f"  [OK] 找到供应商:")
        print(f"      名称：{sup['name']}")
        print(f"      代码：{sup['code']}")
        print(f"      状态：{sup.get('status', 'N/A')}")
    else:
        print(f"  [!] Neo4j 中无此供应商 (可能未同步)")
        print(f"      提示：问题数据的 vendorId={vendor_id} 可能指向不存在的供应商")

d.close()
