#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Oracle EBS ERP Batch 3-4 表创建 + 样例数据生成
"""

import psycopg2
import random
from datetime import datetime, timedelta

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'erp',
    'user': 'postgres',
    'password': 'postgres'
}

def read_sql_file(file_path):
    """读取 SQL 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def execute_sql_script(conn, sql_script):
    """执行 SQL 脚本"""
    try:
        with conn.cursor() as cur:
            cur.execute(sql_script)
        conn.commit()
        return True, "成功"
    except Exception as e:
        conn.rollback()
        return False, str(e)

def count_tables(conn):
    """统计当前表数量"""
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
              AND table_type = 'BASE TABLE'
        """)
        return cur.fetchone()[0]

def generate_sample_data(conn):
    """生成样例数据"""
    print("\n[INFO] 开始生成样例数据...")
    
    try:
        with conn.cursor() as cur:
            # 1. 生成货币数据
            currencies = [
                ('USD', 'US Dollar', '$'),
                ('CNY', 'Chinese Yuan', '¥'),
                ('EUR', 'Euro', '€'),
                ('GBP', 'British Pound', '£'),
                ('JPY', 'Japanese Yen', '¥')
            ]
            for curr in currencies:
                cur.execute("""
                    INSERT INTO fnd_currencies (currency_code, currency_name, symbol, status)
                    VALUES (%s, %s, %s, 'ACTIVE')
                    ON CONFLICT (currency_code) DO NOTHING
                """, curr)
            
            # 2. 生成库存组织
            orgs = [
                ('WH001', 'Main Warehouse', 'MAIN'),
                ('WH002', 'Distribution Center', 'DC'),
                ('MFG001', 'Manufacturing Plant', 'MFG')
            ]
            for org in orgs:
                cur.execute("""
                    INSERT INTO inv_organization_parameters 
                    (organization_code, organization_name, status)
                    VALUES (%s, %s, 'ACTIVE')
                """, org)
            
            # 3. 生成物料类别
            categories = [
                ('CAT001', 'Raw Materials', 'RAW'),
                ('CAT002', 'Finished Goods', 'FG'),
                ('CAT003', 'Packaging', 'PKG'),
                ('CAT004', 'Office Supplies', 'OFFICE')
            ]
            for cat in categories:
                cur.execute("""
                    INSERT INTO inv_item_categories 
                    (segment1, description, status)
                    VALUES (%s, %s, 'ACTIVE')
                """, (cat[0], cat[1]))
            
            # 4. 生成物料主数据 (100 个)
            print("  - 生成 100 个物料...")
            for i in range(1, 101):
                cur.execute("""
                    INSERT INTO inv_system_items_b 
                    (segment1, organization_id, description, item_type, status, 
                     primary_uom_code, base_unit_of_measure)
                    VALUES (%s, %s, %s, %s, 'ACTIVE', 'Ea', 'Each')
                """, (f'ITEM{i:05d}', 1, f'Product Item {i}', 'PURCHASED'))
            
            # 5. 生成库存余额
            print("  - 生成库存余额...")
            for i in range(1, 101):
                qty = random.randint(100, 10000)
                unit_cost = round(random.uniform(10, 500), 2)
                cur.execute("""
                    INSERT INTO inv_onhand_quantities 
                    (inventory_item_id, organization_id, subinventory_code, 
                     quantity, unit_cost, total_value)
                    VALUES (%s, 1, 'MAIN', %s, %s, %s)
                """, (i, qty, unit_cost, qty * unit_cost))
            
            # 6. 生成客户数据
            print("  - 生成 50 个客户...")
            for i in range(1, 51):
                cur.execute("""
                    INSERT INTO ar_customers 
                    (customer_number, customer_name, customer_type, status, 
                     credit_limit, currency_code)
                    VALUES (%s, %s, %s, 'ACTIVE', %s, 'USD')
                """, (f'CUST{i:05d}', f'Customer {chr(65+i%26)}{i}', 
                      random.choice(['ENTERPRISE', 'SMB', 'RETAIL']),
                      random.randint(10000, 500000)))
            
            # 7. 生成销售订单 (200 个)
            print("  - 生成 200 个销售订单...")
            for i in range(1, 201):
                order_date = datetime.now() - timedelta(days=random.randint(0, 90))
                customer_id = random.randint(1, 50)
                total_amt = round(random.uniform(1000, 100000), 2)
                
                cur.execute("""
                    INSERT INTO oe_order_headers_all 
                    (order_number, customer_id, order_date, status, 
                     total_amount, currency_code, booked_flag, flow_status_code)
                    VALUES (%s, %s, %s, %s, %s, 'USD', 'Y', 'BOOKED')
                """, (f'ORD{i:06d}', customer_id, order_date.date(), 
                      random.choice(['ENTERED', 'BOOKED', 'PICKED', 'SHIPPED']),
                      total_amt))
                
                # 每个订单 1-5 行
                line_count = random.randint(1, 5)
                for line_num in range(1, line_count + 1):
                    qty = random.randint(1, 100)
                    price = round(random.uniform(10, 1000), 2)
                    cur.execute("""
                        INSERT INTO oe_order_lines_all 
                        (header_id, line_number, inventory_item_id, 
                         ordered_quantity, unit_selling_price, amount, status)
                        VALUES (%s, %s, %s, %s, %s, %s, 'BOOKED')
                    """, (i, line_num, random.randint(1, 100), qty, price, qty * price))
            
            # 8. 生成项目数据 (30 个)
            print("  - 生成 30 个项目...")
            for i in range(1, 31):
                start_date = datetime.now() - timedelta(days=random.randint(0, 365))
                budget = round(random.uniform(50000, 2000000), 2)
                
                cur.execute("""
                    INSERT INTO pa_projects_all 
                    (project_number, project_name, project_type, status, 
                     start_date, budget_amount, actual_cost)
                    VALUES (%s, %s, %s, 'ACTIVE', %s, %s, %s)
                """, (f'PROJ{i:04d}', f'Project {chr(65+i%26)}', 
                      random.choice(['CAPEX', 'OPEX', 'RESEARCH']),
                      start_date.date(), budget, budget * 0.6))
            
            # 9. 生成资产数据 (50 个)
            print("  - 生成 50 个固定资产...")
            for i in range(1, 51):
                cost = round(random.uniform(10000, 500000), 2)
                placed_date = datetime.now() - timedelta(days=random.randint(30, 1000))
                
                cur.execute("""
                    INSERT INTO fa_additions_b 
                    (asset_id, date_placed_in_service, cost, category_id, book_id)
                    VALUES (%s, %s, %s, %s, 1)
                """, (i, placed_date.date(), cost, random.randint(1, 4)))
            
            # 10. 生成员工数据 (100 个)
            print("  - 生成 100 个员工...")
            for i in range(1, 101):
                cur.execute("""
                    INSERT INTO per_all_people_f 
                    (employee_number, full_name, first_name, last_name, 
                     date_of_birth, gender, status)
                    VALUES (%s, %s, %s, %s, %s, %s, 'ACTIVE')
                """, (f'EMP{i:05d}', f'Employee {i}', f'First{i}', f'Last{i}',
                      (datetime.now() - timedelta(days=random.randint(7300, 21900))).date(),
                      random.choice(['M', 'F'])))
            
            # 11. 生成库存交易 (500 条)
            print("  - 生成 500 条库存交易...")
            for i in range(1, 501):
                trans_date = datetime.now() - timedelta(days=random.randint(0, 90))
                qty = random.randint(-100, 100)
                
                cur.execute("""
                    INSERT INTO inv_material_transactions 
                    (inventory_item_id, organization_id, transaction_type_name, 
                     quantity, transaction_cost, transaction_date)
                    VALUES (%s, 1, %s, %s, %s, %s)
                """, (random.randint(1, 100), 
                      random.choice(['Receipt', 'Issue', 'Transfer', 'Adjustment']),
                      qty, abs(qty) * random.uniform(10, 100), trans_date))
            
            conn.commit()
            print("[OK] 样例数据生成完成!")
            return True
            
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] 样例数据生成失败：{e}")
        return False

def main():
    print("=" * 70)
    print("Oracle EBS ERP Batch 3-4 表创建 + 样例数据生成")
    print("=" * 70)
    
    # 连接数据库
    print("\n正在连接数据库...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print(f"[OK] 数据库连接成功")
    except Exception as e:
        print(f"[ERROR] 数据库连接失败：{e}")
        return
    
    # 统计当前表数
    current_count = count_tables(conn)
    print(f"[INFO] 当前表数量：{current_count}")
    
    # 读取 SQL 文件
    sql_file = r'D:\erpAgent\backend\scripts\create_extended_tables_batch3_4.sql'
    print(f"\n正在读取 SQL 文件：{sql_file}")
    
    try:
        sql_script = read_sql_file(sql_file)
        print(f"[OK] SQL 文件读取成功 ({len(sql_script):,} 字节)")
    except Exception as e:
        print(f"[ERROR] 读取 SQL 文件失败：{e}")
        conn.close()
        return
    
    # 执行 SQL 脚本
    print("\n正在执行 SQL 脚本...")
    success, message = execute_sql_script(conn, sql_script)
    
    if success:
        print(f"\n[OK] SQL 脚本执行成功!")
        new_count = count_tables(conn)
        print(f"\n[INFO] 表数量统计:")
        print(f"   创建前：{current_count} 张")
        print(f"   创建后：{new_count} 张")
        print(f"   新增：{new_count - current_count} 张")
        
        # 生成样例数据
        generate_sample_data(conn)
        
        print("\n" + "=" * 70)
        print("[OK] Batch 3-4 扩展表创建完成!")
        print("=" * 70)
    else:
        print(f"\n[ERROR] SQL 脚本执行失败:")
        print(f"   错误信息：{message}")
    
    conn.close()
    print(f"\n数据库连接已关闭")

if __name__ == '__main__':
    main()
