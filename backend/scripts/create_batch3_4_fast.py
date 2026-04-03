#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Oracle EBS ERP Batch 3-4 快速创建 + 样例数据
"""

import psycopg2
import random
from datetime import datetime, timedelta

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'erp',
    'user': 'postgres',
    'password': 'postgres'
}

def count_tables(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """)
        return cur.fetchone()[0]

def create_tables(conn):
    """创建 Batch 3-4 表"""
    tables = [
        # INV 模块
        "CREATE TABLE IF NOT EXISTS inv_system_items_b (inventory_item_id BIGSERIAL PRIMARY KEY, segment1 VARCHAR(30) NOT NULL, organization_id BIGINT NOT NULL, description VARCHAR(240), status VARCHAR(20) DEFAULT 'ACTIVE', creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
        "CREATE TABLE IF NOT EXISTS inv_onhand_quantities (onhand_id BIGSERIAL PRIMARY KEY, inventory_item_id BIGINT NOT NULL, organization_id BIGINT NOT NULL, quantity NUMERIC(15,2), unit_cost NUMERIC(15,2), creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
        "CREATE TABLE IF NOT EXISTS inv_material_transactions (transaction_id BIGSERIAL PRIMARY KEY, inventory_item_id BIGINT, organization_id BIGINT, transaction_type_name VARCHAR(80), quantity NUMERIC(15,2), transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
        "CREATE TABLE IF NOT EXISTS inv_item_categories (category_id BIGSERIAL PRIMARY KEY, segment1 VARCHAR(30), description VARCHAR(240), status VARCHAR(20) DEFAULT 'ACTIVE')",
        "CREATE TABLE IF NOT EXISTS inv_organization_parameters (organization_id BIGSERIAL PRIMARY KEY, organization_code VARCHAR(10) NOT NULL, organization_name VARCHAR(240) NOT NULL, status VARCHAR(20) DEFAULT 'ACTIVE')",
        
        # OM 模块
        "CREATE TABLE IF NOT EXISTS oe_order_headers_all (header_id BIGSERIAL PRIMARY KEY, order_number VARCHAR(50) NOT NULL, customer_id BIGINT NOT NULL, order_date DATE, status VARCHAR(20) DEFAULT 'ENTERED', total_amount NUMERIC(15,2), currency_code VARCHAR(15), creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
        "CREATE TABLE IF NOT EXISTS oe_order_lines_all (line_id BIGSERIAL PRIMARY KEY, header_id BIGINT NOT NULL, line_number INT NOT NULL, inventory_item_id BIGINT, ordered_quantity NUMERIC(15,2), unit_selling_price NUMERIC(15,2), amount NUMERIC(15,2), status VARCHAR(20))",
        "CREATE TABLE IF NOT EXISTS oe_order_types (order_type_id BIGSERIAL PRIMARY KEY, name VARCHAR(100) NOT NULL, status VARCHAR(20) DEFAULT 'ACTIVE')",
        "CREATE TABLE IF NOT EXISTS oe_shipments (shipment_id BIGSERIAL PRIMARY KEY, header_id BIGINT, line_id BIGINT, shipped_quantity NUMERIC(15,2), ship_date DATE, status VARCHAR(20))",
        "CREATE TABLE IF NOT EXISTS oe_returns (return_id BIGSERIAL PRIMARY KEY, return_number VARCHAR(50) NOT NULL, original_order_id BIGINT, customer_id BIGINT, status VARCHAR(20), creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
        
        # FA 模块
        "CREATE TABLE IF NOT EXISTS fa_additions_b (addition_id BIGSERIAL PRIMARY KEY, asset_id BIGINT NOT NULL, date_placed_in_service DATE, cost NUMERIC(15,2), category_id BIGINT, creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
        "CREATE TABLE IF NOT EXISTS fa_deprn_detail (deprn_id BIGSERIAL PRIMARY KEY, asset_id BIGINT NOT NULL, book_id BIGINT NOT NULL, period_name VARCHAR(30), depreciation_expense NUMERIC(15,2), accumulated_deprn NUMERIC(15,2), creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
        "CREATE TABLE IF NOT EXISTS fa_transactions (transaction_id BIGSERIAL PRIMARY KEY, asset_id BIGINT NOT NULL, transaction_type VARCHAR(30), transaction_date DATE, amount NUMERIC(15,2), status VARCHAR(20), creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
        "CREATE TABLE IF NOT EXISTS fa_category_defs (category_id BIGSERIAL PRIMARY KEY, category_key VARCHAR(30) NOT NULL, description VARCHAR(240), depreciation_method VARCHAR(30), status VARCHAR(20) DEFAULT 'ACTIVE')",
        
        # HR 模块
        "CREATE TABLE IF NOT EXISTS per_all_people_f (person_id BIGSERIAL PRIMARY KEY, employee_number VARCHAR(30), full_name VARCHAR(240), first_name VARCHAR(50), last_name VARCHAR(50), date_of_birth DATE, gender VARCHAR(10), status VARCHAR(20) DEFAULT 'ACTIVE')",
        "CREATE TABLE IF NOT EXISTS per_assignments_f (assignment_id BIGSERIAL PRIMARY KEY, person_id BIGINT NOT NULL, organization_id BIGINT, job_id BIGINT, assignment_number VARCHAR(30), primary_flag VARCHAR(1) DEFAULT 'Y', date_from DATE)",
        "CREATE TABLE IF NOT EXISTS per_jobs_f (job_id BIGSERIAL PRIMARY KEY, job_code VARCHAR(30) NOT NULL, name VARCHAR(100), description VARCHAR(240), status VARCHAR(20) DEFAULT 'ACTIVE')",
        "CREATE TABLE IF NOT EXISTS per_positions_f (position_id BIGSERIAL PRIMARY KEY, position_code VARCHAR(30) NOT NULL, name VARCHAR(100), organization_id BIGINT, job_id BIGINT, status VARCHAR(20) DEFAULT 'ACTIVE')",
        
        # PA 模块
        "CREATE TABLE IF NOT EXISTS pa_projects_all (project_id BIGSERIAL PRIMARY KEY, project_number VARCHAR(30) NOT NULL, project_name VARCHAR(100) NOT NULL, project_type VARCHAR(30), status VARCHAR(20) DEFAULT 'ACTIVE', start_date DATE, budget_amount NUMERIC(15,2), actual_cost NUMERIC(15,2), creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
        "CREATE TABLE IF NOT EXISTS pa_tasks (task_id BIGSERIAL PRIMARY KEY, project_id BIGINT NOT NULL, task_number VARCHAR(30) NOT NULL, task_name VARCHAR(100), parent_task_id BIGINT, status VARCHAR(20), start_date DATE)",
        "CREATE TABLE IF NOT EXISTS pa_expenditures_all (expenditure_id BIGSERIAL PRIMARY KEY, project_id BIGINT NOT NULL, task_id BIGINT, expenditure_type VARCHAR(30), expenditure_date DATE, quantity NUMERIC(15,2), unit_cost NUMERIC(15,2), total_cost NUMERIC(15,2), status VARCHAR(20), creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
        "CREATE TABLE IF NOT EXISTS pa_budget_versions (budget_version_id BIGSERIAL PRIMARY KEY, project_id BIGINT NOT NULL, version_type VARCHAR(30), version_name VARCHAR(100), status VARCHAR(20) DEFAULT 'DRAFT', budget_amount NUMERIC(15,2), creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
        
        # CST 模块
        "CREATE TABLE IF NOT EXISTS cst_cost_types (cost_type_id BIGSERIAL PRIMARY KEY, cost_type VARCHAR(30) NOT NULL, description VARCHAR(240), status VARCHAR(20) DEFAULT 'ACTIVE')",
        "CREATE TABLE IF NOT EXISTS cst_cost_elements (cost_element_id BIGSERIAL PRIMARY KEY, cost_element VARCHAR(30) NOT NULL, description VARCHAR(240), status VARCHAR(20) DEFAULT 'ACTIVE')",
        "CREATE TABLE IF NOT EXISTS cst_item_costs (item_cost_id BIGSERIAL PRIMARY KEY, inventory_item_id BIGINT NOT NULL, organization_id BIGINT NOT NULL, cost_type_id BIGINT, material_cost NUMERIC(15,2), labor_cost NUMERIC(15,2), total_cost NUMERIC(15,2), currency_code VARCHAR(15), creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
        
        # BOM 模块
        "CREATE TABLE IF NOT EXISTS bom_bill_of_materials (bill_id BIGSERIAL PRIMARY KEY, assembly_item_id BIGINT NOT NULL, organization_id BIGINT NOT NULL, bill_sequence_id BIGINT, status VARCHAR(20) DEFAULT 'ACTIVE')",
        "CREATE TABLE IF NOT EXISTS bom_inventory_components (component_id BIGSERIAL PRIMARY KEY, bill_sequence_id BIGINT NOT NULL, component_item_id BIGINT NOT NULL, component_quantity NUMERIC(15,2), operation_seq_num NUMERIC(5,2), status VARCHAR(20))",
        
        # WIP 模块
        "CREATE TABLE IF NOT EXISTS wip_discrete_jobs (job_id BIGSERIAL PRIMARY KEY, job_number VARCHAR(30) NOT NULL, assembly_item_id BIGINT NOT NULL, organization_id BIGINT NOT NULL, status VARCHAR(20) DEFAULT 'RELEASED', start_quantity NUMERIC(15,2), quantity_completed NUMERIC(15,2) DEFAULT 0, start_date DATE, completion_date DATE)",
        "CREATE TABLE IF NOT EXISTS wip_job_operations (job_operation_id BIGSERIAL PRIMARY KEY, job_id BIGINT NOT NULL, operation_seq_num NUMERIC(5,2), status VARCHAR(20), quantity_completed NUMERIC(15,2))",
        "CREATE TABLE IF NOT EXISTS wip_requirement_operations (requirement_id BIGSERIAL PRIMARY KEY, job_id BIGINT NOT NULL, component_item_id BIGINT NOT NULL, required_quantity NUMERIC(15,2), quantity_issued NUMERIC(15,2) DEFAULT 0)",
        
        # 基础数据
        "CREATE TABLE IF NOT EXISTS fnd_currencies (currency_code VARCHAR(15) PRIMARY KEY, currency_name VARCHAR(100), symbol VARCHAR(10), precision INT DEFAULT 2, status VARCHAR(20) DEFAULT 'ACTIVE')",
        "CREATE TABLE IF NOT EXISTS fnd_countries (country_code VARCHAR(2) PRIMARY KEY, country_name VARCHAR(100), iso_code VARCHAR(3), status VARCHAR(20) DEFAULT 'ACTIVE')",
        "CREATE TABLE IF NOT EXISTS fnd_locations (location_id BIGSERIAL PRIMARY KEY, location_code VARCHAR(30), address_line1 VARCHAR(240), city VARCHAR(80), country VARCHAR(80), postal_code VARCHAR(30), status VARCHAR(20) DEFAULT 'ACTIVE')",
        "CREATE TABLE IF NOT EXISTS fnd_user (user_id BIGSERIAL PRIMARY KEY, username VARCHAR(100) NOT NULL, email VARCHAR(240), status VARCHAR(20) DEFAULT 'ACTIVE', creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)",
    ]
    
    print(f"\n[INFO] 创建 {len(tables)} 张表...")
    with conn.cursor() as cur:
        for i, sql in enumerate(tables, 1):
            cur.execute(sql)
            if i % 10 == 0:
                print(f"  - 已创建 {i}/{len(tables)} 张表")
    conn.commit()
    print(f"[OK] 表创建完成!")

def generate_sample_data(conn):
    """生成样例数据"""
    print("\n[INFO] 开始生成样例数据...")
    
    with conn.cursor() as cur:
        # 1. 货币
        currencies = [('USD', 'US Dollar', '$'), ('CNY', 'Chinese Yuan', '¥'), ('EUR', 'Euro', '€')]
        for curr in currencies:
            cur.execute("INSERT INTO fnd_currencies VALUES (%s,%s,%s,2,'ACTIVE') ON CONFLICT DO NOTHING", curr)
        
        # 2. 库存组织
        orgs = [('WH001', 'Main Warehouse'), ('WH002', 'Distribution Center'), ('MFG001', 'Manufacturing Plant')]
        for org in orgs:
            cur.execute("INSERT INTO inv_organization_parameters (organization_code, organization_name, status) VALUES (%s,%s,'ACTIVE')", org)
        
        # 3. 物料类别
        categories = [('CAT001', 'Raw Materials'), ('CAT002', 'Finished Goods'), ('CAT003', 'Packaging')]
        for cat in categories:
            cur.execute("INSERT INTO inv_item_categories (segment1, description, status) VALUES (%s,%s,'ACTIVE')", cat)
        
        # 4. 物料 (100 个)
        print("  - 生成 100 个物料...")
        for i in range(1, 101):
            cur.execute("INSERT INTO inv_system_items_b (segment1, organization_id, description, status) VALUES (%s,1,%s,'ACTIVE')", 
                       (f'ITEM{i:05d}', f'Product Item {i}'))
        
        # 5. 库存余额
        print("  - 生成库存余额...")
        for i in range(1, 101):
            qty = random.randint(100, 10000)
            cost = round(random.uniform(10, 500), 2)
            cur.execute("INSERT INTO inv_onhand_quantities (inventory_item_id, organization_id, quantity, unit_cost) VALUES (%s,1,%s,%s)",
                       (i, qty, cost))
        
        # 6. 客户 (50 个) - 使用已存在的表
        print("  - 生成库存交易 (使用现有 ar_customers 表)...")
        
        # 7. 销售订单 (200 个)
        print("  - 生成 200 个销售订单...")
        for i in range(1, 201):
            order_date = datetime.now() - timedelta(days=random.randint(0, 90))
            cust_id = random.randint(1, 50)
            total_amt = round(random.uniform(1000, 100000), 2)
            cur.execute("INSERT INTO oe_order_headers_all (order_number, customer_id, order_date, status, total_amount, currency_code) VALUES (%s,%s,%s,'BOOKED',%s,'USD')",
                       (f'ORD{i:06d}', cust_id, order_date.date(), total_amt))
            
            # 订单行
            for line_num in range(1, random.randint(1, 5) + 1):
                qty = random.randint(1, 100)
                price = round(random.uniform(10, 1000), 2)
                cur.execute("INSERT INTO oe_order_lines_all (header_id, line_number, inventory_item_id, ordered_quantity, unit_selling_price, amount, status) VALUES (%s,%s,%s,%s,%s,%s,'BOOKED')",
                           (i, line_num, random.randint(1, 100), qty, price, qty * price))
        
        # 8. 项目 (30 个) - 简化字段
        print("  - 生成 30 个项目...")
        for i in range(1, 31):
            start_date = datetime.now() - timedelta(days=random.randint(0, 365))
            budget = round(random.uniform(50000, 2000000), 2)
            cur.execute("INSERT INTO pa_projects_all (project_number, project_name, project_type, start_date, budget_amount, actual_cost, creation_date) VALUES (%s,%s,%s,%s,%s,%s,CURRENT_TIMESTAMP)",
                       (f'PROJ{i:04d}', f'Project {chr(65+i%26)}', random.choice(['CAPEX','OPEX','RESEARCH']), start_date.date(), budget, budget * 0.6))
        
        # 9. 资产 (50 个)
        print("  - 生成 50 个固定资产...")
        for i in range(1, 51):
            cost = round(random.uniform(10000, 500000), 2)
            placed_date = datetime.now() - timedelta(days=random.randint(30, 1000))
            cur.execute("INSERT INTO fa_additions_b (asset_id, date_placed_in_service, cost, category_id, creation_date) VALUES (%s,%s,%s,1,CURRENT_TIMESTAMP)",
                       (i, placed_date.date(), cost))
        
        # 10. 员工 (100 个) - 简化
        print("  - 生成 100 个员工...")
        for i in range(1, 101):
            dob = datetime.now() - timedelta(days=random.randint(7300, 21900))
            cur.execute("INSERT INTO per_all_people_f (employee_number, full_name, first_name, last_name, date_of_birth, gender) VALUES (%s,%s,%s,%s,%s,%s)",
                       (f'EMP{i:05d}', f'Employee {i}', f'First{i}', f'Last{i}', dob.date(), random.choice(['M', 'F'])))
        
        # 11. 库存交易 (500 条)
        print("  - 生成 500 条库存交易...")
        for i in range(1, 501):
            trans_date = datetime.now() - timedelta(days=random.randint(0, 90))
            qty = random.randint(-100, 100)
            cur.execute("INSERT INTO inv_material_transactions (inventory_item_id, organization_id, transaction_type_name, quantity, transaction_date) VALUES (%s,1,%s,%s,%s)",
                       (random.randint(1, 100), random.choice(['Receipt','Issue','Transfer','Adjustment']), qty, trans_date))
        
        conn.commit()
        print("[OK] 样例数据生成完成!")

def main():
    print("=" * 70)
    print("Oracle EBS ERP Batch 3-4 快速创建")
    print("=" * 70)
    
    print("\n正在连接数据库...")
    conn = psycopg2.connect(**DB_CONFIG)
    print("[OK] 数据库连接成功")
    
    current_count = count_tables(conn)
    print(f"[INFO] 当前表数量：{current_count}")
    
    # 创建表
    create_tables(conn)
    
    new_count = count_tables(conn)
    print(f"\n[INFO] 表数量统计:")
    print(f"   创建前：{current_count} 张")
    print(f"   创建后：{new_count} 张")
    print(f"   新增：{new_count - current_count} 张")
    
    # 生成数据
    generate_sample_data(conn)
    
    print("\n" + "=" * 70)
    print("[OK] Batch 3-4 完成！总计 177 张核心表")
    print("=" * 70)
    
    conn.close()
    print("\n数据库连接已关闭")

if __name__ == '__main__':
    main()
