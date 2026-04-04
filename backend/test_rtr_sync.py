# -*- coding: utf-8 -*-
"""
RTR 实时同步测试脚本
测试 PostgreSQL → Neo4j 自动同步
"""

import sys
import io

# 修复 Windows 编码问题
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

import psycopg2
import time
from neo4j import GraphDatabase

# 配置
PG_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'erp',
    'user': 'postgres',
    'password': 'postgres'
}

NEO4J_CONFIG = {
    'uri': 'bolt://localhost:7687',
    'auth': ('neo4j', 'Tony1985')
}


def test_insert_sync():
    """测试 INSERT 同步"""
    print("\n" + "="*50)
    print("📝 测试 1: INSERT 同步")
    print("="*50)
    
    # 1. 插入测试数据到 PostgreSQL
    pg_conn = psycopg2.connect(**PG_CONFIG)
    cur = pg_conn.cursor()
    
    test_invoice_num = f'RTR-TEST-{int(time.time())}'
    
    print(f" 插入测试发票：{test_invoice_num}")
    cur.execute("""
        INSERT INTO ap_invoices_all 
        (invoice_id, invoice_num, vendor_id, invoice_amount, payment_status, invoice_date)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (99999, test_invoice_num, 1, 1888.88, 'PENDING', '2026-04-05'))
    
    pg_conn.commit()
    print("✅ PostgreSQL 插入成功")
    
    cur.close()
    pg_conn.close()
    
    # 2. 等待同步（最多等待 5 秒）
    print("⏳ 等待同步...")
    time.sleep(2)
    
    # 3. 查询 Neo4j
    driver = GraphDatabase.driver(**NEO4J_CONFIG)
    with driver.session() as session:
        result = session.run("""
            MATCH (i:Invoice {invoice_num: $invoice_num}) 
            RETURN i
        """, invoice_num=test_invoice_num)
        
        record = result.single()
        if record:
            invoice = record['i']
            print(f"✅ Neo4j 同步成功！")
            print(f"   发票号：{invoice.get('invoice_num')}")
            print(f"   金额：{invoice.get('amount')}")
            print(f"   状态：{invoice.get('status')}")
            return True
        else:
            print("❌ Neo4j 未找到同步的节点")
            return False
    
    driver.close()


def test_update_sync():
    """测试 UPDATE 同步"""
    print("\n" + "="*50)
    print("📝 测试 2: UPDATE 同步")
    print("="*50)
    
    # 1. 更新 PostgreSQL 数据
    pg_conn = psycopg2.connect(**PG_CONFIG)
    cur = pg_conn.cursor()
    
    print(" 更新发票金额：1888.88 → 2999.99")
    cur.execute("""
        UPDATE ap_invoices_all 
        SET invoice_amount = 2999.99, payment_status = 'APPROVED'
        WHERE invoice_id = 99999
    """)
    
    pg_conn.commit()
    print("✅ PostgreSQL 更新成功")
    
    cur.close()
    pg_conn.close()
    
    # 2. 等待同步
    print("⏳ 等待同步...")
    time.sleep(2)
    
    # 3. 查询 Neo4j
    driver = GraphDatabase.driver(**NEO4J_CONFIG)
    with driver.session() as session:
        result = session.run("""
            MATCH (i:Invoice) 
            WHERE i.invoice_id = 99999 OR i.id = 99999
            RETURN i
        """)
        
        record = result.single()
        if record:
            invoice = record['i']
            print(f"✅ Neo4j 更新成功！")
            print(f"   新金额：{invoice.get('amount')}")
            print(f"   新状态：{invoice.get('status')}")
            return True
        else:
            print("❌ Neo4j 未找到更新的节点")
            return False
    
    driver.close()


def test_delete_sync():
    """测试 DELETE 同步"""
    print("\n" + "="*50)
    print("📝 测试 3: DELETE 同步")
    print("="*50)
    
    # 1. 删除 PostgreSQL 数据
    pg_conn = psycopg2.connect(**PG_CONFIG)
    cur = pg_conn.cursor()
    
    print("📌 删除测试发票")
    cur.execute("DELETE FROM ap_invoices_all WHERE invoice_id = 99999")
    
    pg_conn.commit()
    print("✅ PostgreSQL 删除成功")
    
    cur.close()
    pg_conn.close()
    
    # 2. 等待同步
    print("⏳ 等待同步...")
    time.sleep(2)
    
    # 3. 查询 Neo4j
    driver = GraphDatabase.driver(**NEO4J_CONFIG)
    with driver.session() as session:
        result = session.run("""
            MATCH (i:Invoice) 
            WHERE i.invoice_id = 99999 OR i.id = 99999
            RETURN i
        """)
        
        record = result.single()
        if record:
            print("❌ Neo4j 节点仍然存在（同步失败）")
            return False
        else:
            print("✅ Neo4j 节点已删除（同步成功）")
            return True
    
    driver.close()


def check_sync_log():
    """检查同步日志"""
    print("\n" + "="*50)
    print("📋 同步日志")
    print("="*50)
    
    pg_conn = psycopg2.connect(**PG_CONFIG)
    cur = pg_conn.cursor()
    
    cur.execute("""
        SELECT id, table_name, operation, status, sync_time
        FROM rtr_sync_log
        ORDER BY id DESC
        LIMIT 10
    """)
    
    rows = cur.fetchall()
    if rows:
        print(f"{'ID':<6} {'表名':<25} {'操作':<10} {'状态':<12} {'时间'}")
        print("-" * 80)
        for row in rows:
            print(f"{row[0]:<6} {row[1]:<25} {row[2]:<10} {row[3]:<12} {row[4]}")
    else:
        print("暂无同步日志")
    
    cur.close()
    pg_conn.close()


def main():
    """主函数"""
    print("\n" + "="*60)
    print("🚀 RTR 实时同步测试")
    print("="*60)
    
    # 检查 Neo4j 连接
    try:
        driver = GraphDatabase.driver(**NEO4J_CONFIG)
        with driver.session() as session:
            session.run("RETURN 1")
        driver.close()
        print("✅ Neo4j 连接正常")
    except Exception as e:
        print(f"❌ Neo4j 连接失败：{e}")
        print("💡 请确保 Neo4j 正在运行（端口 7687）")
        return
    
    # 检查 PostgreSQL 连接
    try:
        pg_conn = psycopg2.connect(**PG_CONFIG)
        pg_conn.close()
        print("✅ PostgreSQL 连接正常")
    except Exception as e:
        print(f"❌ PostgreSQL 连接失败：{e}")
        return
    
    # 运行测试
    results = []
    
    results.append(("INSERT", test_insert_sync()))
    time.sleep(1)
    
    results.append(("UPDATE", test_update_sync()))
    time.sleep(1)
    
    results.append(("DELETE", test_delete_sync()))
    
    # 检查同步日志
    check_sync_log()
    
    # 总结
    print("\n" + "="*60)
    print("📊 测试结果总结")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name:<10} {status}")
    
    print("-" * 60)
    print(f"总计：{passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！RTR 实时同步运行正常！")
    else:
        print(f"\n⚠️ {total - passed} 个测试失败，请检查日志")
    
    print("="*60)


if __name__ == "__main__":
    main()
