# 检查触发器发送的内容
import psycopg2
import json

pg = psycopg2.connect(
    host='localhost',
    port=5432,
    database='erp',
    user='postgres',
    password='postgres'
)
pg.autocommit = True
cur = pg.cursor()

# 监听
cur.execute("LISTEN neo4j_rtr_sync;")
pg.commit()

print("Listening... Trigger an insert now!\n")

# 在另一个连接插入
pg2 = psycopg2.connect(
    host='localhost',
    port=5432,
    database='erp',
    user='postgres',
    password='postgres'
)
pg2.autocommit = True
cur2 = pg2.cursor()

import time
test_id = int(time.time() * 1000) % 1000000
cur2.execute(f"""
    INSERT INTO ap_invoices_all 
    (invoice_id, invoice_num, vendor_id, invoice_amount, payment_status, invoice_date)
    VALUES ({test_id}, 'CHECK-DATA-{test_id}', 1, 123.45, 'PENDING', '2026-04-05')
""")
print(f"Inserted test record {test_id}")

# 等待通知
start = time.time()
while time.time() - start < 3:
    pg.poll()
    while pg.notifies:
        n = pg.notifies.pop(0)
        print(f"\n[NOTIFY] Payload: {n.payload}")
        try:
            data = json.loads(n.payload)
            print(f"         Parsed: {json.dumps(data, indent=2)}")
        except:
            pass

cur.close()
pg.close()
cur2.close()
pg2.close()
