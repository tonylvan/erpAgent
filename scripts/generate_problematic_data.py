# -*- coding: utf-8 -*-
"""
Generate Problematic and Noisy Data for Testing
用于测试数据质量规则和异常检测
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

def generate_problematic_invoice_data(cur):
    """生成有问题的发票数据（用于测试验证规则）"""
    print("\n[1/6] Generating problematic invoice data...")
    
    # 1. 缺少必填字段的发票
    cur.execute("""
        INSERT INTO ap_invoices_all (invoice_id, invoice_num, invoice_type_lookup_code, 
                                     vendor_id, invoice_amount, payment_status, invoice_date)
        VALUES 
            (2001, 'INV-NO-AMOUNT', 'STANDARD', 1, NULL, 'UNPAID', NOW()),
            (2002, 'INV-NO-DATE', 'STANDARD', 2, 5000, 'UNPAID', NULL)
        ON CONFLICT (invoice_id) DO NOTHING
    """)
    print("  OK Generated 2 invoices with missing required fields")
    
    # 2. 金额超出范围的发票
    cur.execute("""
        INSERT INTO ap_invoices_all (invoice_id, invoice_num, invoice_type_lookup_code,
                                     vendor_id, invoice_amount, payment_status, invoice_date)
        VALUES
            (2003, 'INV-NEGATIVE', 'STANDARD', 3, -5000, 'UNPAID', NOW()),
            (2004, 'INV-TOO-LARGE', 'STANDARD', 4, 15000000, 'UNPAID', NOW())
        ON CONFLICT (invoice_id) DO NOTHING
    """)
    print("  OK Generated 2 invoices with out-of-range amounts")
    
    # 3. 头表与行表金额不一致的发票
    cur.execute("""
        INSERT INTO ap_invoices_all (invoice_id, invoice_num, invoice_amount, vendor_id, 
                                     payment_status, invoice_date, created_by)
        VALUES (2005, 'INV-MISMATCH-1', 10000, 5, 'UNPAID', NOW(), 1001)
        ON CONFLICT (invoice_id) DO NOTHING
    """)
    cur.execute("""
        INSERT INTO ap_invoice_lines_all (invoice_line_id, invoice_id, line_number, amount, description)
        VALUES 
            (339, 2005, 1, 3000, 'Line 1'),
            (340, 2005, 2, 4000, 'Line 2')
        ON CONFLICT (invoice_line_id) DO NOTHING
    """)
    # 头表 10000 != 行表 7000
    print("  OK Generated 1 invoice with header/line amount mismatch")
    
    # 4. 日期逻辑错误的发票（发票日期早于 PO 日期）
    cur.execute("""
        INSERT INTO ap_invoices_all (invoice_id, invoice_num, invoice_amount, vendor_id,
                                     payment_status, invoice_date, created_by)
        VALUES (2006, 'INV-DATE-ERROR', 8000, 6, 'UNPAID', '2020-01-01', 1002)
        ON CONFLICT (invoice_id) DO NOTHING
    """)
    print("  OK Generated 1 invoice with date before PO date")
    
    # 5. 重复的发票号
    cur.execute("""
        INSERT INTO ap_invoices_all (invoice_id, invoice_num, invoice_amount, vendor_id,
                                     payment_status, invoice_date)
        VALUES 
            (2007, 'PO-0000001', 5000, 7, 'UNPAID', NOW()),
            (2008, 'PO-0000001', 6000, 8, 'UNPAID', NOW())
        ON CONFLICT (invoice_id) DO NOTHING
    """)
    print("  OK Generated 2 invoices with duplicate invoice numbers")

def generate_problematic_po_data(cur):
    """生成有问题的采购订单数据"""
    print("\n[2/6] Generating problematic PO data...")
    
    # 1. 头表与行表金额不一致的 PO
    cur.execute("""
        INSERT INTO po_headers_all (po_header_id, segment1, type_lookup_code, vendor_id, 
                                    amount, status_lookup_code, approved_flag, creation_date)
        VALUES (101, 'PO-MISMATCH', 'STANDARD', 1, 50000, 'APPROVED', 'Y', NOW())
        ON CONFLICT (po_header_id) DO NOTHING
    """)
    cur.execute("""
        INSERT INTO po_lines_all (po_line_id, po_header_id, line_num, amount, item_description)
        VALUES 
            (314, 101, 1, 10000, 'Line 1'),
            (315, 101, 2, 15000, 'Line 2')
        ON CONFLICT (po_line_id) DO NOTHING
    """)
    # 头表 50000 != 行表 25000
    print("  OK Generated 1 PO with header/line amount mismatch")
    
    # 2. 状态为 APPROVED 但没有审批人的 PO
    cur.execute("""
        INSERT INTO po_headers_all (po_header_id, segment1, type_lookup_code, vendor_id,
                                    amount, status_lookup_code, approved_flag, creation_date)
        VALUES (102, 'PO-NO-APPROVER', 'STANDARD', 2, 20000, 'APPROVED', 'Y', NOW())
        ON CONFLICT (po_header_id) DO NOTHING
    """)
    print("  OK Generated 1 approved PO without approver")
    
    # 3. 金额异常的 PO
    cur.execute("""
        INSERT INTO po_headers_all (po_header_id, segment1, type_lookup_code, vendor_id,
                                    amount, status_lookup_code, creation_date)
        VALUES
            (103, 'PO-ZERO-AMOUNT', 'STANDARD', 3, 0, 'PENDING', NOW()),
            (104, 'PO-NEGATIVE', 'STANDARD', 4, -1000, 'PENDING', NOW())
        ON CONFLICT (po_header_id) DO NOTHING
    """)
    print("  OK Generated 2 POs with zero/negative amounts")

def generate_noisy_employee_data(cur):
    """生成噪音员工数据"""
    print("\n[3/6] Generating noisy employee data...")
    
    # 1. 重复的员工记录
    cur.execute("""
        INSERT INTO employees (employee_id, employee_name, department)
        VALUES
            (1501, 'John Smith', 'IT'),
            (1502, 'John Smith', 'IT'),
            (1503, 'John  Smith', 'IT')  -- 多一个空格
        ON CONFLICT (employee_id) DO NOTHING
    """)
    print("  OK Generated 3 duplicate employee records")
    
    # 2. 员工姓名为空或异常
    cur.execute("""
        INSERT INTO employees (employee_id, employee_name, department)
        VALUES
            (1504, '', 'IT'),
            (1505, 'NULL', 'Finance'),
            (1506, 'Test Test', 'HR'),
            (1507, '999999', 'Sales')
        ON CONFLICT (employee_id) DO NOTHING
    """)
    print("  OK Generated 4 employees with invalid names")
    
    # 3. 部门不存在的员工
    cur.execute("""
        INSERT INTO employees (employee_id, employee_name, department)
        VALUES
            (1508, 'Valid Name', 'NonExistent_Dept_1'),
            (1509, 'Valid Name 2', 'NonExistent_Dept_2')
        ON CONFLICT (employee_id) DO NOTHING
    """)
    print("  OK Generated 2 employees with non-existent departments")

def generate_noisy_supplier_data(cur):
    """生成噪音供应商数据"""
    print("\n[4/6] Generating noisy supplier data...")
    
    # 1. 供应商名称相似（可能是重复）
    cur.execute("""
        INSERT INTO ap_suppliers (vendor_id, segment1, vendor_name, vendor_type_lookup_code, status)
        VALUES
            (52, 'SUP-DUP-1', 'ABC Corporation', 'VENDOR', 'ACTIVE'),
            (53, 'SUP-DUP-2', 'ABC Corp', 'VENDOR', 'ACTIVE'),
            (54, 'SUP-DUP-3', 'A.B.C. Corporation', 'VENDOR', 'ACTIVE'),
            (55, 'SUP-DUP-4', 'abc corporation', 'VENDOR', 'ACTIVE')
        ON CONFLICT (vendor_id) DO NOTHING
    """)
    print("  OK Generated 4 potentially duplicate suppliers")
    
    # 2. 供应商编码重复（使用不同的编码）
    cur.execute("""
        INSERT INTO ap_suppliers (vendor_id, segment1, vendor_name, vendor_type_lookup_code, status)
        VALUES
            (56, 'SUP-DUP-5', 'Different Supplier 1', 'VENDOR', 'ACTIVE'),
            (57, 'SUP-DUP-6', 'Different Supplier 2', 'VENDOR', 'ACTIVE')
        ON CONFLICT (vendor_id) DO NOTHING
    """)
    print("  OK Generated 2 suppliers with similar names")
    
    # 3. 状态异常的供应商
    cur.execute("""
        INSERT INTO ap_suppliers (vendor_id, segment1, vendor_name, vendor_type_lookup_code, status)
        VALUES
            (58, 'SUP-INACTIVE', 'Inactive Supplier', 'VENDOR', 'INACTIVE'),
            (59, 'SUP-INVALID', 'Invalid Status Supplier', 'VENDOR', 'INVALID_STATUS')
        ON CONFLICT (vendor_id) DO NOTHING
    """)
    print("  OK Generated 2 suppliers with abnormal status")

def generate_noisy_project_data(cur):
    """生成噪音项目数据"""
    print("\n[5/6] Generating noisy project data...")
    
    # 1. 预算 < 实际成本的项目
    cur.execute("""
        INSERT INTO pa_projects_all (project_id, project_number, project_name, project_type,
                                     status_code, budget_amount, actual_cost, manager_id, organization_id)
        VALUES
            (51, 'PRJ-OVER-BUDGET', 'Over Budget Project', 'IT', 'ACTIVE', 100000, 150000, 1001, 1),
            (52, 'PRJ-NEG-BUDGET', 'Negative Budget Project', 'IT', 'ACTIVE', -50000, 30000, 1002, 1)
        ON CONFLICT (project_id) DO NOTHING
    """)
    print("  OK Generated 2 projects with budget issues")
    
    # 2. 完成日期早于开始日期的项目
    cur.execute("""
        INSERT INTO pa_projects_all (project_id, project_number, project_name, project_type,
                                     status_code, start_date, completion_date, budget_amount, 
                                     actual_cost, manager_id, organization_id)
        VALUES
            (53, 'PRJ-DATE-ERROR', 'Date Error Project', 'IT', 'COMPLETED', 
             '2025-12-01', '2025-01-01', 200000, 180000, 1003, 1)
        ON CONFLICT (project_id) DO NOTHING
    """)
    print("  OK Generated 1 project with completion date before start date")
    
    # 3. 项目名为空或异常
    cur.execute("""
        INSERT INTO pa_projects_all (project_id, project_number, project_name, project_type,
                                     status_code, budget_amount, actual_cost, manager_id, organization_id)
        VALUES
            (54, 'PRJ-NO-NAME', '', 'IT', 'ACTIVE', 100000, 50000, 1004, 1),
            (55, 'PRJ-TEST', 'TEST', 'IT', 'ACTIVE', 100000, 50000, 1005, 1),
            (56, 'PRJ-XXX', 'XXX', 'IT', 'ACTIVE', 100000, 50000, 1006, 1)
        ON CONFLICT (project_id) DO NOTHING
    """)
    print("  OK Generated 3 projects with invalid names")

def generate_noisy_asset_data(cur):
    """生成噪音固定资产数据"""
    print("\n[6/6] Generating noisy asset data...")
    
    # 1. 折旧金额 > 资产原值
    cur.execute("""
        INSERT INTO fa_additions_b (asset_id, asset_number, asset_type, asset_status, 
                                    cost, category_id, book_type_code, created_by)
        VALUES (101, 'AST-OVER-DEPRN', 'ASSET', 'IN_USE', 10000, 1, 'CORP', 1001)
        ON CONFLICT (asset_id) DO NOTHING
    """)
    cur.execute("""
        INSERT INTO fa_deprn_detail (deprn_id, asset_id, deprn_date, deprn_amount, ytd_deprn, net_book_value)
        VALUES
            (10101, 101, NOW(), 5000, 60000, -50000),  -- 累计折旧 > 原值
            (10102, 101, NOW(), 5000, 60000, -50000)
        ON CONFLICT (deprn_id) DO NOTHING
    """)
    print("  OK Generated 1 asset with depreciation > cost")
    
    # 2. 资产净值为负
    cur.execute("""
        INSERT INTO fa_additions_b (asset_id, asset_number, asset_type, asset_status,
                                    cost, category_id, book_type_code, created_by)
        VALUES (102, 'AST-NEG-NET', 'ASSET', 'IN_USE', 5000, 1, 'CORP', 1002)
        ON CONFLICT (asset_id) DO NOTHING
    """)
    cur.execute("""
        INSERT INTO fa_deprn_detail (deprn_id, asset_id, deprn_date, deprn_amount, ytd_deprn, net_book_value)
        VALUES
            (10201, 102, NOW(), 3000, 8000, -3000)  -- 净值为负
        ON CONFLICT (deprn_id) DO NOTHING
    """)
    print("  OK Generated 1 asset with negative net book value")
    
    # 3. 资产状态异常
    cur.execute("""
        INSERT INTO fa_additions_b (asset_id, asset_number, asset_type, asset_status,
                                    cost, category_id, book_type_code, created_by)
        VALUES
            (103, 'AST-INVALID-STATUS', 'ASSET', 'INVALID_STATUS', 10000, 1, 'CORP', 1003),
            (104, 'AST-NO-STATUS', 'ASSET', '', 10000, 1, 'CORP', 1004)
        ON CONFLICT (asset_id) DO NOTHING
    """)
    print("  OK Generated 2 assets with invalid status")

def show_summary():
    """显示问题数据统计"""
    print("\n" + "="*70)
    print("Problematic & Noisy Data Summary")
    print("="*70)
    
    conn = get_connection()
    cur = conn.cursor()
    
    problem_tables = {
        'ap_invoices_all (问题发票)': """
            SELECT COUNT(*) FROM ap_invoices_all 
            WHERE invoice_id >= 2001
        """,
        'po_headers_all (问题 PO)': """
            SELECT COUNT(*) FROM po_headers_all 
            WHERE po_header_id >= 101
        """,
        'employees (噪音员工)': """
            SELECT COUNT(*) FROM employees 
            WHERE employee_id >= 1501
        """,
        'ap_suppliers (噪音供应商)': """
            SELECT COUNT(*) FROM ap_suppliers 
            WHERE vendor_id >= 52
        """,
        'pa_projects_all (噪音项目)': """
            SELECT COUNT(*) FROM pa_projects_all 
            WHERE project_id >= 51
        """,
        'fa_additions_b (噪音资产)': """
            SELECT COUNT(*) FROM fa_additions_b 
            WHERE asset_id >= 101
        """,
    }
    
    print("\nProblem Data Counts:")
    print("-" * 50)
    for desc, sql in problem_tables.items():
        try:
            cur.execute(sql)
            count = cur.fetchone()[0]
            print(f"  {desc:35s}: {count:5d}")
        except Exception as e:
            print(f"  {desc:35s}: ERROR - {e}")
    
    cur.close()
    conn.close()

def main():
    print("="*70)
    print("Generate Problematic and Noisy Data")
    print("="*70)
    
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # Generate all problematic data
        generate_problematic_invoice_data(cur)
        generate_problematic_po_data(cur)
        generate_noisy_employee_data(cur)
        generate_noisy_supplier_data(cur)
        generate_noisy_project_data(cur)
        generate_noisy_asset_data(cur)
        
        conn.commit()
        
        # Show summary
        show_summary()
        
        print("\n" + "="*70)
        print("OK Problematic and noisy data generated successfully!")
        print("="*70)
        print("\nUse this data to test:")
        print("  - Data quality validation rules")
        print("  - Anomaly detection algorithms")
        print("  - Data cleansing processes")
        print("  - Duplicate detection")
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
