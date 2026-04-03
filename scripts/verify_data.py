# -*- coding: utf-8 -*-
import psycopg2

conn = psycopg2.connect(host='localhost', database='erp', user='postgres', password='postgres')
cur = conn.cursor()

cur.execute("SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename")
print("Tables:")
for r in cur.fetchall():
    print(f"  - {r[0]}")

cur.execute("SELECT COUNT(*) FROM mtl_system_items_b")
print(f"\nInventory items: {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(*) FROM so_headers_all")
print(f"Sales orders: {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(*) FROM so_lines_all")
print(f"Sales order lines: {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(*) FROM per_all_people_f")
print(f"Employees: {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(*) FROM fa_additions_b")
print(f"Fixed assets: {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(*) FROM ce_bank_accounts")
print(f"Bank accounts: {cur.fetchone()[0]}")

cur.close()
conn.close()
print("\nDone!")
