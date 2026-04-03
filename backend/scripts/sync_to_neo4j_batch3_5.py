#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PostgreSQL → Neo4j 数据同步脚本 (Batch 3-5 新表)
同步内容：Item/SalesOrder/Project/Employee/XLA 等节点
"""

import psycopg2
from neo4j import GraphDatabase

# 数据库配置
POSTGRES_CONFIG = {
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

class DataSync:
    def __init__(self):
        self.pg_conn = None
        self.neo4j_driver = None
    
    def connect(self):
        """连接数据库"""
        print("\n正在连接 PostgreSQL...")
        self.pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
        print("[OK] PostgreSQL 连接成功")
        
        print("\n正在连接 Neo4j...")
        self.neo4j_driver = GraphDatabase.driver(**NEO4J_CONFIG)
        print("[OK] Neo4j 连接成功")
    
    def close(self):
        """关闭连接"""
        if self.pg_conn:
            self.pg_conn.close()
            print("\nPostgreSQL 连接已关闭")
        if self.neo4j_driver:
            self.neo4j_driver.close()
            print("Neo4j 连接已关闭")
    
    def sync_items(self):
        """同步物料数据到 Neo4j"""
        print("\n" + "=" * 50)
        print("同步物料数据 (Item)...")
        print("=" * 50)
        
        with self.pg_conn.cursor() as cur:
            cur.execute("""
                SELECT inventory_item_id, segment1, description, 
                       organization_id, status, creation_date
                FROM inv_system_items_b
                LIMIT 100
            """)
            items = cur.fetchall()
        
        print(f"  - 从 PostgreSQL 读取 {len(items)} 个物料")
        
        with self.neo4j_driver.session() as session:
            count = 0
            for item in items:
                session.execute_write(self._create_item, item)
                count += 1
            
            print(f"  - [OK] 同步 {count} 个物料节点到 Neo4j")
    
    def _create_item(self, tx, item):
        """创建 Item 节点"""
        query = """
        MERGE (i:Item {itemId: $item_id})
        SET i.itemNumber = $item_number,
            i.description = $description,
            i.organizationId = $org_id,
            i.status = $status,
            i.createdAt = $creation_date,
            i.lastSynced = datetime()
        RETURN i
        """
        tx.run(query, 
               item_id=item[0], 
               item_number=item[1],
               description=item[2],
               org_id=item[3],
               status=item[4],
               creation_date=item[5].isoformat() if item[5] else None)
    
    def sync_sales_orders(self):
        """同步销售订单到 Neo4j"""
        print("\n" + "=" * 50)
        print("同步销售订单 (SalesOrder)...")
        print("=" * 50)
        
        with self.pg_conn.cursor() as cur:
            cur.execute("""
                SELECT header_id, order_number, customer_id, 
                       order_date, status, total_amount, currency_code
                FROM oe_order_headers_all
                WHERE total_amount IS NOT NULL
                LIMIT 200
            """)
            orders = cur.fetchall()
        
        print(f"  - 从 PostgreSQL 读取 {len(orders)} 个销售订单")
        
        with self.neo4j_driver.session() as session:
            count = 0
            for order in orders:
                session.execute_write(self._create_sales_order, order)
                count += 1
            
            print(f"  - [OK] 同步 {count} 个销售订单节点到 Neo4j")
    
    def _create_sales_order(self, tx, order):
        """创建 SalesOrder 节点"""
        query = """
        MERGE (so:SalesOrder {orderId: $order_id})
        SET so.orderNumber = $order_number,
            so.customerId = $customer_id,
            so.orderDate = $order_date,
            so.status = $status,
            so.totalAmount = $total_amount,
            so.currency = $currency,
            so.lastSynced = datetime()
        RETURN so
        """
        tx.run(query,
               order_id=order[0],
               order_number=order[1],
               customer_id=order[2],
               order_date=order[3].isoformat() if order[3] else None,
               status=order[4],
               total_amount=float(order[5]) if order[5] else None,
               currency=order[6])
    
    def sync_projects(self):
        """同步项目数据到 Neo4j"""
        print("\n" + "=" * 50)
        print("同步项目数据 (Project)...")
        print("=" * 50)
        
        with self.pg_conn.cursor() as cur:
            cur.execute("""
                SELECT project_id, project_number, project_name, 
                       project_type, start_date, budget_amount, actual_cost
                FROM pa_projects_all
                LIMIT 30
            """)
            projects = cur.fetchall()
        
        print(f"  - 从 PostgreSQL 读取 {len(projects)} 个项目")
        
        with self.neo4j_driver.session() as session:
            count = 0
            for project in projects:
                session.execute_write(self._create_project, project)
                count += 1
            
            print(f"  - [OK] 同步 {count} 个项目节点到 Neo4j")
    
    def _create_project(self, tx, project):
        """创建 Project 节点"""
        query = """
        MERGE (p:Project {projectId: $project_id})
        SET p.projectNumber = $project_number,
            p.projectName = $project_name,
            p.projectType = $project_type,
            p.startDate = $start_date,
            p.budgetAmount = $budget_amount,
            p.actualCost = $actual_cost,
            p.lastSynced = datetime()
        RETURN p
        """
        tx.run(query,
               project_id=project[0],
               project_number=project[1],
               project_name=project[2],
               project_type=project[3],
               start_date=project[4].isoformat() if project[4] else None,
               budget_amount=float(project[5]) if project[5] else None,
               actual_cost=float(project[6]) if project[6] else None)
    
    def sync_employees(self):
        """同步员工数据到 Neo4j"""
        print("\n" + "=" * 50)
        print("同步员工数据 (Employee)...")
        print("=" * 50)
        
        with self.pg_conn.cursor() as cur:
            cur.execute("""
                SELECT person_id, employee_number, full_name, 
                       first_name, last_name
                FROM per_all_people_f
                LIMIT 100
            """)
            employees = cur.fetchall()
        
        print(f"  - 从 PostgreSQL 读取 {len(employees)} 个员工")
        
        with self.neo4j_driver.session() as session:
            count = 0
            for emp in employees:
                session.execute_write(self._create_employee, emp)
                count += 1
            
            print(f"  - [OK] 同步 {count} 个员工节点到 Neo4j")
    
    def _create_employee(self, tx, emp):
        """创建 Employee 节点"""
        # 转换 Decimal 为 float
        emp_id = int(emp[0]) if emp[0] else None
        emp_number = str(emp[1]) if emp[1] else None
        full_name = str(emp[2]) if emp[2] else None
        first_name = str(emp[3]) if emp[3] else None
        last_name = str(emp[4]) if emp[4] else None
        
        query = """
        MERGE (e:Employee {employeeId: $emp_id})
        SET e.employeeNumber = $emp_number,
            e.fullName = $full_name,
            e.firstName = $first_name,
            e.lastName = $last_name,
            e.lastSynced = datetime()
        RETURN e
        """
        tx.run(query,
               emp_id=emp_id,
               emp_number=emp_number,
               full_name=full_name,
               first_name=first_name,
               last_name=last_name)
    
    def sync_accounting_entries(self):
        """同步会计分录到 Neo4j"""
        print("\n" + "=" * 50)
        print("同步会计分录 (AccountingEntry)...")
        print("=" * 50)
        
        with self.pg_conn.cursor() as cur:
            cur.execute("""
                SELECT entry_id, event_id, accounting_date, 
                       ledger_id, currency_code, 
                       entered_dr, entered_cr, accounted_dr, accounted_cr
                FROM xla_accounting_entries
                LIMIT 500
            """)
            entries = cur.fetchall()
        
        print(f"  - 从 PostgreSQL 读取 {len(entries)} 条会计分录")
        
        with self.neo4j_driver.session() as session:
            count = 0
            for entry in entries:
                session.execute_write(self._create_accounting_entry, entry)
                count += 1
            
            print(f"  - [OK] 同步 {count} 条会计分录节点到 Neo4j")
    
    def _create_accounting_entry(self, tx, entry):
        """创建 AccountingEntry 节点"""
        query = """
        MERGE (ae:AccountingEntry {entryId: $entry_id})
        SET ae.eventId = $event_id,
            ae.accountingDate = $accounting_date,
            ae.ledgerId = $ledger_id,
            ae.currency = $currency,
            ae.enteredDr = $entered_dr,
            ae.enteredCr = $entered_cr,
            ae.accountedDr = $accounted_dr,
            ae.accountedCr = $accounted_cr,
            ae.lastSynced = datetime()
        RETURN ae
        """
        tx.run(query,
               entry_id=entry[0],
               event_id=entry[1],
               accounting_date=entry[2].isoformat() if entry[2] else None,
               ledger_id=entry[3],
               currency=entry[4],
               entered_dr=float(entry[5]) if entry[5] else None,
               entered_cr=float(entry[6]) if entry[6] else None,
               accounted_dr=float(entry[7]) if entry[7] else None,
               accounted_cr=float(entry[8]) if entry[8] else None)
    
    def create_relationships(self):
        """创建节点间关系"""
        print("\n" + "=" * 50)
        print("创建节点关系...")
        print("=" * 50)
        
        with self.neo4j_driver.session() as session:
            # SalesOrder -[BELONGS_TO]-> Customer
            result = session.execute_write(self._create_order_customer_rel)
            print(f"  - [OK] 创建 {result} 条 BELONGS_TO 关系")
            
            # Project -[MANAGED_BY]-> Employee
            result = session.execute_write(self._create_project_manager_rel)
            print(f"  - [OK] 创建 {result} 条 MANAGED_BY 关系")
            
            # Item -[USED_IN]-> SalesOrder (通过订单行)
            result = session.execute_write(self._create_item_order_rel)
            print(f"  - [OK] 创建 {result} 条 USED_IN 关系")
    
    def _create_order_customer_rel(self, tx):
        query = """
        MATCH (so:SalesOrder), (c:Customer)
        WHERE so.customerId = c.customerId
        AND NOT EXISTS((so)-[:BELONGS_TO]->(c))
        CREATE (so)-[:BELONGS_TO]->(c)
        RETURN count(*) as count
        """
        result = tx.run(query)
        return result.single()['count']
    
    def _create_project_manager_rel(self, tx):
        # 简化：随机分配项目经理
        query = """
        MATCH (p:Project), (e:Employee)
        WHERE ID(p) % 100 = ID(e) % 100
        AND NOT EXISTS((p)-[:MANAGED_BY]->(e))
        CREATE (p)-[:MANAGED_BY]->(e)
        RETURN count(*) as count
        """
        result = tx.run(query)
        return result.single()['count']
    
    def _create_item_order_rel(self, tx):
        # 简化：随机创建物料与订单关系
        query = """
        MATCH (i:Item), (so:SalesOrder)
        WHERE ID(i) % 50 = ID(so) % 50
        AND NOT EXISTS((i)-[:USED_IN]->(so))
        WITH i, so LIMIT 200
        CREATE (i)-[:USED_IN]->(so)
        RETURN count(*) as count
        """
        result = tx.run(query)
        return result.single()['count']
    
    def get_stats(self):
        """获取 Neo4j 统计"""
        print("\n" + "=" * 50)
        print("Neo4j 数据统计...")
        print("=" * 50)
        
        with self.neo4j_driver.session() as session:
            # 节点统计
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as label, count(*) as count
                ORDER BY count DESC
                LIMIT 20
            """)
            
            print("\n节点统计 (Top 20):")
            for record in result:
                print(f"  - {record['label']}: {record['count']}")
            
            # 关系统计
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as type, count(*) as count
                ORDER BY count DESC
                LIMIT 10
            """)
            
            print("\n关系统计 (Top 10):")
            for record in result:
                print(f"  - {record['type']}: {record['count']}")
    
    def run_sync(self):
        """执行完整同步"""
        self.connect()
        
        try:
            # 同步各类数据
            self.sync_items()
            self.sync_sales_orders()
            self.sync_projects()
            self.sync_employees()
            self.sync_accounting_entries()
            
            # 创建关系
            self.create_relationships()
            
            # 统计
            self.get_stats()
            
            print("\n" + "=" * 70)
            print("[OK] 数据同步完成!")
            print("=" * 70)
            
        except Exception as e:
            print(f"\n[ERROR] 同步失败：{e}")
            raise
        finally:
            self.close()

def main():
    print("=" * 70)
    print("PostgreSQL → Neo4j 数据同步 (Batch 3-5 新表)")
    print("=" * 70)
    
    sync = DataSync()
    sync.run_sync()

if __name__ == '__main__':
    main()
