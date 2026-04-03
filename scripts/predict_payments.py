from neo4j import GraphDatabase
from datetime import datetime, timedelta

d = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'Tony1985'))
s = d.session()

print("="*70)
print("未来一周付款预测")
print("="*70)

# 1. 查询历史付款数据
print("\n[1] 历史付款数据统计:")
print("-"*70)
r = s.run("""
    MATCH (p:Payment)
    WHERE p.amount IS NOT NULL AND p.checkDate IS NOT NULL
    RETURN 
        count(p) as total,
        sum(p.amount) as total_amount,
        avg(p.amount) as avg_amount,
        min(p.checkDate) as first_date,
        max(p.checkDate) as last_date
""")
rec = r.single()
print(f"  付款单总数：{rec['total']}")
print(f"  总金额：${float(rec['total_amount']):,.2f}")
print(f"  平均金额：${float(rec['avg_amount']):,.2f}")
print(f"  日期范围：{rec['first_date']} 至 {rec['last_date']}")

# 2. 按周统计付款
print("\n[2] 按周付款统计:")
print("-"*70)
r = s.run("""
    MATCH (p:Payment)
    WHERE p.amount IS NOT NULL AND p.checkDate IS NOT NULL
    WITH date({year: date(p.checkDate).year, week: date(p.checkDate).week, dayOfWeek: 1}) as week_start, sum(p.amount) as week_total
    RETURN week_start, week_total
    ORDER BY week_start DESC
    LIMIT 8
""")
for rec in r:
    print(f"  {rec['week_start']}: ${float(rec['week_total']):,.2f}")

# 3. 按供应商统计（Top 10）
print("\n[3] 供应商付款统计 (Top 10):")
print("-"*70)
r = s.run("""
    MATCH (p:Payment)-[:BELONGS_TO]->(sup:Supplier)
    WHERE p.amount IS NOT NULL
    RETURN sup.name, count(p) as count, sum(p.amount) as total
    ORDER BY total DESC
    LIMIT 10
""")
for rec in r:
    print(f"  {rec['sup.name']:<30s}: {rec['count']}笔 | ${float(rec['total']):,.2f}")

# 4. 预测未来一周
print("\n" + "="*70)
print("[4] 未来一周付款预测:")
print("-"*70)

# 计算平均每周付款
r = s.run("""
    MATCH (p:Payment)
    WHERE p.amount IS NOT NULL
    RETURN sum(p.amount) / count(DISTINCT date(p.checkDate).year + '-' + date(p.checkDate).week) as weekly_avg
""")
rec = r.single()
weekly_avg = float(rec['weekly_avg']) if rec['weekly_avg'] else 0

# 计算平均每日付款
daily_avg = weekly_avg / 7

print(f"  历史平均每周付款：${weekly_avg:,.2f}")
print(f"  历史平均每日付款：${daily_avg:,.2f}")

# 预测
next_week_dates = []
today = datetime.now()
for i in range(7):
    next_week_dates.append(today + timedelta(days=i+1))

print(f"\n  未来 7 天预测 (2026-04-03 至 2026-04-09):")
print(f"  ────────────────────────────────────────")
for date in next_week_dates:
    print(f"    {date.strftime('%Y-%m-%d')} ({date.strftime('%A')[:3]}): ${daily_avg:,.2f}")

print(f"\n  ────────────────────────────────────────")
print(f"  下周预测总额：${weekly_avg:,.2f}")
print(f"  ────────────────────────────────────────")

# 5. 基于待付款状态的预测
print("\n[5] 待付款状态统计:")
print("-"*70)
r = s.run("""
    MATCH (p:Payment)
    WHERE p.status IN ['PENDING', 'ISSUED', 'DUE']
    WITH p.status as status, count(p) as count, sum(p.amount) as total
    RETURN status, count, total
""")
pending_total = 0
for rec in r:
    status = rec['status']
    count = rec['count']
    total = float(rec['total']) if rec['total'] else 0
    pending_total += total
    print(f"  {status:<10s}: {count}笔 | ${total:,.2f}")

print(f"\n  待付款总额：${pending_total:,.2f}")
print(f"  提示：这些是短期内需要支付的金额")

d.close()
