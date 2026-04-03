# -*- coding: utf-8 -*-
"""
Option 3: Sync Problem Data with Independent Labels (No constraint conflicts)
方案 3：使用独立标签，避免约束冲突
"""

import psycopg2
from decimal import Decimal
from neo4j import GraphDatabase

PG_CONFIG = {'host': 'localhost', 'port': 5432, 'database': 'erp', 'user': 'postgres', 'password': 'postgres'}
NEO4J_CONFIG = {'uri': 'bolt://localhost:7687', 'auth': ('neo4j', 'Tony1985')}

def get_pg(): return psycopg2.connect(**PG_CONFIG)
def get_neo4j(): return GraphDatabase.driver(**NEO4J_CONFIG)
def cv(val):
    if val is None: return None
    return float(val) if isinstance(val, Decimal) else val

def main():
    print("="*70)
    print("Option 3: Sync Problem Data with Independent Labels")
    print("="*70)
    
    pg = get_pg()
    cur = pg.cursor()
    driver = get_neo4j()
    
    try:
        with driver.session() as s:
            # Problem Invoices -> ProblemInvoice
            cur.execute("SELECT invoice_id, invoice_num, invoice_amount, vendor_id, payment_status FROM ap_invoices_all WHERE invoice_id >= 2001")
            for r in cur.fetchall():
                s.run("MERGE (n:ProblemData:ProblemInvoice {id: $id}) SET n.invoiceNum=$num, n.amount=$amt, n.vendorId=$vid, n.paymentStatus=$st, n.isProblematic=true, n.problemType='data_quality_issue'", id=r[0], num=r[1], amt=cv(r[2]), vid=r[3], st=r[4])
            print(f"  OK Synced {cur.rowcount} problem invoices")
            
            # Problem POs -> ProblemPurchaseOrder
            cur.execute("SELECT po_header_id, segment1, amount, vendor_id, status_lookup_code FROM po_headers_all WHERE po_header_id >= 101")
            for r in cur.fetchall():
                s.run("MERGE (n:ProblemData:ProblemPurchaseOrder {id: $id}) SET n.poNumber=$num, n.amount=$amt, n.vendorId=$vid, n.status=$st, n.isProblematic=true, n.problemType='data_quality_issue'", id=r[0], num=r[1], amt=cv(r[2]), vid=r[3], st=r[4])
            print(f"  OK Synced {cur.rowcount} problem POs")
            
            # Noisy Employees -> ProblemEmployee
            cur.execute("SELECT employee_id, employee_name, department FROM employees WHERE employee_id >= 1501")
            for r in cur.fetchall():
                s.run("MERGE (n:ProblemData:ProblemEmployee {id: $id}) SET n.name=$nm, n.department=$dept, n.isProblematic=true, n.problemType='noisy_data'", id=r[0], nm=r[1], dept=r[2])
            print(f"  OK Synced {cur.rowcount} noisy employees")
            
            # Noisy Suppliers -> ProblemSupplier
            cur.execute("SELECT vendor_id, segment1, vendor_name, status FROM ap_suppliers WHERE vendor_id >= 52")
            for r in cur.fetchall():
                s.run("MERGE (n:ProblemData:ProblemSupplier {id: $id}) SET n.code=$code, n.name=$nm, n.status=$st, n.isProblematic=true, n.problemType='noisy_data'", id=r[0], code=r[1], nm=r[2], st=r[3])
            print(f"  OK Synced {cur.rowcount} noisy suppliers")
            
            # Noisy Projects -> ProblemProject
            cur.execute("SELECT project_id, project_number, project_name, budget_amount, actual_cost FROM pa_projects_all WHERE project_id >= 51")
            for r in cur.fetchall():
                s.run("MERGE (n:ProblemData:ProblemProject {id: $id}) SET n.projectNumber=$num, n.name=$nm, n.budget=$bud, n.actual=$act, n.isProblematic=true, n.problemType='noisy_data'", id=r[0], num=r[1], nm=r[2], bud=cv(r[3]), act=cv(r[4]))
            print(f"  OK Synced {cur.rowcount} noisy projects")
            
            # Noisy Assets -> ProblemFixedAsset
            cur.execute("SELECT asset_id, asset_number, cost, asset_status FROM fa_additions_b WHERE asset_id >= 101")
            for r in cur.fetchall():
                s.run("MERGE (n:ProblemData:ProblemFixedAsset {id: $id}) SET n.assetNumber=$num, n.cost=$cost, n.status=$st, n.isProblematic=true, n.problemType='noisy_data'", id=r[0], num=r[1], cost=cv(r[2]), st=r[3])
            print(f"  OK Synced {cur.rowcount} noisy assets")
        
        # Verify
        print("\n" + "="*70)
        print("Verification:")
        print("="*70)
        with driver.session() as s:
            r = s.run("MATCH (n:ProblemData) RETURN labels(n)[1] as label, count(n) as count ORDER BY label")
            print("\nProblem Node Types:")
            print("-"*50)
            total = 0
            for rec in r:
                label = rec['label'] or 'Unknown'
                print(f"  {label:30s}: {rec['count']}")
                total += rec['count']
            print(f"\n  Total: {total}")
        
        print("\n[OK] Option 3 completed!")
        print("\nQuery: MATCH (n:ProblemData) RETURN n")
        print("="*70)
        
    except Exception as e:
        print(f"\nERROR: {e}")
        raise
    finally:
        cur.close()
        pg.close()
        driver.close()

if __name__ == '__main__':
    main()
