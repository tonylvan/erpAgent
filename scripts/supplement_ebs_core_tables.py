# -*- coding: utf-8 -*-
"""
Supplement Oracle EBS Core Tables for FA, CST, HR, PA Modules
"""

import psycopg2
from psycopg2.extras import execute_batch
import random
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'database': 'erp',
    'user': 'postgres',
    'password': 'postgres'
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def main():
    print("="*70)
    print("Supplement Oracle EBS Core Tables - FA, CST, HR, PA")
    print("="*70)
    
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # Create FA tables
        print("\n[1/4] Creating FA tables...")
        cur.execute("DROP TABLE IF EXISTS fa_transactions CASCADE")
        cur.execute("DROP TABLE IF EXISTS fa_deprn_detail CASCADE")
        cur.execute("DROP TABLE IF EXISTS fa_additions_b CASCADE")
        cur.execute("DROP TABLE IF EXISTS fa_categories_b CASCADE")
        
        cur.execute("""
            CREATE TABLE fa_categories_b (
                category_id BIGINT PRIMARY KEY,
                category_name VARCHAR(100),
                asset_type VARCHAR(20),
                depreciation_method VARCHAR(30),
                life_months INTEGER,
                enabled_flag VARCHAR(1)
            )
        """)
        
        cur.execute("""
            CREATE TABLE fa_additions_b (
                asset_id BIGINT PRIMARY KEY,
                asset_number VARCHAR(30),
                asset_type VARCHAR(20),
                asset_status VARCHAR(20),
                date_placed_in_service DATE,
                cost NUMERIC(15,2),
                category_id BIGINT,
                book_type_code VARCHAR(15),
                created_by BIGINT,
                creation_date TIMESTAMP
            )
        """)
        
        cur.execute("""
            CREATE TABLE fa_deprn_detail (
                deprn_id BIGINT PRIMARY KEY,
                asset_id BIGINT REFERENCES fa_additions_b(asset_id),
                deprn_date DATE,
                deprn_amount NUMERIC(15,2),
                ytd_deprn NUMERIC(15,2),
                net_book_value NUMERIC(15,2)
            )
        """)
        
        cur.execute("""
            CREATE TABLE fa_transactions (
                transaction_id BIGINT PRIMARY KEY,
                asset_id BIGINT REFERENCES fa_additions_b(asset_id),
                transaction_type VARCHAR(30),
                transaction_date DATE,
                amount NUMERIC(15,2),
                status VARCHAR(20)
            )
        """)
        print("  OK Created 4 FA tables")
        
        # Create CST tables
        print("\n[2/4] Creating CST tables...")
        cur.execute("DROP TABLE IF EXISTS cst_item_costs CASCADE")
        cur.execute("DROP TABLE IF EXISTS cst_cost_elements CASCADE")
        cur.execute("DROP TABLE IF EXISTS cst_cost_types CASCADE")
        
        cur.execute("""
            CREATE TABLE cst_cost_types (
                cost_type_id BIGINT PRIMARY KEY,
                cost_type VARCHAR(20),
                description VARCHAR(240),
                cost_method VARCHAR(20),
                frozen_flag VARCHAR(1)
            )
        """)
        
        cur.execute("""
            CREATE TABLE cst_cost_elements (
                cost_element_id BIGINT PRIMARY KEY,
                cost_element VARCHAR(30),
                element_type VARCHAR(20),
                description VARCHAR(240)
            )
        """)
        
        cur.execute("""
            CREATE TABLE cst_item_costs (
                cost_id BIGINT PRIMARY KEY,
                inventory_item_id BIGINT,
                organization_id BIGINT,
                cost_type VARCHAR(20),
                material_cost NUMERIC(15,2),
                material_overhead_cost NUMERIC(15,2),
                resource_cost NUMERIC(15,2),
                overhead_cost NUMERIC(15,2),
                outside_processing_cost NUMERIC(15,2),
                total_cost NUMERIC(15,2),
                update_date TIMESTAMP
            )
        """)
        print("  OK Created 3 CST tables")
        
        # Create HR tables
        print("\n[3/4] Creating HR tables...")
        cur.execute("DROP TABLE IF EXISTS per_pay_proposals_f CASCADE")
        cur.execute("DROP TABLE IF EXISTS per_positions_f CASCADE")
        cur.execute("DROP TABLE IF EXISTS per_jobs_f CASCADE")
        cur.execute("DROP TABLE IF EXISTS per_assignments_f CASCADE")
        
        cur.execute("""
            CREATE TABLE per_jobs_f (
                job_id BIGINT PRIMARY KEY,
                job_name VARCHAR(100),
                job_code VARCHAR(30),
                organization_id BIGINT,
                date_from DATE,
                date_to DATE
            )
        """)
        
        cur.execute("""
            CREATE TABLE per_positions_f (
                position_id BIGINT PRIMARY KEY,
                position_name VARCHAR(100),
                position_code VARCHAR(30),
                organization_id BIGINT,
                job_id BIGINT,
                headcount INTEGER,
                date_from DATE,
                date_to DATE
            )
        """)
        
        cur.execute("""
            CREATE TABLE per_assignments_f (
                assignment_id BIGINT PRIMARY KEY,
                employee_id BIGINT REFERENCES employees(employee_id),
                organization_id BIGINT,
                job_id BIGINT,
                position_id BIGINT,
                assignment_type VARCHAR(20),
                assignment_status VARCHAR(30),
                start_date DATE,
                end_date DATE,
                primary_flag VARCHAR(1)
            )
        """)
        
        cur.execute("""
            CREATE TABLE per_pay_proposals_f (
                proposal_id BIGINT PRIMARY KEY,
                assignment_id BIGINT,
                salary_amount NUMERIC(15,2),
                currency_code VARCHAR(15),
                pay_annualization_factor NUMERIC(5,2),
                change_date DATE,
                approved_flag VARCHAR(1)
            )
        """)
        print("  OK Created 4 HR tables")
        
        # Create PA tables
        print("\n[4/4] Creating PA tables...")
        cur.execute("DROP TABLE IF EXISTS pa_budget_versions CASCADE")
        cur.execute("DROP TABLE IF EXISTS pa_expenditures_all CASCADE")
        cur.execute("DROP TABLE IF EXISTS pa_tasks CASCADE")
        cur.execute("DROP TABLE IF EXISTS pa_projects_all CASCADE")
        
        cur.execute("""
            CREATE TABLE pa_projects_all (
                project_id BIGINT PRIMARY KEY,
                project_number VARCHAR(25),
                project_name VARCHAR(240),
                project_type VARCHAR(30),
                status_code VARCHAR(30),
                start_date DATE,
                completion_date DATE,
                manager_id BIGINT,
                organization_id BIGINT,
                budget_amount NUMERIC(15,2),
                actual_cost NUMERIC(15,2)
            )
        """)
        
        cur.execute("""
            CREATE TABLE pa_tasks (
                task_id BIGINT PRIMARY KEY,
                project_id BIGINT REFERENCES pa_projects_all(project_id),
                task_number VARCHAR(25),
                task_name VARCHAR(240),
                parent_task_id BIGINT,
                start_date DATE,
                completion_date DATE
            )
        """)
        
        cur.execute("""
            CREATE TABLE pa_expenditures_all (
                expenditure_id BIGINT PRIMARY KEY,
                project_id BIGINT REFERENCES pa_projects_all(project_id),
                task_id BIGINT REFERENCES pa_tasks(task_id),
                expenditure_type VARCHAR(30),
                expenditure_item_date DATE,
                quantity NUMERIC(15,2),
                raw_cost NUMERIC(15,2),
                burdened_cost NUMERIC(15,2),
                status_code VARCHAR(30)
            )
        """)
        
        cur.execute("""
            CREATE TABLE pa_budget_versions (
                budget_version_id BIGINT PRIMARY KEY,
                project_id BIGINT REFERENCES pa_projects_all(project_id),
                budget_type_code VARCHAR(30),
                budget_name VARCHAR(240),
                budget_status_code VARCHAR(30),
                budget_amount NUMERIC(15,2),
                version_number INTEGER
            )
        """)
        print("  OK Created 4 PA tables")
        
        conn.commit()
        
        # Generate FA data
        print("\nGenerating FA data...")
        categories = [
            (1, 'Computer Equipment', 'ASSET', 'STRAIGHT_LINE', 36, 'Y'),
            (2, 'Office Furniture', 'ASSET', 'STRAIGHT_LINE', 60, 'Y'),
            (3, 'Vehicles', 'ASSET', 'DECLINING_BALANCE', 48, 'Y'),
            (4, 'Machinery', 'ASSET', 'STRAIGHT_LINE', 120, 'Y'),
            (5, 'Buildings', 'ASSET', 'STRAIGHT_LINE', 480, 'Y'),
        ]
        execute_batch(cur, "INSERT INTO fa_categories_b VALUES (%s,%s,%s,%s,%s,%s)", categories)
        
        assets = []
        for i in range(1, 101):
            assets.append((
                i, f'AST{i:06d}', random.choice(['ASSET', 'CIP']),
                random.choice(['IN_USE', 'RETIRED', 'PENDING']),
                (datetime.now() - timedelta(days=random.randint(30, 1000))).date(),
                round(random.uniform(1000, 500000), 2), random.randint(1, 5),
                'CORP', random.randint(1001, 1107), datetime.now()
            ))
        execute_batch(cur, "INSERT INTO fa_additions_b VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", assets)
        
        deprn = []
        for asset_id in range(1, 101):
            for month in range(1, 13):
                deprn.append((
                    asset_id * 100 + month, asset_id,
                    (datetime.now() - timedelta(days=month * 30)).date(),
                    round(random.uniform(100, 5000), 2),
                    round(random.uniform(100, 5000), 2) * month,
                    round(random.uniform(10000, 100000), 2)
                ))
        execute_batch(cur, "INSERT INTO fa_deprn_detail VALUES (%s,%s,%s,%s,%s,%s)", deprn)
        
        txns = []
        for i in range(1, 201):
            txns.append((
                i, random.randint(1, 100),
                random.choice(['ADDITION', 'ADJUSTMENT', 'RETIREMENT', 'TRANSFER']),
                (datetime.now() - timedelta(days=random.randint(0, 365))).date(),
                round(random.uniform(100, 50000), 2),
                random.choice(['COMPLETE', 'PENDING', 'ERROR'])
            ))
        execute_batch(cur, "INSERT INTO fa_transactions VALUES (%s,%s,%s,%s,%s,%s)", txns)
        print(f"  OK Generated 5 categories, 100 assets, {len(deprn)} deprn, {len(txns)} transactions")
        
        # Generate CST data
        print("\nGenerating CST data...")
        cost_types = [
            (1, 'AVERAGE', 'Average Costing', 'AVERAGE', 'N'),
            (2, 'STANDARD', 'Standard Costing', 'STANDARD', 'Y'),
            (3, 'FIFO', 'FIFO Costing', 'FIFO', 'N'),
        ]
        execute_batch(cur, "INSERT INTO cst_cost_types VALUES (%s,%s,%s,%s,%s)", cost_types)
        
        cost_elements = [
            (1, 'Material', 'MATERIAL', 'Raw material cost'),
            (2, 'Material Overhead', 'MATERIAL_OVERHEAD', 'Material overhead'),
            (3, 'Resource', 'RESOURCE', 'Resource/labor cost'),
            (4, 'Overhead', 'OVERHEAD', 'Manufacturing overhead'),
            (5, 'Outside Processing', 'OUTSIDE_PROCESSING', 'OSP cost'),
        ]
        execute_batch(cur, "INSERT INTO cst_cost_elements VALUES (%s,%s,%s,%s)", cost_elements)
        
        item_costs = []
        for item_id in range(1, 101):
            mat = round(random.uniform(100, 5000), 2)
            item_costs.append((
                item_id, item_id, 1, 'STANDARD', mat,
                round(mat * 0.05, 2), round(random.uniform(50, 1000), 2),
                round(random.uniform(20, 500), 2), round(random.uniform(0, 300), 2),
                round(mat * 1.1, 2), datetime.now()
            ))
        execute_batch(cur, "INSERT INTO cst_item_costs VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", item_costs)
        print(f"  OK Generated 3 cost types, 5 cost elements, 100 item costs")
        
        # Generate HR data
        print("\nGenerating HR data...")
        jobs = [
            (1, 'Software Engineer', 'SE', 1, datetime(2020,1,1).date(), None),
            (2, 'Senior Software Engineer', 'SSE', 1, datetime(2020,1,1).date(), None),
            (3, 'Manager', 'MGR', 1, datetime(2020,1,1).date(), None),
            (4, 'Director', 'DIR', 1, datetime(2020,1,1).date(), None),
            (5, 'Analyst', 'ANL', 2, datetime(2020,1,1).date(), None),
            (6, 'Senior Analyst', 'SAN', 2, datetime(2020,1,1).date(), None),
            (7, 'HR Specialist', 'HRS', 6, datetime(2020,1,1).date(), None),
            (8, 'Finance Manager', 'FM', 2, datetime(2020,1,1).date(), None),
        ]
        execute_batch(cur, "INSERT INTO per_jobs_f VALUES (%s,%s,%s,%s,%s,%s)", jobs)
        
        positions = []
        for i in range(1, 51):
            positions.append((i, f'Position {i}', f'POS{i:03d}', random.randint(1,6), random.randint(1,8), random.randint(1,5), datetime(2020,1,1).date(), None))
        execute_batch(cur, "INSERT INTO per_positions_f VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", positions)
        
        assignments = []
        for emp_id in range(1001, 1434):
            assignments.append((emp_id, emp_id, random.randint(1,6), random.randint(1,8), random.randint(1,50), 'EMPLOYEE_ASSIGNMENT', 'ACTIVE', (datetime.now() - timedelta(days=random.randint(30, 1000))).date(), None, 'Y' if emp_id % 10 == 0 else 'N'))
        execute_batch(cur, "INSERT INTO per_assignments_f VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", assignments)
        
        proposals = []
        for i, emp_id in enumerate(range(1001, 1434)):
            proposals.append((i+1, emp_id, round(random.uniform(30000, 200000), 2), 'CNY', 1.0, (datetime.now() - timedelta(days=random.randint(0, 365))).date(), 'Y' if random.random() > 0.1 else 'N'))
        execute_batch(cur, "INSERT INTO per_pay_proposals_f VALUES (%s,%s,%s,%s,%s,%s,%s)", proposals)
        print(f"  OK Generated 8 jobs, 50 positions, 433 assignments, 433 proposals")
        
        # Generate PA data
        print("\nGenerating PA data...")
        projects = []
        for i in range(1, 51):
            budget = round(random.uniform(100000, 5000000), 2)
            projects.append((i, f'PRJ{i:05d}', f'Project {i}', random.choice(['IT', 'CONSTRUCTION', 'RESEARCH', 'MARKETING']), random.choice(['ACTIVE', 'COMPLETED', 'ON_HOLD', 'CANCELLED']), (datetime.now() - timedelta(days=random.randint(100, 1000))).date(), (datetime.now() + timedelta(days=random.randint(0, 500))).date(), random.randint(1001, 1107), 1, budget, round(budget * random.uniform(0.3, 0.9), 2)))
        execute_batch(cur, "INSERT INTO pa_projects_all VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)", projects)
        
        tasks = []
        task_id = 1
        for proj_id in range(1, 51):
            for j in range(random.randint(3, 10)):
                tasks.append((task_id, proj_id, f'T{proj_id}-{j+1:02d}', f'Task {j+1}', None if j == 0 else task_id - 1, (datetime.now() - timedelta(days=random.randint(50, 500))).date(), (datetime.now() + timedelta(days=random.randint(0, 200))).date()))
                task_id += 1
        execute_batch(cur, "INSERT INTO pa_tasks VALUES (%s,%s,%s,%s,%s,%s,%s)", tasks)
        
        expenditures = []
        for i in range(1, 1001):
            raw_cost = round(random.uniform(100, 50000), 2)
            expenditures.append((i, random.randint(1, 50), random.randint(1, task_id - 1), random.choice(['LABOR', 'MATERIAL', 'EXPENSE', 'USAGE']), (datetime.now() - timedelta(days=random.randint(0, 365))).date(), round(random.uniform(1, 100), 2), raw_cost, round(raw_cost * 1.2, 2), random.choice(['APPROVED', 'PENDING', 'REJECTED'])))
        execute_batch(cur, "INSERT INTO pa_expenditures_all VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)", expenditures)
        
        budget_versions = []
        for proj_id in range(1, 51):
            budget_versions.append((proj_id, proj_id, 'ORIGINAL', f'Original Budget for Project {proj_id}', 'APPROVED', round(random.uniform(100000, 5000000), 2), 1))
        execute_batch(cur, "INSERT INTO pa_budget_versions VALUES (%s,%s,%s,%s,%s,%s,%s)", budget_versions)
        print(f"  OK Generated 50 projects, {len(tasks)} tasks, 1000 expenditures, 50 budget versions")
        
        conn.commit()
        
        # Show summary
        print("\n" + "="*70)
        print("Data Summary - New Modules")
        print("="*70)
        
        modules = {
            'FA': ['fa_additions_b', 'fa_categories_b', 'fa_deprn_detail', 'fa_transactions'],
            'CST': ['cst_item_costs', 'cst_cost_types', 'cst_cost_elements'],
            'HR': ['per_assignments_f', 'per_jobs_f', 'per_positions_f', 'per_pay_proposals_f'],
            'PA': ['pa_projects_all', 'pa_tasks', 'pa_expenditures_all', 'pa_budget_versions'],
        }
        
        for module, tables in modules.items():
            print(f"\n{module} Module:")
            print("-" * 50)
            for table in tables:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                print(f"  {table:35s}: {count:5d}")
        
        print("\n" + "="*70)
        print("OK All tables and data created successfully!")
        print("="*70)
        
    except Exception as e:
        print(f"\nERROR Error: {e}")
        conn.rollback()
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == '__main__':
    main()
