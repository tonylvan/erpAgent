# -*- coding: utf-8 -*-
"""
Option 2: Sync Problem Data and Mark (Use ON CREATE SET to avoid constraint errors)
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
    print("Option 2: Sync and Mark Problem Data")
    print("="*70)
    
    pg = get_pg()
    cur = pg.cursor()
    driver = get_neo4j()
    
    try:
        with driver.session() as s:
            # Invoices
            cur.execute("SELECT invoice_id, invoice_num, invoice_amount, vendor_id, payment_status FROM ap_invoices_all WHERE invoice_id >= 2001")
            for r in cur.fetchall():
                s.run("MERGE (n:Invoice {id: $id}) ON CREATE SET n.invoiceNum=$num, n.amount=$amt, n.vendorId=$vid, n.paymentStatus=$st SET n.isProblematic=true, n.problemType='data_quality_issue'", id=r[0], num=r[1], amt=cv(r[2]), vid=r[3], st=r[4])
            print(f"  OK Synced {cur.rowcount} problem invoices")
            
            # POs
            cur.execute("SELECT po_header_id, segment1, amount, vendor_id, status_lookup_code FROM po_headers_all WHERE po_header_id >= 101")
            for r in cur.fetchall():
                s.run("MERGE (n:PurchaseOrder {id: $id}) ON CREATE SET n.poNumber=$num, n.amount=$amt, n.vendorId=$vid, n.status=$st SET n.isProblematic=true, n.problemType='data_quality_issue'", id=r[0], num=r[1], amt=cv(r[2]), vid=r[3], st=r[4])
            print(f"  OK Synced {cur.rowcount} problem POs")
            
            # Employees
            cur.execute("SELECT employee_id, employee_name, department FROM employees WHERE employee_id >= 1501")
            for r in cur.fetchall():
                s.run("MERGE (n:Employee {id: $id}) ON CREATE SET n.name=$nm, n.department=$dept SET n.isProblematic=true, n.problemType='noisy_data'", id=r[0], nm=r[1], dept=r[2])
            print(f"  OK Synced {cur.rowcount} noisy employees")
            
            # Suppliers
            cur.execute("SELECT vendor_id, segment1, vendor_name, status FROM ap_suppliers WHERE vendor_id >= 52")
            for r in cur.fetchall():
                s.run("MERGE (n:Supplier {id: $id}) ON CREATE SET n.code=$code, n.name=$nm, n.status=$st SET n.isProblematic=true, n.problemType='noisy_data'", id=r[0], code=r[1], nm=r[2], st=r[3])
            print(f"  OK Synced {cur.rowcount} noisy suppliers")
            
            # Projects
            cur.execute("SELECT project_id, project_number, project_name, budget_amount, actual_cost FROM pa_projects_all WHERE project_id >= 51")
            for r in cur.fetchall():
                s.run("MERGE (n:Project {id: $id}) ON CREATE SET n.projectNumber=$num, n.name=$nm, n.budget=$bud, n.actual=$act SET n.isProblematic=true, n.problemType='noisy_data'", id=r[0], num=r[1], nm=r[2], bud=cv(r[3]), act=cv(r[4]))
            print(f"  OK Synced {cur.rowcount} noisy projects")
            
            # Assets
            cur.execute("SELECT asset_id, asset_number, cost, asset_status FROM fa_additions_b WHERE asset_id >= 101")
            for r in cur.fetchall():
                s.run("MERGE (n:FixedAsset {id: $id}) ON CREATE SET n.assetNumber=$num, n.cost=$cost, n.status=$st SET n.isProblematic=true, n.problemType='noisy_data'", id=r[0], num=r[1], cost=cv(r[2]), st=r[3])
            print(f"  OK Synced {cur.rowcount} noisy assets")
        
        # Verify
        print("\n" + "="*70)
        print("Verification:")
        print("="*70)
        with driver.session() as s:
            r = s.run("MATCH (n) WHERE n.isProblematic=true RETURN labels(n)[0] as label, count(n) as count ORDER BY label")
            print("\nMarked Problem Nodes:")
            print("-"*50)
            total = 0
            for rec in r:
                label = rec['label'] or 'Unknown'
                print(f"  {label:30s}: {rec['count']}")
                total += rec['count']
            print(f"\n  Total: {total}")
        
        print("\n[OK] Option 2 completed!")
        print("\nQuery: MATCH (n) WHERE n.isProblematic=true RETURN n")
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
