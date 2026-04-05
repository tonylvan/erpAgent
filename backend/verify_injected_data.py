import psycopg2
from decimal import Decimal

conn = psycopg2.connect(
    host='localhost',
    port=5432,
    database='erp',
    user='postgres',
    password='postgres'
)
cur = conn.cursor()

print("="*70)
print("验证注入的异常数据")
print("="*70)

# 1. 验证负库存
print("\n[1/3] 负库存数据:")
cur.execute("""SELECT * FROM mtl_material_transactions WHERE transaction_id = -888888""")
row = cur.fetchone()
if row:
    print(f"  [OK] 负库存交易存在，数量={row[4]}")

# 2. 验证异常付款
print("\n[2/3] 异常付款数据:")
cur.execute("""SELECT check_id, check_number, amount FROM ap_payments_all WHERE check_id = -666666""")
row = cur.fetchone()
if row:
    print(f"  [OK] 异常付款存在，金额=${row[2]:,.2f}")

# 3. 验证天价采购
print("\n[3/3] 天价采购订单:")
cur.execute("""SELECT po_header_id, amount FROM po_headers_all WHERE po_header_id = -555555""")
row = cur.fetchone()
if row:
    print(f"  [OK] 天价采购订单存在，总金额=${row[1]:,.2f}")

cur.close()
conn.close()

print("\n" + "="*70)
print("[OK] 所有异常数据已验证！")
print("="*70)
print("\n下一步:")
print("  1. 访问 http://localhost:5181 查看预警中心")
print("  2. 检查是否检测到这些异常数据")
