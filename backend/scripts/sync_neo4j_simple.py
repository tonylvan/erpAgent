#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Neo4j 数据同步 - 简化版
同步 Project/Item/Order 等节点
"""

from neo4j import GraphDatabase
import psycopg2
from decimal import Decimal

def convert_value(val):
    """转换 PostgreSQL 类型为 Neo4j 兼容类型"""
    if val is None:
        return None
    elif isinstance(val, Decimal):
        return float(val)
    elif isinstance(val, (int, float, str, bool)):
        return val
    else:
        return str(val)

# Neo4j 连接
driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'Tony1985'))

# PostgreSQL 连接
pg_conn = psycopg2.connect(
    host='localhost',
    database='erp',
    user='postgres',
    password='postgres'
)

print("=" * 70)
print("Neo4j 数据同步 - 简化版")
print("=" * 70)

try:
    with driver.session() as session:
        # 1. 同步项目 (30 个)
        print("\n同步项目数据...")
        with pg_conn.cursor() as cur:
            cur.execute("SELECT project_id, project_number, project_name, project_type, budget_amount, actual_cost FROM pa_projects_all LIMIT 30")
            projects = cur.fetchall()
        
        count = 0
        for p in projects:
            session.execute_write(lambda tx: tx.run("""
                MERGE (proj:Project {projectId: $pid})
                SET proj.projectNumber = $pnum,
                    proj.projectName = $pname,
                    proj.projectType = $ptype,
                    proj.budgetAmount = $budget,
                    proj.actualCost = $actual,
                    proj.lastSynced = datetime()
            """, {
                'pid': convert_value(p[0]),
                'pnum': convert_value(p[1]),
                'pname': convert_value(p[2]),
                'ptype': convert_value(p[3]),
                'budget': convert_value(p[4]),
                'actual': convert_value(p[5])
            }))
            count += 1
        print(f"  [OK] 同步 {count} 个项目")
        
        # 2. 同步会计分录 (500 条)
        print("\n同步会计分录...")
        with pg_conn.cursor() as cur:
            cur.execute("SELECT entry_id, event_id, ledger_id, entered_dr, entered_cr FROM xla_accounting_entries LIMIT 500")
            entries = cur.fetchall()
        
        count = 0
        for e in entries:
            session.execute_write(lambda tx: tx.run("""
                MERGE (ae:AccountingEntry {entryId: $eid})
                SET ae.eventId = $event,
                    ae.ledgerId = $ledger,
                    ae.enteredDr = $dr,
                    ae.enteredCr = $cr,
                    ae.lastSynced = datetime()
            """, {
                'eid': convert_value(e[0]),
                'event': convert_value(e[1]),
                'ledger': convert_value(e[2]),
                'dr': convert_value(e[3]),
                'cr': convert_value(e[4])
            }))
            count += 1
        print(f"  [OK] 同步 {count} 条会计分录")
        
        # 3. 统计 Neo4j 数据
        print("\n" + "=" * 50)
        print("Neo4j 数据统计:")
        print("=" * 50)
        
        result = session.run("MATCH (n) RETURN labels(n)[0] as label, count(*) as count ORDER BY count DESC LIMIT 15")
        print("\n节点统计 (Top 15):")
        for record in result:
            print(f"  - {record['label']}: {record['count']}")
        
        result = session.run("MATCH ()-[r]->() RETURN type(r) as type, count(*) as count ORDER BY count DESC LIMIT 10")
        print("\n关系统计 (Top 10):")
        for record in result:
            print(f"  - {record['type']}: {record['count']}")
        
        print("\n" + "=" * 70)
        print("[OK] Neo4j 同步完成!")
        print("=" * 70)

except Exception as e:
    print(f"\n[ERROR] 同步失败：{e}")
    import traceback
    traceback.print_exc()

finally:
    driver.close()
    pg_conn.close()
    print("\n连接已关闭")
