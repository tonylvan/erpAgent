# -*- coding: utf-8 -*-
"""
Mark Problematic Data in Neo4j (Option 2)
标记现有节点为问题数据，不创建新节点
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

def mark_problematic_invoices(driver, pg_cur):
    """Mark problematic invoices in existing nodes"""
    print("\n" + "="*70)
    print("Marking problematic invoices...")
    print("="*70)
    
    with driver.session() as session:
        # Get problematic invoice IDs
        pg_cur.execute("SELECT invoice_id FROM ap_invoices_all WHERE invoice_id >= 2001")
        problem_ids = [row[0] for row in pg_cur.fetchall()]
        
        marked = 0
        for inv_id in problem_ids:
            result = session.run("""
                MATCH (inv:Invoice {id: $id})
                SET inv.isProblematic = true,
                    inv.problemType = 'data_quality_issue'
                RETURN inv
            """, id=inv_id)
            if result.single():
                marked += 1
        
        print(f"  OK Marked {marked}/{len(problem_ids)} problematic invoices")
        return marked

def mark_problematic_pos(driver, pg_cur):
    """Mark problematic POs in existing nodes"""
    print("\n" + "="*70)
    print("Marking problematic POs...")
    print("="*70)
    
    with driver.session() as session:
        pg_cur.execute("SELECT po_header_id FROM po_headers_all WHERE po_header_id >= 101")
        problem_ids = [row[0] for row in pg_cur.fetchall()]
        
        marked = 0
        for po_id in problem_ids:
            result = session.run("""
                MATCH (po:PurchaseOrder {id: $id})
                SET po.isProblematic = true,
                    po.problemType = 'data_quality_issue'
                RETURN po
            """, id=po_id)
            if result.single():
                marked += 1
        
        print(f"  OK Marked {marked}/{len(problem_ids)} problematic POs")
        return marked

def mark_noisy_employees(driver, pg_cur):
    """Mark noisy employees in existing nodes"""
    print("\n" + "="*70)
    print("Marking noisy employees...")
    print("="*70)
    
    with driver.session() as session:
        pg_cur.execute("SELECT employee_id FROM employees WHERE employee_id >= 1501")
        problem_ids = [row[0] for row in pg_cur.fetchall()]
        
        marked = 0
        for emp_id in problem_ids:
            result = session.run("""
                MATCH (emp:Employee {id: $id})
                SET emp.isProblematic = true,
                    emp.problemType = 'noisy_data'
                RETURN emp
            """, id=emp_id)
            if result.single():
                marked += 1
        
        print(f"  OK Marked {marked}/{len(problem_ids)} noisy employees")
        return marked

def mark_noisy_suppliers(driver, pg_cur):
    """Mark noisy suppliers in existing nodes"""
    print("\n" + "="*70)
    print("Marking noisy suppliers...")
    print("="*70)
    
    with driver.session() as session:
        pg_cur.execute("SELECT vendor_id FROM ap_suppliers WHERE vendor_id >= 52")
        problem_ids = [row[0] for row in pg_cur.fetchall()]
        
        marked = 0
        for sup_id in problem_ids:
            result = session.run("""
                MATCH (sup:Supplier {id: $id})
                SET sup.isProblematic = true,
                    sup.problemType = 'noisy_data'
                RETURN sup
            """, id=sup_id)
            if result.single():
                marked += 1
        
        print(f"  OK Marked {marked}/{len(problem_ids)} noisy suppliers")
        return marked

def mark_noisy_projects(driver, pg_cur):
    """Mark noisy projects in existing nodes"""
    print("\n" + "="*70)
    print("Marking noisy projects...")
    print("="*70)
    
    with driver.session() as session:
        pg_cur.execute("SELECT project_id FROM pa_projects_all WHERE project_id >= 51")
        problem_ids = [row[0] for row in pg_cur.fetchall()]
        
        marked = 0
        for proj_id in problem_ids:
            result = session.run("""
                MATCH (proj:Project {id: $id})
                SET proj.isProblematic = true,
                    proj.problemType = 'noisy_data'
                RETURN proj
            """, id=proj_id)
            if result.single():
                marked += 1
        
        print(f"  OK Marked {marked}/{len(problem_ids)} noisy projects")
        return marked

def mark_noisy_assets(driver, pg_cur):
    """Mark noisy assets in existing nodes"""
    print("\n" + "="*70)
    print("Marking noisy assets...")
    print("="*70)
    
    with driver.session() as session:
        pg_cur.execute("SELECT asset_id FROM fa_additions_b WHERE asset_id >= 101")
        problem_ids = [row[0] for row in pg_cur.fetchall()]
        
        marked = 0
        for asset_id in problem_ids:
            result = session.run("""
                MATCH (asset:FixedAsset {id: $id})
                SET asset.isProblematic = true,
                    asset.problemType = 'noisy_data'
                RETURN asset
            """, id=asset_id)
            if result.single():
                marked += 1
        
        print(f"  OK Marked {marked}/{len(problem_ids)} noisy assets")
        return marked

def verify_marks(driver):
    """Verify marked nodes"""
    print("\n" + "="*70)
    print("Verifying Marked Problem Data...")
    print("="*70)
    
    with driver.session() as session:
        # Count by type
        result = session.run("""
            MATCH (n)
            WHERE n.isProblematic = true
            RETURN labels(n)[0] as label, count(n) as count
            ORDER BY label
        """)
        
        print("\nMarked Problem Nodes:")
        print("-" * 50)
        total = 0
        for rec in result:
            label = rec['label'] or 'Unknown'
            print(f"  {label:30s}: {rec['count']}")
            total += rec['count']
        
        print(f"\n  Total Marked Nodes: {total}")
        print("="*70)
        
        # Show sample
        result = session.run("""
            MATCH (n)
            WHERE n.isProblematic = true
            RETURN labels(n)[0] as label, n.id as id, n.problemType as type
            LIMIT 5
        """)
        
        print("\nSample Marked Nodes:")
        print("-" * 50)
        for rec in result:
            label = rec['label'] or 'Unknown'
            print(f"  {label}: ID={rec['id']}, Type={rec['type']}")

def main():
    print("="*70)
    print("Mark Problematic Data in Neo4j (Option 2)")
    print("="*70)
    print("\nStrategy: Mark existing nodes with isProblematic=true")
    print("          Do NOT create separate ProblemData nodes")
    print("="*70)
    
    pg_conn = get_pg_connection()
    pg_cur = pg_conn.cursor()
    driver = get_neo4j_driver()
    
    try:
        # Mark all problematic data
        inv_count = mark_problematic_invoices(driver, pg_cur)
        po_count = mark_problematic_pos(driver, pg_cur)
        emp_count = mark_noisy_employees(driver, pg_cur)
        sup_count = mark_noisy_suppliers(driver, pg_cur)
        proj_count = mark_noisy_projects(driver, pg_cur)
        asset_count = mark_noisy_assets(driver, pg_cur)
        
        # Verify
        verify_marks(driver)
        
        print("\n" + "="*70)
        print("[OK] Marking completed!")
        print("="*70)
        print("\nTest Graph Info:")
        print("  All problem nodes marked with: isProblematic = true")
        print("  Query: MATCH (n) WHERE n.isProblematic = true RETURN n")
        print("  Filter: MATCH (n) WHERE n.isProblematic IS NOT true RETURN n")
        print("  Usage: Testing data quality rules and anomaly detection")
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
