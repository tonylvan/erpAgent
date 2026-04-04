import psycopg2

# 检查当前数据库的监听
conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='erp',
    user='postgres',
    password='postgres'
)

cur = conn.cursor()

# 检查 pg_listening_channels
cur.execute("SELECT * FROM pg_listening_channels;")
channels = cur.fetchall()
print(f"当前监听的频道：{channels}")

# 手动发送一个通知
cur.execute("NOTIFY neo4j_rtr_sync, 'test message';")
print("发送了测试通知")

cur.close()
conn.close()
