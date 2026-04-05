import psycopg2

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='erp',
    user='postgres',
    password='postgres'
)
cur = conn.cursor()

# 查找 OTC 相关表（订单到收款）
print('=== OTC 模块表 (Order to Cash) ===')
cur.execute("""SELECT table_name FROM information_schema.tables 
WHERE table_schema='public' AND (
    table_name LIKE '%order%' OR 
    table_name LIKE '%sales%' OR 
    table_name LIKE '%customer%' OR
    table_name LIKE 'ar_%' OR
    table_name LIKE '%receipt%'
) ORDER BY table_name""")
otc_tables = [row[0] for row in cur.fetchall()]
for t in otc_tables:
    print(f'  - {t}')

# 查找 PTP 相关表（采购到付款）
print('\n=== PTP 模块表 (Procure to Pay) ===')
cur.execute("""SELECT table_name FROM information_schema.tables 
WHERE table_schema='public' AND (
    table_name LIKE '%purchase%' OR
    table_name LIKE 'po_%' OR
    table_name LIKE '%vendor%' OR
    table_name LIKE 'supplier%' OR
    table_name LIKE 'ap_%' OR
    table_name LIKE '%payment%'
) ORDER BY table_name""")
ptp_tables = [row[0] for row in cur.fetchall()]
for t in ptp_tables:
    print(f'  - {t}')

cur.close()
conn.close()

print(f'\nOTC 表数量：{len(otc_tables)}')
print(f'PTP 表数量：{len(ptp_tables)}')
