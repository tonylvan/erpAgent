# -*- coding: utf-8 -*-
"""Neo4j 关系扩展脚本 v3 - 基于已验证字段"""
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
PG_DB = os.getenv("POSTGRES_DB", "erp")
PG_USER = os.getenv("POSTGRES_USER", "postgres")
PG_PASSWORD = os.getenv("POSTGRES_PASSWORD", "Tongtong2025!")

print("=" * 60)
print("Neo4j 关系扩展 v3 - 基于已验证字段")
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
    
    # 1. AP 模块 - Invoice 到 POLine 关系 (MATCHES_PO)
    print("\n[1/5] AP 模块：Invoice -[MATCHES_PO]-> POLine")
    pg_cur.execute("""
        SELECT DISTINCT invoice_id, po_line_id 
        FROM ap_invoice_po_matches 
        WHERE po_line_id IS NOT NULL AND invoice_id IS NOT NULL
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
    
    # 2. AP 模块 - Invoice 到 Payment 关系 (HAS_PAYMENT)
    print("\n[2/5] AP 模块：Invoice -[HAS_PAYMENT]-> Payment")
    pg_cur.execute("""
        SELECT DISTINCT invoice_id, check_id 
        FROM ap_invoice_payments_all 
        WHERE check_id IS NOT NULL AND invoice_id IS NOT NULL
        LIMIT 100
    """)
    payments = pg_cur.fetchall()
    print(f"   找到 {len(payments)} 条付款记录")
    
    count = 0
    for invoice_id, check_id in payments:
        result = session.run("""
            MATCH (inv:Invoice {invoice_id: $invoice_id})
            MATCH (pay:Payment {check_id: $check_id})
            WHERE NOT EXISTS((inv)-[:HAS_PAYMENT]->(pay))
            CREATE (inv)-[:HAS_PAYMENT]->(pay)
            RETURN count(*) as c
        """, invoice_id=str(invoice_id), check_id=str(check_id))
        count += result.single()["c"]
    print(f"   [OK] 创建 HAS_PAYMENT 关系：{count} 条")
    
    # 3. PO 模块 - POLine 到 PODistribution 关系 (HAS_DISTRIBUTION)
    print("\n[3/5] PO 模块：POLine -[HAS_DISTRIBUTION]-> PODistribution")
    pg_cur.execute("""
        SELECT DISTINCT po_line_id 
        FROM po_distributions_all 
        WHERE po_line_id IS NOT NULL
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
    
    # 4. AR 模块 - Customer 到 ARTransaction 关系 (HAS_TRANSACTION)
    print("\n[4/5] AR 模块：Customer -[HAS_TRANSACTION]-> ARTransaction")
    pg_cur.execute("""
        SELECT DISTINCT customer_id 
        FROM ar_transactions_all 
        WHERE customer_id IS NOT NULL
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
    
    # 5. PO 模块 - POHeader 到 POLine 关系 (HAS_LINE)
    print("\n[5/5] PO 模块：POHeader -[HAS_LINE]-> POLine")
    pg_cur.execute("""
        SELECT DISTINCT po_header_id 
        FROM po_lines_all 
        WHERE po_header_id IS NOT NULL
        LIMIT 200
    """)
    headers = pg_cur.fetchall()
    print(f"   找到 {len(headers)} 个采购订单头")
    
    count = 0
    for (po_header_id,) in headers:
        result = session.run("""
            MATCH (po:PurchaseOrder {po_header_id: $po_header_id})
            MATCH (po_line:POLine {po_header_id: $po_header_id})
            WHERE NOT EXISTS((po)-[:HAS_LINE]->(po_line))
            CREATE (po)-[:HAS_LINE]->(po_line)
            RETURN count(*) as c
        """, po_header_id=str(po_header_id))
        count += result.single()["c"]
    print(f"   [OK] 创建 HAS_LINE 关系：{count} 条")

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
