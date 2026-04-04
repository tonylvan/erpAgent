# -*- coding: utf-8 -*-
"""检查 PostgreSQL 和 Neo4j 数据差异"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import psycopg2
from neo4j import GraphDatabase

# PostgreSQL 连接
pg_conn = psycopg2.connect(
    host='localhost',
    port='5432',
    database='erp',
    user='postgres',
    password='Tongtong2025!',
    async_=False
)
pg_cur = pg_conn.cursor()

# Neo4j 连接
neo4j_driver = GraphDatabase.driver('bolt://127.0.0.1:7687', auth=('neo4j', 'Tony1985'))

print("=" * 60)
print("PostgreSQL vs Neo4j 数据对比")
print("=" * 60)

# PostgreSQL 统计
print("\n【PostgreSQL】")
pg_cur.execute("SELECT COUNT(*) FROM ap_invoices_all")
print(f"  Invoices: {pg_cur.fetchone()[0]} 条")

pg_cur.execute("SELECT COUNT(*) FROM po_lines_all")
print(f"  POLines: {pg_cur.fetchone()[0]} 条")

pg_cur.execute("SELECT COUNT(*) FROM ap_payments_all")
print(f"  Payments: {pg_cur.fetchone()[0]} 条")

pg_cur.execute("SELECT COUNT(*) FROM ar_transactions_all")
print(f"  AR Transactions: {pg_cur.fetchone()[0]} 条")

# Neo4j 统计
print("\n【Neo4j】")
with neo4j_driver.session() as session:
    result = session.run("MATCH (inv:Invoice) RETURN count(inv) as c")
    print(f"  Invoice 节点：{result.single()['c']} 个")
    
    result = session.run("MATCH (po:POLine) RETURN count(po) as c")
    print(f"  POLine 节点：{result.single()['c']} 个")
    
    result = session.run("MATCH (pay:Payment) RETURN count(pay) as c")
    print(f"  Payment 节点：{result.single()['c']} 个")
    
    result = session.run("MATCH (trans:ARTransaction) RETURN count(trans) as c")
    print(f"  ARTransaction 节点：{result.single()['c']} 个")

pg_cur.close()
pg_conn.close()
neo4j_driver.close()

print("\n" + "=" * 60)
print("RTR 实时同步状态：❌ 未启用")
print("=" * 60)
