# 执行 SQL
import psycopg2

pg = psycopg2.connect(
    host='localhost',
    port=5432,
    database='erp',
    user='postgres',
    password='postgres'
)
pg.autocommit = True
cur = pg.cursor()

with open('rtr_trigger_fixed.sql', 'r', encoding='utf-8') as f:
    sql = f.read()

print("Executing SQL...")
cur.execute(sql)

# 验证
cur.execute("SELECT COUNT(*) FROM pg_trigger WHERE tgname LIKE '%_rtr'")
count = cur.fetchone()[0]
print(f"\n[OK] Created {count} RTR triggers")

# 显示触发器
cur.execute("""
    SELECT tgname, tgrelid::regclass 
    FROM pg_trigger 
    WHERE tgname LIKE '%_rtr'
""")
print("\nTriggers:")
for row in cur.fetchall():
    print(f"  - {row[0]} on {row[1]}")

cur.close()
pg.close()
