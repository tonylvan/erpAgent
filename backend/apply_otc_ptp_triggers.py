import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='erp',
    user='postgres',
    password='postgres'
)
conn.autocommit = True
cur = conn.cursor()

print("执行 OTC/PTP 触发器 SQL...")

with open('rtr_otc_ptp_triggers.sql', 'r', encoding='utf-8') as f:
    sql = f.read()

cur.execute(sql)

# 验证
cur.execute("SELECT COUNT(*) FROM pg_trigger WHERE tgname LIKE '%_rtr'")
total = cur.fetchone()[0]
print(f"\n[OK] 总共 {total} 个 RTR 触发器")

# 显示 OTC 触发器
print("\n=== OTC 模块触发器 ===")
cur.execute("""
    SELECT tgname, tgrelid::regclass 
    FROM pg_trigger 
    WHERE tgname LIKE '%_rtr' AND (
        tgrelid::regclass::text LIKE 'ar_%' OR 
        tgrelid::regclass::text LIKE 'oe_%' OR
        tgrelid::regclass::text LIKE 'om_%'
    )
    ORDER BY tgrelid::regclass::text
""")
for row in cur.fetchall():
    print(f"  [OK] {row[0]} on {row[1]}")

# 显示 PTP 触发器
print("\n=== PTP 模块触发器 ===")
cur.execute("""
    SELECT tgname, tgrelid::regclass 
    FROM pg_trigger 
    WHERE tgname LIKE '%_rtr' AND (
        tgrelid::regclass::text LIKE 'ap_%' OR 
        tgrelid::regclass::text LIKE 'po_%'
    )
    ORDER BY tgrelid::regclass::text
""")
for row in cur.fetchall():
    print(f"  [OK] {row[0]} on {row[1]}")

cur.close()
conn.close()
