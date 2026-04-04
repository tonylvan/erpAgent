# -*- coding: utf-8 -*-
"""
RTR 实时同步消费者
方案 B: PostgreSQL 触发器 → Redis Pub/Sub → Neo4j 消费者
延迟：1-2 秒
"""

import asyncio
import json
import sys
from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any

import psycopg2
from psycopg2 import sql
from neo4j import AsyncGraphDatabase
import redis.asyncio as redis

# ============================================
# 配置
# ============================================
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

REDIS_CONFIG = {
    'host': 'localhost',
    'port': 6379,
    'db': 0
}

# 表到 Neo4j 标签的映射
TABLE_MAPPING = {
    'ap_invoices_all': 'Invoice',
    'ap_payments_all': 'Payment',
    'ap_invoice_po_matches': 'InvoicePOMatch',
    'po_headers_all': 'PurchaseOrder',
    'po_lines_all': 'POLine',
    'po_distributions_all': 'PODistribution',
    'ar_transactions_all': 'ARTransaction',
    'ar_payments_all': 'ARPayment',
    'suppliers': 'Supplier',
    'customers': 'Customer',
    'sales_orders_all': 'SalesOrder',
    'sales_order_lines_all': 'SalesOrderLine',
    'items': 'Product',
    'item_organizations': 'ProductOrg'
}

# 主键字段映射
PRIMARY_KEY_MAPPING = {
    'ap_invoices_all': 'invoice_id',
    'ap_payments_all': 'payment_id',
    'ap_invoice_po_matches': 'match_id',
    'po_headers_all': 'po_header_id',
    'po_lines_all': 'po_line_id',
    'po_distributions_all': 'po_distribution_id',
    'ar_transactions_all': 'transaction_id',
    'ar_payments_all': 'payment_id',
    'suppliers': 'vendor_id',
    'customers': 'customer_id',
    'sales_orders_all': 'order_id',
    'sales_order_lines_all': 'order_line_id',
    'items': 'inventory_item_id',
    'item_organizations': 'organization_id'
}


class DecimalEncoder(json.JSONEncoder):
    """JSON 编码器，支持 Decimal 类型"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


class RTRSyncConsumer:
    """RTR 实时同步消费者"""
    
    def __init__(self):
        self.pg_conn = None
        self.pg_cursor = None
        self.neo4j_driver = None
        self.redis_client = None
        self.stats = {
            'insert': 0,
            'update': 0,
            'delete': 0,
            'error': 0,
            'start_time': datetime.now()
        }
        
    async def connect(self):
        """建立数据库连接"""
        print("🔌 正在连接数据库...")
        
        # PostgreSQL 连接
        self.pg_conn = psycopg2.connect(**PG_CONFIG)
        self.pg_cursor = self.pg_conn.cursor()
        print("✅ PostgreSQL 连接成功")
        
        # Neo4j 连接
        self.neo4j_driver = AsyncGraphDatabase.driver(**NEO4J_CONFIG)
        print("✅ Neo4j 连接成功")
        
        # Redis 连接
        self.redis_client = redis.Redis(**REDIS_CONFIG)
        await self.redis_client.ping()
        print("✅ Redis 连接成功")
        
    async def disconnect(self):
        """关闭数据库连接"""
        if self.pg_cursor:
            self.pg_cursor.close()
        if self.pg_conn:
            self.pg_conn.close()
        if self.neo4j_driver:
            await self.neo4j_driver.close()
        if self.redis_client:
            await self.redis_client.close()
        print("🔌 数据库连接已关闭")
        
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
            elif isinstance(value, (list, dict)):
                cleaned[key] = json.dumps(value, cls=DecimalEncoder)
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
                    # 创建节点
                    query = f"CREATE (n:{label} $props)"
                    await session.run(query, props=cleaned_data)
                    
                elif operation == 'UPDATE':
                    # 更新节点（需要主键）
                    pk_value = self.get_primary_key(label.lower(), cleaned_data)
                    if pk_value:
                        # 查找并更新
                        match_query = f"MATCH (n:{label}) WHERE n.id = $pk_id OR n.{list(cleaned_data.keys())[0]} = $pk_id SET n += $props"
                        await session.run(match_query, pk_id=pk_value, props=cleaned_data)
                    else:
                        # 没有主键则创建
                        query = f"CREATE (n:{label} $props)"
                        await session.run(query, props=cleaned_data)
                    
                elif operation == 'DELETE':
                    # 删除节点（需要主键）
                    pk_value = self.get_primary_key(label.lower(), cleaned_data)
                    if pk_value:
                        query = f"MATCH (n:{label}) WHERE n.id = $pk_id DETACH DELETE n"
                        result = await session.run(query, pk_id=pk_value)
                        print(f"🗑️ 删除了 {result.summary().counters.nodes_deleted} 个节点")
                    
            except Exception as e:
                print(f"❌ Neo4j 同步失败：{e}")
                raise
    
    def update_sync_log(self, table: str, operation: str, status: str, log_id: int = None):
        """更新同步日志"""
        try:
            if log_id:
                self.pg_cursor.execute("""
                    UPDATE rtr_sync_log SET status = %s WHERE id = %s
                """, (status, log_id))
            else:
                self.pg_cursor.execute("""
                    UPDATE rtr_sync_log SET status = %s 
                    WHERE table_name = %s AND operation = %s 
                    ORDER BY id DESC LIMIT 1
                """, (status, table, operation))
            self.pg_conn.commit()
        except Exception as e:
            print(f"⚠️ 更新日志失败：{e}")
    
    async def process_change(self, channel: str, data: str):
        """处理数据变更"""
        try:
            change = json.loads(data)
            table = change['table']
            operation = change['operation']
            record = change.get('new') or change.get('old')
            
            print(f"\n📨 收到变更：{table} - {operation}")
            
            if table not in TABLE_MAPPING:
                print(f"⚠️ 未映射的表：{table}")
                self.update_sync_log(table, operation, 'skipped')
                return
            
            label = TABLE_MAPPING[table]
            
            # 同步到 Neo4j
            await self.sync_node(label, record, operation)
            
            # 更新日志
            self.update_sync_log(table, operation, 'completed')
            
            # 统计
            self.stats[operation.lower()] += 1
            print(f"✅ 同步成功：{label} {operation}")
            
        except json.JSONDecodeError as e:
            print(f"❌ JSON 解析失败：{e}")
            self.stats['error'] += 1
        except Exception as e:
            print(f"❌ 同步失败：{e}")
            self.stats['error'] += 1
            self.update_sync_log('unknown', 'unknown', 'failed')
    
    async def listen(self):
        """监听 PostgreSQL 通知"""
        print("\n" + "="*50)
        print("🎧 RTR 实时同步消费者启动")
        print("="*50)
        print(f"📍 PostgreSQL: {PG_CONFIG['host']}:{PG_CONFIG['port']}/{PG_CONFIG['database']}")
        print(f"📍 Neo4j: {NEO4J_CONFIG['uri']}")
        print(f"📍 Redis: {REDIS_CONFIG['host']}:{REDIS_CONFIG['port']}")
        print("="*50)
        
        # 订阅频道
        self.pg_cursor.execute("LISTEN neo4j_rtr_sync;")
        self.pg_conn.commit()
        print("✅ 已订阅频道：neo4j_rtr_sync")
        print("🎧 开始监听 PostgreSQL 通知...\n")
        
        while True:
            try:
                # 轮询通知
                self.pg_conn.poll()
                while self.pg_conn.notifies:
                    notify = self.pg_conn.notifies.pop(0)
                    await self.process_change(notify.channel, notify.payload)
                
                # 短暂休眠，避免 CPU 占用过高
                await asyncio.sleep(0.1)
                
            except KeyboardInterrupt:
                print("\n\n🛑 用户中断，正在停止...")
                break
            except Exception as e:
                print(f"❌ 监听错误：{e}")
                await asyncio.sleep(1)
        
        # 打印统计
        self.print_stats()
    
    def print_stats(self):
        """打印统计信息"""
        print("\n" + "="*50)
        print("📊 RTR 同步统计")
        print("="*50)
        print(f"⏱️  运行时长：{datetime.now() - self.stats['start_time']}")
        print(f"✅ INSERT: {self.stats['insert']}")
        print(f"✅ UPDATE: {self.stats['update']}")
        print(f"✅ DELETE: {self.stats['delete']}")
        print(f"❌ ERROR: {self.stats['error']}")
        print(f"📈 总计：{self.stats['insert'] + self.stats['update'] + self.stats['delete']}")
        print("="*50)
    
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
        print("\n👋 再见！")
