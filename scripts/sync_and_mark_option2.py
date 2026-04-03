# -*- coding: utf-8 -*-
"""
Sync and Mark Problematic Data (Option 2)
先同步所有数据，然后标记问题数据
"""

import psycopg2
from decimal import Decimal
from neo4j import GraphDatabase

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

def get_pg_connection():
    return psycopg2.connect(**PG_CONFIG)

def get_neo4j_driver():
    return GraphDatabase.driver(**NEO4J_CONFIG)

def convert_value(val):
    if val is None:
        return None
    if isinstance(val, Decimal):
        return float(val)
    return val

def sync_and_mark_invoices(driver, pg_cur):
    """Sync and mark invoices"""
    print("\n" + "="*70)
    print("Syncing and marking invoices...")
    print("="*70)
    
    with driver.session() as session:
        # All invoices
        pg_cur.execute("""
            SELECT invoice_id, invoice_num, invoice_amount, vendor_id, payment_status
            FROM ap_invoices_all
        """)
        invoices = pg_cur.fetchall()
        
        synced = 0
        marked = 0
        for inv in invoices:
            is_problem = inv[0] >= 2001
            session.run("""
                MERGE (inv:Invoice {id: $id})
                SET inv.invoiceNum = $num,
                    inv.amount = $amount,
                    inv.vendorId = $vendor,
                    inv.paymentStatus = $status,
                    inv.isProblematic = $is_problem,
                    inv.problemType = CASE WHEN $is_problem THEN 'data_quality_issue' ELSE null END
            """, id=inv[0], num=inv[1], amount=convert_value(inv[2]), 
                vendor=inv[3], status=inv[4], is_problem=is_problem)
            synced += 1
            if is_problem:
                marked += 1
        
        print(f"  OK Synced {synced} invoices ({marked} marked as problematic)")
        return marked

def sync_and_mark_pos(driver, pg_cur):
    """Sync and mark POs"""
    print("\n" + "="*70)
    print("Syncing and marking POs...")
    print("="*70)
    
    with driver.session() as session:
        pg_cur.execute("""
            SELECT po_header_id, segment1, amount, vendor_id, status_lookup_code
            FROM po_headers_all
        """)
        pos = pg_cur.fetchall()
        
        synced = 0
        marked = 0
        for po in pos:
            is_problem = po[0] >= 101
            session.run("""
                MERGE (po:PurchaseOrder {id: $id})
                SET po.poNumber = $num,
                    po.amount = $amount,
                    po.vendorId = $vendor,
                    po.status = $status,
                    po.isProblematic = $is_problem,
                    po.problemType = CASE WHEN $is_problem THEN 'data_quality_issue' ELSE null END
            """, id=po[0], num=po[1], amount=convert_value(po[2]), 
                vendor=po[3], status=po[4], is_problem=is_problem)
            synced += 1
            if is_problem:
                marked += 1
        
        print(f"  OK Synced {synced} POs ({marked} marked as problematic)")
        return marked

def sync_and_mark_employees(driver, pg_cur):
    """Sync and mark employees"""
    print("\n" + "="*70)
    print("Syncing and marking employees...")
    print("="*70)
    
    with driver.session() as session:
        pg_cur.execute("""
            SELECT employee_id, employee_name, department
            FROM employees
        """)
        emps = pg_cur.fetchall()
        
        synced = 0
        marked = 0
        for emp in emps:
            is_problem = emp[0] >= 1501
            session.run("""
                MERGE (emp:Employee {id: $id})
                SET emp.name = $name,
                    emp.department = $dept,
                    emp.isProblematic = $is_problem,
                    emp.problemType = CASE WHEN $is_problem THEN 'noisy_data' ELSE null END
            """, id=emp[0], name=emp[1], dept=emp[2], is_problem=is_problem)
            synced += 1
            if is_problem:
                marked += 1
        
        print(f"  OK Synced {synced} employees ({marked} marked as noisy)")
        return marked

def sync_and_mark_suppliers(driver, pg_cur):
    """Sync and mark suppliers"""
    print("\n" + "="*70)
    print("Syncing and marking suppliers...")
    print("="*70)
    
    with driver.session() as session:
        pg_cur.execute("""
            SELECT vendor_id, segment1, vendor_name, status
            FROM ap_suppliers
        """)
        sups = pg_cur.fetchall()
        
        synced = 0
        marked = 0
        for sup in sups:
            is_problem = sup[0] >= 52
            session.run("""
                MERGE (sup:Supplier {id: $id})
                SET sup.code = $code,
                    sup.name = $name,
                    sup.status = $status,
                    sup.isProblematic = $is_problem,
                    sup.problemType = CASE WHEN $is_problem THEN 'noisy_data' ELSE null END
            """, id=sup[0], code=sup[1], name=sup[2], status=sup[3], is_problem=is_problem)
            synced += 1
            if is_problem:
                marked += 1
        
        print(f"  OK Synced {synced} suppliers ({marked} marked as noisy)")
        return marked

def sync_and_mark_projects(driver, pg_cur):
    """Sync and mark projects"""
    print("\n" + "="*70)
    print("Syncing and marking projects...")
    print("="*70)
    
    with driver.session() as session:
        pg_cur.execute("""
            SELECT project_id, project_number, project_name, budget_amount, actual_cost
            FROM pa_projects_all
        """)
        projs = pg_cur.fetchall()
        
        synced = 0
        marked = 0
        for proj in projs:
            is_problem = proj[0] >= 51
            session.run("""
                MERGE (proj:Project {id: $id})
                SET proj.projectNumber = $num,
                    proj.name = $name,
                    proj.budget = $budget,
                    proj.actual = $actual,
                    proj.isProblematic = $is_problem,
                    proj.problemType = CASE WHEN $is_problem THEN 'noisy_data' ELSE null END
            """, id=proj[0], num=proj[1], name=proj[2], 
                budget=convert_value(proj[3]), actual=convert_value(proj[4]), 
                is_problem=is_problem)
            synced += 1
            if is_problem:
                marked += 1
        
        print(f"  OK Synced {synced} projects ({marked} marked as noisy)")
        return marked

def sync_and_mark_assets(driver, pg_cur):
    """Sync and mark assets"""
    print("\n" + "="*70)
    print("Syncing and marking assets...")
    print("="*70)
    
    with driver.session() as session:
        pg_cur.execute("""
            SELECT asset_id, asset_number, cost, asset_status
            FROM fa_additions_b
        """)
        assets = pg_cur.fetchall()
        
        synced = 0
        marked = 0
        for asset in assets:
            is_problem = asset[0] >= 101
            session.run("""
                MERGE (asset:FixedAsset {id: $id})
                SET asset.assetNumber = $num,
                    asset.cost = $cost,
                    asset.status = $status,
                    asset.isProblematic = $is_problem,
                    asset.problemType = CASE WHEN $is_problem THEN 'noisy_data' ELSE null END
            """, id=asset[0], num=asset[1], cost=convert_value(asset[2]), 
                status=asset[3], is_problem=is_problem)
            synced += 1
            if is_problem:
                marked += 1
        
        print(f"  OK Synced {synced} assets ({marked} marked as noisy)")
        return marked

def verify(driver):
    """Verify results"""
    print("\n" + "="*70)
    print("Verifying Results...")
    print("="*70)
    
    with driver.session() as session:
        # Count marked
        result = session.run("""
            MATCH (n)
            WHERE n.isProblematic = true
            RETURN labels(n)[0] as label, count(n) as count
            ORDER BY label
        """)
        
        print("\nMarked Problem Nodes:")
        print("-" * 50)
        total_problem = 0
        for rec in result:
            label = rec['label'] or 'Unknown'
            print(f"  {label:30s}: {rec['count']}")
            total_problem += rec['count']
        
        # Count normal
        result = session.run("""
            MATCH (n)
            WHERE n.isProblematic IS NULL OR n.isProblematic = false
            RETURN labels(n)[0] as label, count(n) as count
            ORDER BY label
        """)
        
        print("\nNormal Nodes:")
        print("-" * 50)
        total_normal = 0
        for rec in result:
            label = rec['label'] or 'Unknown'
            print(f"  {label:30s}: {rec['count']}")
            total_normal += rec['count']
        
        print(f"\n  Total Problem: {total_problem}")
        print(f"  Total Normal: {total_normal}")
        print("="*70)

def main():
    print("="*70)
    print("Option 2: Sync and Mark Problematic Data")
    print("="*70)
    
    pg_conn = get_pg_connection()
    pg_cur = pg_conn.cursor()
    driver = get_neo4j_driver()
    
    try:
        # Sync and mark all
        inv_count = sync_and_mark_invoices(driver, pg_cur)
        po_count = sync_and_mark_pos(driver, pg_cur)
        emp_count = sync_and_mark_employees(driver, pg_cur)
        sup_count = sync_and_mark_suppliers(driver, pg_cur)
        proj_count = sync_and_mark_projects(driver, pg_cur)
        asset_count = sync_and_mark_assets(driver, pg_cur)
        
        # Verify
        verify(driver)
        
        print("\n" + "="*70)
        print("[OK] Option 2 completed!")
        print("="*70)
        print(f"\nSummary:")
        print(f"  - Problem nodes: {inv_count + po_count + emp_count + sup_count + proj_count + asset_count}")
        print(f"  - All marked with: isProblematic = true")
        print(f"\nQuery:")
        print(f"  MATCH (n) WHERE n.isProblematic = true RETURN n")
        print("="*70)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        raise
    finally:
        pg_cur.close()
        pg_conn.close()
        driver.close()

if __name__ == '__main__':
    main()
