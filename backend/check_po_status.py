import psycopg2

conn = psycopg2.connect(
    host='localhost',
    database='erp',
    user='postgres',
    password='postgres'
)
cur = conn.cursor()

# 检查 po_headers_all 的 status 相关字段
cur.execute("""
    SELECT column_name, data_type 
    FROM information_schema.columns 
    WHERE table_name = 'po_headers_all' 
    AND column_name LIKE '%status%'
""")
print("po_headers_all status 相关字段:")
for r in cur.fetchall():
    print(f"  {r[0]}: {r[1]}")

# 显示所有字段
cur.execute("""
    SELECT column_name 
    FROM information_schema.columns 
    WHERE table_name = 'po_headers_all' 
    ORDER BY ordinal_position
""")
print("\npo_headers_all 所有字段:")
for r in cur.fetchall():
    print(f"  {r[0]}")

cur.close()
conn.close()
