# -*- coding: utf-8 -*-
"""Neo4j 关系扩展脚本 v2 - 基于 PostgreSQL 数据"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from neo4j import GraphDatabase
import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

# Neo4j 连接
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "Tony1985")

# PostgreSQL 连接
PG_HOST = os.getenv("POSTGRES_HOST", "localhost")
PG_PORT = os.getenv("POSTGRES_PORT", "5432")
PG_DB = os.getenv("POSTGRES_DB", "gsd_erp")
PG_USER = os.getenv("POSTGRES_USER", "postgres")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "Tongtong2025!")

print("=" * 60)
print("Neo4j 关系扩展 v2 - 基于 PostgreSQL 数据")
print("=" * 60)

# 连接 Neo4j
neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# 连接 PostgreSQL
pg_conn = psycopg2.connect(
    host=PG_HOST,
    port=PG_PORT,
    database=PG_DB,
    user=PG_USER,
    password=PG_PASSWORD
)
pg_cur = pg_conn.cursor()

print(f"\n[OK] PostgreSQL 连接成功：{PG_DB}")

with neo4j_driver.session() as session:
    
    # 1. AP 模块 - Invoice 到 POLine 关系
    print("\n[AP 模块] Invoice -> POLine")
    pg_cur.execute("""
        SELECT DISTINCT invoice_id, po_line_id 
        FROM ap_invoice_po_matches 
        WHERE po_line_id IS NOT NULL 
        LIMIT 100
    """)
    matches = pg_cur.fetchall()
    print(f"   找到 {len(matches)} 条匹配记录")
    
    count = 0
    for invoice_id, po_line_id in matches:
        result = session.run("""
            MATCH (inv:Invoice {invoice_id: $invoice_id})
            MATCH (po_line:POLine {po_line_id: $po_line_id})
            WHERE NOT EXISTS((inv)-[:MATCHES_PO]->(po_line))
            CREATE (inv)-[:MATCHES_PO]->(po_line)
            RETURN count(*) as c
        """, invoice_id=str(invoice_id), po_line_id=str(po_line_id))
        count += result.single()["c"]
    print(f"   [OK] 创建 MATCHES_PO 关系：{count} 条")
    
    # 2. AP 模块 - Payment 到 Invoice 关系
    print("\n[AP 模块] Payment -> Invoice")
    pg_cur.execute("""
        SELECT DISTINCT payment_id, invoice_id 
        FROM ap_payments_all 
        WHERE invoice_id IS NOT NULL 
        LIMIT 100
    """)
    payments = pg_cur.fetchall()
    print(f"   找到 {len(payments)} 条付款记录")
    
    count = 0
    for payment_id, invoice_id in payments:
        result = session.run("""
            MATCH (pay:Payment {payment_id: $payment_id})
            MATCH (inv:Invoice {invoice_id: $invoice_id})
            WHERE NOT EXISTS((pay)-[:PAYS_FOR]->(inv))
            CREATE (pay)-[:PAYS_FOR]->(inv)
            RETURN count(*) as c
        """, payment_id=str(payment_id), invoice_id=str(invoice_id))
        count += result.single()["c"]
    print(f"   [OK] 创建 PAYS_FOR 关系：{count} 条")
    
    # 3. PO 模块 - POLine 到 PODistribution 关系
    print("\n[PO 模块] POLine -> PODistribution")
    pg_cur.execute("""
        SELECT DISTINCT po_line_id 
        FROM po_distributions_all 
        LIMIT 200
    """)
    dists = pg_cur.fetchall()
    print(f"   找到 {len(dists)} 条分配记录")
    
    count = 0
    for (po_line_id,) in dists:
        result = session.run("""
            MATCH (po_line:POLine {po_line_id: $po_line_id})
            MATCH (po_dist:PODistribution {po_line_id: $po_line_id})
            WHERE NOT EXISTS((po_line)-[:HAS_DISTRIBUTION]->(po_dist))
            CREATE (po_line)-[:HAS_DISTRIBUTION]->(po_dist)
            RETURN count(*) as c
        """, po_line_id=str(po_line_id))
        count += result.single()["c"]
    print(f"   [OK] 创建 HAS_DISTRIBUTION 关系：{count} 条")
    
    # 4. AR 模块 - Customer 到 ARTransaction 关系
    print("\n[AR 模块] Customer -> ARTransaction")
    pg_cur.execute("""
        SELECT DISTINCT customer_id 
        FROM ar_transactions_all 
        LIMIT 100
    """)
    customers = pg_cur.fetchall()
    print(f"   找到 {len(customers)} 个客户交易")
    
    count = 0
    for (customer_id,) in customers:
        result = session.run("""
            MATCH (cust:Customer {customer_id: $customer_id})
            MATCH (trans:ARTransaction {customer_id: $customer_id})
            WHERE NOT EXISTS((cust)-[:HAS_TRANSACTION]->(trans))
            CREATE (cust)-[:HAS_TRANSACTION]->(trans)
            RETURN count(*) as c
        """, customer_id=str(customer_id))
        count += result.single()["c"]
    print(f"   [OK] 创建 HAS_TRANSACTION 关系：{count} 条")
    
    # 5. INV 模块 - Item 到 Inventory 关系
    print("\n[INV 模块] Item -> Inventory")
    pg_cur.execute("""
        SELECT DISTINCT inventory_item_id 
        FROM inv_system_items_b 
        LIMIT 100
    """)
    items = pg_cur.fetchall()
    print(f"   找到 {len(items)} 个库存物品")
    
    count = 0
    for (item_id,) in items:
        result = session.run("""
            MATCH (item:Item {item_id: $item_id})
            MATCH (inv:Inventory {item_id: $item_id})
            WHERE NOT EXISTS((item)-[:HAS_INVENTORY]->(inv))
            CREATE (item)-[:HAS_INVENTORY]->(inv)
            RETURN count(*) as c
        """, item_id=str(item_id))
        count += result.single()["c"]
    print(f"   [OK] 创建 HAS_INVENTORY 关系：{count} 条")

# 验证结果
print("\n" + "=" * 60)
print("验证结果")
print("=" * 60)

with neo4j_driver.session() as session:
    result = session.run("CALL db.relationshipTypes()")
    types = [r["relationshipType"] for r in result]
    print(f"\n关系类型数：{len(types)}")
    for t in sorted(types):
        print(f"  - {t}")
    
    result = session.run("MATCH ()-[r]->() RETURN count(r) as count")
    total = result.single()["count"]
    print(f"\n总关系数：{total}")

pg_cur.close()
pg_conn.close()
neo4j_driver.close()

print("\n" + "=" * 60)
print("[OK] Neo4j 关系扩展完成！")
print("=" * 60)
