# -*- coding: utf-8 -*-
"""
RTR 实时同步消费者 - 修复版
使用 .env 文件读取配置，避免编码问题
"""

import asyncio
import json
import sys
import os
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any

from dotenv import load_dotenv
load_dotenv()  # 加载 .env 文件

import psycopg2
from neo4j import AsyncGraphDatabase

# ============================================
# 从 .env 读取配置
# ============================================
PG_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': int(os.getenv('POSTGRES_PORT', 5432)),
    'database': os.getenv('POSTGRES_DB', 'erp'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
}

NEO4J_CONFIG = {
    'uri': os.getenv('NEO4J_URI', 'bolt://localhost:7687'),
    'auth': (
        os.getenv('NEO4J_USER', 'neo4j'),
        os.getenv('NEO4J_PASSWORD', 'Tony1985')
    )
}

# 表到 Neo4j 标签的映射
TABLE_MAPPING = {
    'ap_invoices_all': 'Invoice',
    'ap_payments_all': 'Payment',
    'po_headers_all': 'PurchaseOrder',
    'po_lines_all': 'POLine'
}

# 主键字段映射
PRIMARY_KEY_MAPPING = {
    'ap_invoices_all': 'invoice_id',
    'ap_payments_all': 'payment_id',
    'po_headers_all': 'po_header_id',
    'po_lines_all': 'po_line_id'
}


class RTRSyncConsumer:
    """RTR 实时同步消费者"""
    
    def __init__(self):
        self.pg_conn = None
        self.pg_cursor = None
        self.neo4j_driver = None
        self.stats = {
            'insert': 0,
            'update': 0,
            'delete': 0,
            'error': 0,
            'start_time': datetime.now()
        }
        
    async def connect(self):
        """建立数据库连接"""
        print("="*60)
        print("RTR 实时同步消费者启动")
        print("="*60)
        print(f"PostgreSQL: {PG_CONFIG['host']}:{PG_CONFIG['port']}/{PG_CONFIG['database']}")
        print(f"Neo4j: {NEO4J_CONFIG['uri']}")
        print("="*60)
        
        # PostgreSQL 连接
        self.pg_conn = psycopg2.connect(**PG_CONFIG)
        self.pg_cursor = self.pg_conn.cursor()
        print("[OK] PostgreSQL 连接成功")
        
        # Neo4j 连接
        self.neo4j_driver = AsyncGraphDatabase.driver(**NEO4J_CONFIG)
        print("[OK] Neo4j 连接成功")
        
    async def disconnect(self):
        """关闭数据库连接"""
        if self.pg_cursor:
            self.pg_cursor.close()
        if self.pg_conn:
            self.pg_conn.close()
        if self.neo4j_driver:
            await self.neo4j_driver.close()
        print("[OK] 数据库连接已关闭")
        
    def clean_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """清理数据，转换为 Neo4j 兼容格式"""
        if not data:
            return {}
        
        cleaned = {}
        for key, value in data.items():
            if value is None:
                continue
            if isinstance(value, Decimal):
                cleaned[key] = float(value)
            elif isinstance(value, datetime):
                cleaned[key] = value.isoformat()
            else:
                cleaned[key] = value
        return cleaned
    
    def get_primary_key(self, table: str, data: Dict[str, Any]) -> Optional[Any]:
        """获取主键值"""
        pk_field = PRIMARY_KEY_MAPPING.get(table)
        if pk_field:
            return data.get(pk_field)
        return data.get('id')
    
    async def sync_node(self, label: str, data: Dict[str, Any], operation: str):
        """同步节点到 Neo4j"""
        if not data:
            return
        
        cleaned_data = self.clean_data(data)
        
        async with self.neo4j_driver.session() as session:
            try:
                if operation == 'INSERT':
                    query = f"CREATE (n:{label} $props)"
                    await session.run(query, props=cleaned_data)
                    print(f"  [CREATE] {label} node created")
                    
                elif operation == 'UPDATE':
                    pk_value = self.get_primary_key(label.lower(), cleaned_data)
                    if pk_value:
                        # 先查找是否存在
                        result = await session.run(
                            f"MATCH (n:{label}) WHERE n.invoice_id = $pk_id OR n.payment_id = $pk_id OR n.po_header_id = $pk_id OR n.po_line_id = $pk_id RETURN n LIMIT 1",
                            pk_id=pk_value
                        )
                        record = await result.single()
                        
                        if record:
                            # 更新现有节点
                            set_clauses = []
                            params = {'pk_id': pk_value}
                            for i, (key, value) in enumerate(cleaned_data.items()):
                                set_clauses.append(f"n.{key} = $p{i}")
                                params[f'p{i}'] = value
                            
                            query = f"MATCH (n:{label}) WHERE n.invoice_id = $pk_id OR n.payment_id = $pk_id OR n.po_header_id = $pk_id OR n.po_line_id = $pk_id SET {', '.join(set_clauses)}"
                            await session.run(query, **params)
                            print(f"  [UPDATE] {label} node updated")
                        else:
                            # 创建新节点
                            query = f"CREATE (n:{label} $props)"
                            await session.run(query, props=cleaned_data)
                            print(f"  [CREATE] {label} node created (not found)")
                    
                elif operation == 'DELETE':
                    pk_value = self.get_primary_key(label.lower(), cleaned_data)
                    if pk_value:
                        query = f"MATCH (n:{label}) WHERE n.invoice_id = $pk_id OR n.payment_id = $pk_id OR n.po_header_id = $pk_id OR n.po_line_id = $pk_id DETACH DELETE n"
                        result = await session.run(query, pk_id=pk_value)
                        deleted = result.summary().counters.nodes_deleted
                        print(f"  [DELETE] {deleted} node(s) deleted")
                    
            except Exception as e:
                print(f"  [ERROR] Neo4j sync failed: {e}")
                raise
    
    def update_sync_log(self, table: str, operation: str, status: str):
        """更新同步日志"""
        try:
            self.pg_cursor.execute("""
                UPDATE rtr_sync_log SET status = %s 
                WHERE table_name = %s AND operation = %s 
                ORDER BY id DESC LIMIT 1
            """, (status, table, operation))
            self.pg_conn.commit()
        except Exception as e:
            print(f"  [WARN] Failed to update log: {e}")
    
    async def process_change(self, channel: str, data: str):
        """处理数据变更"""
        try:
            change = json.loads(data)
            table = change['table']
            operation = change['operation']
            record = change.get('new') or change.get('old')
            
            print(f"\n[RECV] {table} - {operation}")
            
            if table not in TABLE_MAPPING:
                print(f"  [SKIP] Table not mapped: {table}")
                return
            
            label = TABLE_MAPPING[table]
            
            # 同步到 Neo4j
            await self.sync_node(label, record, operation)
            
            # 更新日志
            self.update_sync_log(table, operation, 'completed')
            
            # 统计
            self.stats[operation.lower()] += 1
            print(f"  [OK] Sync completed")
            
        except json.JSONDecodeError as e:
            print(f"  [ERROR] JSON decode failed: {e}")
            self.stats['error'] += 1
        except Exception as e:
            print(f"  [ERROR] Sync failed: {e}")
            self.stats['error'] += 1
    
    async def listen(self):
        """监听 PostgreSQL 通知"""
        # 订阅频道
        self.pg_cursor.execute("LISTEN neo4j_rtr_sync;")
        self.pg_conn.commit()
        print("[OK] Subscribed to channel: neo4j_rtr_sync")
        print("[LISTEN] Waiting for notifications...\n")
        
        while True:
            try:
                self.pg_conn.poll()
                while self.pg_conn.notifies:
                    notify = self.pg_conn.notifies.pop(0)
                    await self.process_change(notify.channel, notify.payload)
                
                await asyncio.sleep(0.1)
                
            except KeyboardInterrupt:
                print("\n\n[STOP] User interrupted")
                break
            except Exception as e:
                print(f"[ERROR] Listen error: {e}")
                await asyncio.sleep(1)
        
        self.print_stats()
    
    def print_stats(self):
        """打印统计信息"""
        print("\n" + "="*60)
        print("RTR Sync Statistics")
        print("="*60)
        print(f"Duration: {datetime.now() - self.stats['start_time']}")
        print(f"INSERT: {self.stats['insert']}")
        print(f"UPDATE: {self.stats['update']}")
        print(f"DELETE: {self.stats['delete']}")
        print(f"ERROR: {self.stats['error']}")
        print(f"TOTAL: {self.stats['insert'] + self.stats['update'] + self.stats['delete']}")
        print("="*60)
    
    async def run(self):
        """运行消费者"""
        try:
            await self.connect()
            await self.listen()
        finally:
            await self.disconnect()


async def main():
    """主函数"""
    consumer = RTRSyncConsumer()
    await consumer.run()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[BYE] Goodbye!")
