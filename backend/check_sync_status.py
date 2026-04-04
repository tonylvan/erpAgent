import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='erp',
    user='postgres',
    password='postgres'
)

cur = conn.cursor()

# 检查最新同步日志
cur.execute("""
    SELECT id, table_name, operation, record_id, status, sync_time 
    FROM rtr_sync_log 
    ORDER BY id DESC 
    LIMIT 5
""")

print("Latest Sync Logs:")
print("-" * 80)
for row in cur.fetchall():
    print(f"ID={row[0]} | {row[1]:<25} | {row[2]:<10} | ID={row[3]:<10} | {row[4]:<12} | {row[5]}")

cur.close()
conn.close()
