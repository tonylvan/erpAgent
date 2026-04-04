import psycopg2
import time

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='erp',
    user='postgres',
    password='postgres'
)
conn.autocommit = True

cur = conn.cursor()

# 先监听
cur.execute("LISTEN test_channel;")
print("Listening on test_channel")

# 发送通知
cur.execute("NOTIFY test_channel, 'hello';")
print("Sent NOTIFY")

# 接收
time.sleep(0.5)
conn.poll()
while conn.notifies:
    notify = conn.notifies.pop(0)
    print(f"Received: {notify.channel} - {notify.payload}")

cur.close()
conn.close()
