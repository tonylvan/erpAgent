# -*- coding: utf-8 -*-
"""
RTR 实时同步消费者 - 最终可靠版
使用同步 psycopg2，避免异步问题
"""

import psycopg2
import json
import time
import sys
from datetime import datetime
from decimal import Decimal

from dotenv import load_dotenv
load_dotenv()
import os

# 配置
PG_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'database': os.getenv('POSTGRES_DB', 'erp'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
}

NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'Tony1985')

from neo4j import GraphDatabase

# 表映射
TABLE_MAPPING = {
    'ap_invoices_all': 'Invoice',
    'ap_payments_all': 'Payment',
    'po_headers_all': 'PurchaseOrder',
    'po_lines_all': 'POLine'
}

# 主键映射
PK_MAPPING = {
    'ap_invoices_all': 'invoice_id',
    'ap_payments_all': 'payment_id',
    'po_headers_all': 'po_header_id',
    'po_lines_all': 'po_line_id'
}

print("="*60)
print("RTR Sync Consumer - Final Version")
print("="*60)
print(f"PostgreSQL: {PG_CONFIG['host']}:{PG_CONFIG['port']}/{PG_CONFIG['database']}")
print(f"Neo4j: {NEO4J_URI}")
print("="*60)

# 连接数据库
print("[1/3] Connecting to PostgreSQL...")
pg_conn = psycopg2.connect(**PG_CONFIG)
pg_conn.autocommit = True
pg_cur = pg_conn.cursor()
print("      [OK] PostgreSQL connected")

print("[2/3] Connecting to Neo4j...")
neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
print("      [OK] Neo4j connected")

print("[3/3] Subscribing to channel...")
pg_cur.execute("LISTEN neo4j_rtr_sync;")
pg_conn.commit()
print("      [OK] Subscribed to neo4j_rtr_sync")

print("\n" + "="*60)
print("Listening for changes... (Press Ctrl+C to stop)")
print("="*60 + "\n")

stats = {'insert': 0, 'update': 0, 'delete': 0, 'error': 0}

def clean_data(data):
    """清理数据为 Neo4j 兼容格式"""
    if not data:
        return {}
    cleaned = {}
    for k, v in data.items():
        if v is None:
            continue
        if isinstance(v, Decimal):
            cleaned[k] = float(v)
        elif isinstance(v, datetime):
            cleaned[k] = v.isoformat()
        else:
            cleaned[k] = v
    return cleaned

def sync_to_neo4j(table, operation, data):
    """同步数据到 Neo4j"""
    if table not in TABLE_MAPPING:
        print(f"  [SKIP] Table not mapped: {table}")
        return
    
    label = TABLE_MAPPING[table]
    pk_field = PK_MAPPING.get(table, 'id')
    cleaned = clean_data(data)
    
    if not cleaned:
        print(f"  [SKIP] No data to sync")
        return
    
    pk_value = cleaned.get(pk_field)
    
    with neo4j_driver.session() as session:
        try:
            if operation == 'INSERT':
                # 创建节点
                props_str = ', '.join([f'{k}: ${k}' for k in cleaned.keys()])
                query = f"CREATE (n:{label} {{{props_str}}})"
                session.run(query, **cleaned)
                print(f"  [CREATE] {label} with {pk_field}={pk_value}")
                
            elif operation == 'UPDATE':
                # 先查找是否存在
                find_query = f"MATCH (n:{label}) WHERE n.{pk_field} = $pk_id RETURN n LIMIT 1"
                result = session.run(find_query, pk_id=pk_value)
                record = result.single()
                
                if record:
                    # 更新
                    set_parts = []
                    params = {'pk_id': pk_value}
                    for i, (k, v) in enumerate(cleaned.items()):
                        if k != pk_field:
                            set_parts.append(f"n.{k} = $p{i}")
                            params[f'p{i}'] = v
                    
                    if set_parts:
                        query = f"MATCH (n:{label}) WHERE n.{pk_field} = $pk_id SET {', '.join(set_parts)}"
                        session.run(query, **params)
                        print(f"  [UPDATE] {label} with {pk_field}={pk_value}")
                else:
                    # 不存在则创建
                    props_str = ', '.join([f'{k}: ${k}' for k in cleaned.keys()])
                    query = f"CREATE (n:{label} {{{props_str}}})"
                    session.run(query, **cleaned)
                    print(f"  [CREATE] {label} with {pk_field}={pk_value} (not found)")
                    
            elif operation == 'DELETE':
                # 删除节点
                query = f"MATCH (n:{label}) WHERE n.{pk_field} = $pk_id DETACH DELETE n"
                result = session.run(query, pk_id=pk_value)
                deleted = result.summary().counters.nodes_deleted
                print(f"  [DELETE] {deleted} node(s)")
            
            stats[operation.lower()] += 1
            return True
            
        except Exception as e:
            print(f"  [ERROR] {e}")
            stats['error'] += 1
            return False

def update_log_status(table, operation, status):
    """更新同步日志状态"""
    try:
        pg_cur.execute("""
            UPDATE rtr_sync_log SET status = %s 
            WHERE table_name = %s AND operation = %s 
            ORDER BY id DESC LIMIT 1
        """, (status, table, operation))
        pg_conn.commit()
    except Exception as e:
        print(f"  [WARN] Failed to update log: {e}")

# 主循环
try:
    while True:
        pg_conn.poll()
        
        while pg_conn.notifies:
            notify = pg_conn.notifies.pop(0)
            timestamp = time.strftime('%H:%M:%S')
            
            print(f"[{timestamp}] RECV: {notify.payload}")
            
            try:
                data = json.loads(notify.payload)
                table = data.get('table')
                operation = data.get('operation')
                record = data.get('new') or data.get('old')
                
                print(f"         Table={table}, Op={operation}")
                
                # 同步到 Neo4j
                success = sync_to_neo4j(table, operation, record)
                
                # 更新日志
                if success:
                    update_log_status(table, operation, 'completed')
                else:
                    update_log_status(table, operation, 'failed')
                    
            except json.JSONDecodeError as e:
                print(f"  [ERROR] JSON decode: {e}")
                stats['error'] += 1
            except Exception as e:
                print(f"  [ERROR] Process: {e}")
                stats['error'] += 1
        
        time.sleep(0.1)
        
except KeyboardInterrupt:
    print("\n\n" + "="*60)
    print("Stopping...")
    print("="*60)
    print(f"\nStatistics:")
    print(f"  INSERT: {stats['insert']}")
    print(f"  UPDATE: {stats['update']}")
    print(f"  DELETE: {stats['delete']}")
    print(f"  ERROR:  {stats['error']}")
    print(f"  TOTAL:  {stats['insert'] + stats['update'] + stats['delete']}")
    print("\n" + "="*60)

finally:
    pg_cur.close()
    pg_conn.close()
    neo4j_driver.close()
    print("[OK] Connections closed")
