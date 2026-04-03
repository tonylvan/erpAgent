# -*- coding: utf-8 -*-
"""
Sync Problematic Data to Separate Neo4j Test Database
用于测试的独立问题数据图
"""

import psycopg2
from decimal import Decimal
from neo4j import GraphDatabase

# PostgreSQL config
PG_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'erp',
    'user': 'postgres',
    'password': 'postgres'
}

# Neo4j Test config (same database, different labels)
NEO4J_CONFIG = {
    'uri': 'bolt://localhost:7687',
    'auth': ('neo4j', 'Tony1985')
}

def get_pg_connection():
    return psycopg2.connect(**PG_CONFIG)

def get_neo4j_driver():
    return GraphDatabase.driver(**NEO4J_TEST_CONFIG)

def convert_value(val):
    """Convert values for Neo4j compatibility"""
    if val is None:
        return None
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, (int, float, str)):
        return val
    return str(val)

def create_test_database(driver):
    """Create test database if not exists"""
    print("="*70)
    print("Creating test database 'erp_test'...")
    print("="*70)
    
    with driver.session(database='system') as session:
        try:
            session.run("CREATE DATABASE erp_test IF NOT EXISTS")
            print("  OK Database 'erp_test' created/verified")
        except Exception as e:
            print(f"  Note: {e}")

def sync_problematic_invoices(driver, pg_cur):
    """Sync problematic invoices"""
    print("\n" + "="*70)
    print("Syncing problematic invoices...")
    print("="*70)
    
    with driver.session(database='erp_test') as session:
        # Problem invoices (ID >= 2001)
        pg_cur.execute("""
            SELECT invoice_id, invoice_num, invoice_type_lookup_code, vendor_id,
                   invoice_amount, payment_status, invoice_date, created_by
            FROM ap_invoices_all
            WHERE invoice_id >= 2001
        """)
        invoices = pg_cur.fetchall()
        
        for inv in invoices:
            session.run("""
                MERGE (inv:ProblemInvoice {id: $id})
                SET inv.invoiceNum = $invoice_num,
                    inv.type = $type,
                    inv.vendorId = $vendor_id,
                    inv.amount = $amount,
                    inv.paymentStatus = $status,
                    inv.invoiceDate = toString($invoice_date),
                    inv.createdBy = $created_by,
                    inv.isProblematic = true
            """, id=inv[0], invoice_num=inv[1], type=inv[2], vendor_id=inv[3],
                amount=convert_value(inv[4]), status=inv[5], 
                invoice_date=inv[6], created_by=inv[7])
        
        print(f"  OK Synced {len(invoices)} problematic invoices")
        return len(invoices)

def sync_problematic_pos(driver, pg_cur):
    """Sync problematic POs"""
    print("\n" + "="*70)
    print("Syncing problematic POs...")
    print("="*70)
    
    with driver.session(database='erp_test') as session:
        # Problem POs (ID >= 101)
        pg_cur.execute("""
            SELECT po_header_id, segment1, type_lookup_code, vendor_id,
                   amount, status_lookup_code, approved_flag, creation_date
            FROM po_headers_all
            WHERE po_header_id >= 101
        """)
        pos = pg_cur.fetchall()
        
        for po in pos:
            session.run("""
                MERGE (po:ProblemPurchaseOrder {id: $id})
                SET po.poNumber = $po_number,
                    po.type = $type,
                    po.vendorId = $vendor_id,
                    po.amount = $amount,
                    po.status = $status,
                    po.approvedFlag = $approved,
                    po.creationDate = toString($creation_date),
                    po.isProblematic = true
            """, id=po[0], po_number=po[1], type=po[2], vendor_id=po[3],
                amount=convert_value(po[4]), status=po[5], 
                approved=po[6], creation_date=po[7])
        
        print(f"  OK Synced {len(pos)} problematic POs")
        return len(pos)

def sync_noisy_employees(driver, pg_cur):
    """Sync noisy employees"""
    print("\n" + "="*70)
    print("Syncing noisy employees...")
    print("="*70)
    
    with driver.session(database='erp_test') as session:
        # Noisy employees (ID >= 1501)
        pg_cur.execute("""
            SELECT employee_id, employee_name, department
            FROM employees
            WHERE employee_id >= 1501
        """)
        employees = pg_cur.fetchall()
        
        for emp in employees:
            session.run("""
                MERGE (emp:ProblemEmployee {id: $id})
                SET emp.name = $name,
                    emp.department = $dept,
                    emp.isProblematic = true
            """, id=emp[0], name=emp[1], dept=emp[2])
        
        print(f"  OK Synced {len(employees)} noisy employees")
        return len(employees)

def sync_noisy_suppliers(driver, pg_cur):
    """Sync noisy suppliers"""
    print("\n" + "="*70)
    print("Syncing noisy suppliers...")
    print("="*70)
    
    with driver.session(database='erp_test') as session:
        # Noisy suppliers (ID >= 52)
        pg_cur.execute("""
            SELECT vendor_id, segment1, vendor_name, vendor_type_lookup_code, status
            FROM ap_suppliers
            WHERE vendor_id >= 52
        """)
        suppliers = pg_cur.fetchall()
        
        for sup in suppliers:
            session.run("""
                MERGE (sup:ProblemSupplier {id: $id})
                SET sup.code = $code,
                    sup.name = $name,
                    sup.type = $type,
                    sup.status = $status,
                    sup.isProblematic = true
            """, id=sup[0], code=sup[1], name=sup[2], type=sup[3], status=sup[4])
        
        print(f"  OK Synced {len(suppliers)} noisy suppliers")
        return len(suppliers)

def sync_noisy_projects(driver, pg_cur):
    """Sync noisy projects"""
    print("\n" + "="*70)
    print("Syncing noisy projects...")
    print("="*70)
    
    with driver.session(database='erp_test') as session:
        # Noisy projects (ID >= 51)
        pg_cur.execute("""
            SELECT project_id, project_number, project_name, project_type,
                   status_code, budget_amount, actual_cost, manager_id
            FROM pa_projects_all
            WHERE project_id >= 51
        """)
        projects = pg_cur.fetchall()
        
        for proj in projects:
            session.run("""
                MERGE (proj:ProblemProject {id: $id})
                SET proj.projectNumber = $proj_num,
                    proj.name = $proj_name,
                    proj.type = $proj_type,
                    proj.statusCode = $status,
                    proj.budgetAmount = $budget,
                    proj.actualCost = $actual,
                    proj.managerId = $manager_id,
                    proj.isProblematic = true
            """, id=proj[0], proj_num=proj[1], proj_name=proj[2], 
                proj_type=proj[3], status=proj[4], 
                budget=convert_value(proj[5]), actual=convert_value(proj[6]),
                manager_id=proj[7])
        
        print(f"  OK Synced {len(projects)} noisy projects")
        return len(projects)

def sync_noisy_assets(driver, pg_cur):
    """Sync noisy assets"""
    print("\n" + "="*70)
    print("Syncing noisy assets...")
    print("="*70)
    
    with driver.session(database='erp_test') as session:
        # Noisy assets (ID >= 101)
        pg_cur.execute("""
            SELECT asset_id, asset_number, asset_type, asset_status,
                   cost, category_id, book_type_code
            FROM fa_additions_b
            WHERE asset_id >= 101
        """)
        assets = pg_cur.fetchall()
        
        for asset in assets:
            session.run("""
                MERGE (asset:ProblemFixedAsset {id: $id})
                SET asset.assetNumber = $asset_num,
                    asset.assetType = $type,
                    asset.status = $status,
                    asset.cost = $cost,
                    asset.categoryId = $cat_id,
                    asset.bookTypeCode = $book_type,
                    asset.isProblematic = true
            """, id=asset[0], asset_num=asset[1], type=asset[2], 
                status=asset[3], cost=convert_value(asset[4]), 
                cat_id=asset[5], book_type=asset[6])
        
        print(f"  OK Synced {len(assets)} noisy assets")
        return len(assets)

def create_problem_relationships(driver):
    """Create relationships between problem entities"""
    print("\n" + "="*70)
    print("Creating problem entity relationships...")
    print("="*70)
    
    with driver.session(database='erp_test') as session:
        # Link invoices to vendors
        result = session.run("""
            MATCH (inv:ProblemInvoice)
            MATCH (sup:ProblemSupplier)
            WHERE inv.vendorId = sup.id
            MERGE (inv)-[:FROM_SUPPLIER]->(sup)
            RETURN count(inv) as count
        """)
        inv_count = result.single()['count']
        print(f"  OK Created {inv_count} invoice-supplier relationships")
        
        # Link POs to vendors
        result = session.run("""
            MATCH (po:ProblemPurchaseOrder)
            MATCH (sup:ProblemSupplier)
            WHERE po.vendorId = sup.id
            MERGE (po)-[:FROM_SUPPLIER]->(sup)
            RETURN count(po) as count
        """)
        po_count = result.single()['count']
        print(f"  OK Created {po_count} PO-supplier relationships")

def verify_sync(driver):
    """Verify sync results"""
    print("\n" + "="*70)
    print("Verifying Test Database Sync...")
    print("="*70)
    
    with driver.session(database='erp_test') as session:
        # Count problem nodes
        result = session.run("""
            MATCH (n)
            WHERE n:ProblemData OR n.isProblematic = true
            RETURN labels(n)[0] as label, count(n) as count
            ORDER BY label
        """)
        
        print("\nProblem Node Types:")
        print("-" * 50)
        total_nodes = 0
        for record in result:
            print(f"  {record['label']:30s}: {record['count']}")
            total_nodes += record['count']
        
        # Count relationships
        result = session.run("""
            MATCH ()-[r]->()
            RETURN type(r) as type, count(r) as count
            ORDER BY type
        """)
        
        print("\nProblem Relationships:")
        print("-" * 50)
        total_rels = 0
        for record in result:
            print(f"  {record['type']:30s}: {record['count']}")
            total_rels += record['count']
        
        print("\n" + "="*50)
        print(f"  Total Problem Nodes: {total_nodes}")
        print(f"  Total Relationships: {total_rels}")
        print("="*50)

def main():
    print("="*70)
    print("Sync Problematic Data to Neo4j Test Database")
    print("="*70)
    
    pg_conn = get_pg_connection()
    pg_cur = pg_conn.cursor()
    driver = get_neo4j_driver()
    
    try:
        # Create test database
        create_test_database(driver)
        
        # Sync all problematic data
        inv_count = sync_problematic_invoices(driver, pg_cur)
        po_count = sync_problematic_pos(driver, pg_cur)
        emp_count = sync_noisy_employees(driver, pg_cur)
        sup_count = sync_noisy_suppliers(driver, pg_cur)
        proj_count = sync_noisy_projects(driver, pg_cur)
        asset_count = sync_noisy_assets(driver, pg_cur)
        
        # Create relationships
        create_problem_relationships(driver)
        
        # Verify
        verify_sync(driver)
        
        print("\n" + "="*70)
        print("OK Test database sync completed successfully!")
        print("="*70)
        print(f"\nSummary:")
        print(f"  Problem Invoices: {inv_count}")
        print(f"  Problem POs: {po_count}")
        print(f"  Noisy Employees: {emp_count}")
        print(f"  Noisy Suppliers: {sup_count}")
        print(f"  Noisy Projects: {proj_count}")
        print(f"  Noisy Assets: {asset_count}")
        print("="*70)
        print("\nTest Database Info:")
        print("  Database: erp_test")
        print("  URL: bolt://localhost:7687")
        print("  Usage: Testing data quality rules and anomaly detection")
        print("="*70)
        
    except Exception as e:
        print(f"\nERROR Error during sync: {e}")
        raise
    finally:
        pg_cur.close()
        pg_conn.close()
        driver.close()

if __name__ == '__main__':
    main()
