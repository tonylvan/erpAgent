# -*- coding: utf-8 -*-
"""
Sync Problematic Data to Neo4j with ProblemData Labels
使用 ProblemData 标签标记问题数据
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

def sync_all_problem_data(driver, pg_cur):
    """Sync all problematic data with ProblemData labels"""
    print("="*70)
    print("Syncing Problematic Data to Neo4j (with ProblemData labels)")
    print("="*70)
    
    with driver.session() as session:
        # 1. Problem Invoices
        pg_cur.execute("""
            SELECT invoice_id, invoice_num, invoice_amount, vendor_id, payment_status
            FROM ap_invoices_all WHERE invoice_id >= 2001
        """)
        invoices = pg_cur.fetchall()
        for inv in invoices:
            session.run("""
                MERGE (inv:ProblemData:ProblemInvoice {id: $id})
                SET inv.invoiceNum = $num, inv.amount = $amount,
                    inv.vendorId = $vendor, inv.status = $status,
                    inv.isProblematic = true
            """, id=inv[0], num=inv[1], amount=convert_value(inv[2]), vendor=inv[3], status=inv[4])
        print(f"  OK Synced {len(invoices)} problem invoices")
        
        # 2. Problem POs
        pg_cur.execute("""
            SELECT po_header_id, segment1, amount, vendor_id, status_lookup_code
            FROM po_headers_all WHERE po_header_id >= 101
        """)
        pos = pg_cur.fetchall()
        for po in pos:
            session.run("""
                MERGE (po:ProblemData:ProblemPurchaseOrder {id: $id})
                SET po.poNumber = $num, po.amount = $amount,
                    po.vendorId = $vendor, po.status = $status,
                    po.isProblematic = true
            """, id=po[0], num=po[1], amount=convert_value(po[2]), vendor=po[3], status=po[4])
        print(f"  OK Synced {len(pos)} problem POs")
        
        # 3. Noisy Employees
        pg_cur.execute("""
            SELECT employee_id, employee_name, department
            FROM employees WHERE employee_id >= 1501
        """)
        emps = pg_cur.fetchall()
        for emp in emps:
            session.run("""
                MERGE (emp:ProblemData:ProblemEmployee {id: $id})
                SET emp.name = $name, emp.department = $dept,
                    emp.isProblematic = true
            """, id=emp[0], name=emp[1], dept=emp[2])
        print(f"  OK Synced {len(emps)} noisy employees")
        
        # 4. Noisy Suppliers
        pg_cur.execute("""
            SELECT vendor_id, segment1, vendor_name, status
            FROM ap_suppliers WHERE vendor_id >= 52
        """)
        sups = pg_cur.fetchall()
        for sup in sups:
            session.run("""
                MERGE (sup:ProblemData:ProblemSupplier {id: $id})
                SET sup.code = $code, sup.name = $name, sup.status = $status,
                    sup.isProblematic = true
            """, id=sup[0], code=sup[1], name=sup[2], status=sup[3])
        print(f"  OK Synced {len(sups)} noisy suppliers")
        
        # 5. Noisy Projects
        pg_cur.execute("""
            SELECT project_id, project_number, project_name, budget_amount, actual_cost
            FROM pa_projects_all WHERE project_id >= 51
        """)
        projs = pg_cur.fetchall()
        for proj in projs:
            session.run("""
                MERGE (proj:ProblemData:ProblemProject {id: $id})
                SET proj.projectNumber = $num, proj.name = $name,
                    proj.budget = $budget, proj.actual = $actual,
                    proj.isProblematic = true
            """, id=proj[0], num=proj[1], name=proj[2], 
                budget=convert_value(proj[3]), actual=convert_value(proj[4]))
        print(f"  OK Synced {len(projs)} noisy projects")
        
        # 6. Noisy Assets
        pg_cur.execute("""
            SELECT asset_id, asset_number, cost, asset_status
            FROM fa_additions_b WHERE asset_id >= 101
        """)
        assets = pg_cur.fetchall()
        for asset in assets:
            session.run("""
                MERGE (asset:ProblemData:ProblemFixedAsset {id: $id})
                SET asset.assetNumber = $num, asset.cost = $cost,
                    asset.status = $status, asset.isProblematic = true
            """, id=asset[0], num=asset[1], cost=convert_value(asset[2]), status=asset[3])
        print(f"  OK Synced {len(assets)} noisy assets")

def verify_sync(driver):
    """Verify sync results"""
    print("\n" + "="*70)
    print("Verifying Problem Data Sync...")
    print("="*70)
    
    with driver.session() as session:
        # Count by label
        result = session.run("""
            MATCH (n:ProblemData)
            RETURN labels(n)[1] as label, count(n) as count
            ORDER BY label
        """)
        
        print("\nProblem Node Types:")
        print("-" * 50)
        total = 0
        for rec in result:
            print(f"  {rec['label']:30s}: {rec['count']}")
            total += rec['count']
        
        print(f"\n  Total Problem Nodes: {total}")
        print("="*70)

def main():
    print("="*70)
    print("Sync Problematic Data to Neo4j (Test Graph)")
    print("="*70)
    
    pg_conn = get_pg_connection()
    pg_cur = pg_conn.cursor()
    driver = get_neo4j_driver()
    
    try:
        sync_all_problem_data(driver, pg_cur)
        verify_sync(driver)
        
        print("\n[OK] Sync completed!")
        print("\nTest Graph Info:")
        print("  All problem nodes have :ProblemData label")
        print("  Query: MATCH (n:ProblemData) RETURN n")
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
