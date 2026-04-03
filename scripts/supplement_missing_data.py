# -*- coding: utf-8 -*-
"""
Supplement Missing Nodes, Relationships and Rules
"""

from neo4j import GraphDatabase
import psycopg2

NEO4J_CONFIG = {
    'uri': 'bolt://localhost:7687',
    'user': 'neo4j',
    'password': 'Tony1985'
}

PG_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'erp',
    'user': 'postgres',
    'password': 'postgres'
}

def get_neo4j_driver():
    return GraphDatabase.driver(NEO4J_CONFIG['uri'], auth=(NEO4J_CONFIG['user'], NEO4J_CONFIG['password']))

def get_pg_connection():
    return psycopg2.connect(**PG_CONFIG)

def sync_missing_employee_relationships(driver, pg_cur):
    """Sync CREATED_BY relationships with correct property matching"""
    print("\n" + "="*70)
    print("Syncing Employee CREATED_BY relationships...")
    print("="*70)
    
    with driver.session() as session:
        # First, check what properties Employee nodes have
        result = session.run("MATCH (e:Employee) RETURN properties(e) as props LIMIT 1")
        record = result.single()
        if record:
            props = record['props']
            print(f"  Employee properties: {list(props.keys())}")
            
            # Check if 'id' property exists
            if 'id' in props:
                id_prop = 'id'
            elif 'employeeId' in props:
                id_prop = 'employeeId'
            elif 'employee_id' in props:
                id_prop = 'employee_id'
            else:
                print("  WARNING: Cannot find ID property in Employee nodes")
                return 0
        
        # Sync PO created_by
        count = 0
        pg_cur.execute("SELECT po_header_id, created_by FROM po_headers_all WHERE created_by IS NOT NULL")
        for row in pg_cur.fetchall():
            session.run(f"""
                MATCH (po:PurchaseOrder {{id: $po_id}})
                MATCH (emp:Employee {{{id_prop}: $emp_id}})
                MERGE (po)-[:CREATED_BY]->(emp)
            """, po_id=row[0], emp_id=row[1])
            count += 1
        print(f"  PO CREATED_BY: {count}")
        
        # Sync Invoice created_by
        count_inv = 0
        pg_cur.execute("SELECT invoice_id, created_by FROM ap_invoices_all WHERE created_by IS NOT NULL")
        for row in pg_cur.fetchall():
            session.run(f"""
                MATCH (inv:Invoice {{id: $inv_id}})
                MATCH (emp:Employee {{{id_prop}: $emp_id}})
                MERGE (inv)-[:CREATED_BY]->(emp)
            """, inv_id=row[0], emp_id=row[1])
            count_inv += 1
        print(f"  Invoice CREATED_BY: {count_inv}")
        
        return count + count_inv

def sync_currency_relationships(driver, pg_cur):
    """Sync USES_CURRENCY relationships"""
    print("\n" + "="*70)
    print("Syncing Currency USES_CURRENCY relationships...")
    print("="*70)
    
    with driver.session() as session:
        # Check Currency node properties
        result = session.run("MATCH (c:Currency) RETURN properties(c) as props LIMIT 1")
        record = result.single()
        if record:
            props = record['props']
            print(f"  Currency properties: {list(props.keys())}")
            
            if 'code' in props:
                code_prop = 'code'
            elif 'currencyCode' in props:
                code_prop = 'currencyCode'
            else:
                print("  WARNING: Cannot find code property in Currency nodes")
                return 0
        
        # Sync Supplier currency
        count = 0
        pg_cur.execute("SELECT vendor_id, invoice_currency_code FROM ap_suppliers WHERE invoice_currency_code IS NOT NULL")
        for row in pg_cur.fetchall():
            session.run(f"""
                MATCH (sup:Supplier {{id: $sup_id}})
                MATCH (curr:Currency {{{code_prop}: $curr_code}})
                MERGE (sup)-[:USES_CURRENCY]->(curr)
            """, sup_id=row[0], curr_code=row[1])
            count += 1
        print(f"  Supplier USES_CURRENCY: {count}")
        
        # Sync PO currency
        count_po = 0
        pg_cur.execute("SELECT po_header_id, currency_code FROM po_headers_all WHERE currency_code IS NOT NULL")
        for row in pg_cur.fetchall():
            session.run(f"""
                MATCH (po:PurchaseOrder {{id: $po_id}})
                MATCH (curr:Currency {{{code_prop}: $curr_code}})
                MERGE (po)-[:USES_CURRENCY]->(curr)
            """, po_id=row[0], curr_code=row[1])
            count_po += 1
        print(f"  PO USES_CURRENCY: {count_po}")
        
        return count + count_po

def create_organization_nodes(driver):
    """Create Organization nodes"""
    print("\n" + "="*70)
    print("Creating Organization nodes...")
    print("="*70)
    
    with driver.session() as session:
        orgs = [
            {'id': 1, 'code': 'ORG001', 'name': 'Head Office', 'type': 'HEADQUARTER'},
            {'id': 2, 'code': 'ORG002', 'name': 'Beijing Branch', 'type': 'BRANCH'},
            {'id': 3, 'code': 'ORG003', 'name': 'Shanghai Branch', 'type': 'BRANCH'},
            {'id': 4, 'code': 'ORG004', 'name': 'Guangzhou Branch', 'type': 'BRANCH'},
            {'id': 5, 'code': 'ORG005', 'name': 'Warehouse', 'type': 'WAREHOUSE'},
        ]
        
        for org in orgs:
            session.run("""
                MERGE (o:Organization {id: $id})
                SET o.code = $code,
                    o.name = $name,
                    o.type = $type
            """, **org)
        
        print(f"  Created {len(orgs)} Organization nodes")
        
        # Link employees to organizations
        session.run("""
            MATCH (emp:Employee)
            MATCH (org:Organization {type: 'HEADQUARTER'})
            MERGE (emp)-[:BELONGS_TO]->(org)
        """)
        print("  Linked employees to organizations")
        
        return len(orgs)

def create_department_nodes(driver):
    """Create Department nodes"""
    print("\n" + "="*70)
    print("Creating Department nodes...")
    print("="*70)
    
    with driver.session() as session:
        depts = [
            {'id': 1, 'code': 'DEPT001', 'name': 'Procurement', 'orgId': 1},
            {'id': 2, 'code': 'DEPT002', 'name': 'Finance', 'orgId': 1},
            {'id': 3, 'code': 'DEPT003', 'name': 'Sales', 'orgId': 1},
            {'id': 4, 'code': 'DEPT004', 'name': 'Warehouse', 'orgId': 5},
            {'id': 5, 'code': 'DEPT005', 'name': 'IT', 'orgId': 1},
            {'id': 6, 'code': 'DEPT006', 'name': 'HR', 'orgId': 1},
        ]
        
        for dept in depts:
            session.run("""
                MERGE (d:Department {id: $id})
                SET d.code = $code,
                    d.name = $name,
                    d.orgId = $orgId
            """, **dept)
        
        print(f"  Created {len(depts)} Department nodes")
        
        # Link departments to organizations
        session.run("""
            MATCH (d:Department)
            MATCH (o:Organization {id: d.orgId})
            MERGE (d)-[:BELONGS_TO]->(o)
        """)
        print("  Linked departments to organizations")
        
        # Link employees to departments (random assignment for demo)
        session.run("""
            MATCH (emp:Employee)
            MATCH (d:Department)
            WITH emp, d
            LIMIT 100
            MERGE (emp)-[:WORKS_IN]->(d)
        """)
        print("  Linked employees to departments")
        
        return len(depts)

def create_additional_rules(driver):
    """Create additional business rules"""
    print("\n" + "="*70)
    print("Creating Additional Business Rules...")
    print("="*70)
    
    with driver.session() as session:
        # Date range validation
        session.run("""
            CREATE (r:BusinessRule {
                id: 'VALIDATION_006',
                code: 'DATE_RANGE_CHECK',
                name: '日期范围验证',
                description: '发票日期不能早于 PO 日期',
                category: 'VALIDATION',
                priority: 2
            })
        """)
        print("  [OK] VALIDATION_006: 日期范围验证")
        
        # Supplier status validation
        session.run("""
            CREATE (r:BusinessRule {
                id: 'VALIDATION_007',
                code: 'SUPPLIER_STATUS_CHECK',
                name: '供应商状态验证',
                description: '只能与 ACTIVE 状态的供应商交易',
                category: 'VALIDATION',
                priority: 1
            })
        """)
        print("  [OK] VALIDATION_007: 供应商状态验证")
        
        # Credit limit validation
        session.run("""
            CREATE (r:BusinessRule {
                id: 'VALIDATION_008',
                code: 'CREDIT_LIMIT_CHECK',
                name: '信用额度验证',
                description: '客户订单金额不能超过信用额度',
                category: 'VALIDATION',
                priority: 1
            })
        """)
        print("  [OK] VALIDATION_008: 信用额度验证")
        
        # Payment term validation
        session.run("""
            CREATE (r:BusinessRule {
                id: 'VALIDATION_009',
                code: 'PAYMENT_TERM_CHECK',
                name: '付款条款验证',
                description: '付款日期必须符合付款条款',
                category: 'VALIDATION',
                priority: 2
            })
        """)
        print("  [OK] VALIDATION_009: 付款条款验证")
        
        # Inventory level validation
        session.run("""
            CREATE (r:BusinessRule {
                id: 'VALIDATION_010',
                code: 'INVENTORY_LEVEL_CHECK',
                name: '库存水平验证',
                description: '库存不能低于安全库存水平',
                category: 'VALIDATION',
                priority: 1
            })
        """)
        print("  [OK] VALIDATION_010: 库存水平验证")
        
        print("\n  Created 5 additional validation rules")

def verify_supplements(driver):
    """Verify all supplements"""
    print("\n" + "="*70)
    print("Verifying Supplements...")
    print("="*70)
    
    with driver.session() as session:
        # Count new node types
        result = session.run("""
            MATCH (n)
            WITH labels(n)[0] as label, count(n) as count
            WHERE label IN ['Organization', 'Department']
            RETURN label, count
            ORDER BY label
        """)
        
        print("\nNew Node Types:")
        print("-" * 50)
        for record in result:
            print(f"  {record['label']:25s}: {record['count']}")
        
        # Count new relationships
        result = session.run("""
            MATCH ()-[r]->()
            WITH type(r) as type, count(r) as count
            WHERE type IN ['BELONGS_TO', 'WORKS_IN', 'CREATED_BY', 'USES_CURRENCY']
            RETURN type, count
            ORDER BY type
        """)
        
        print("\nNew/Updated Relationships:")
        print("-" * 50)
        for record in result:
            print(f"  {record['type']:25s}: {record['count']}")
        
        # Count total rules
        result = session.run("""
            MATCH (r:BusinessRule)
            RETURN r.category as category, count(r) as count
            ORDER BY category
        """)
        
        print("\nBusiness Rules (All):")
        print("-" * 50)
        for record in result:
            print(f"  {record['category']:15s}: {record['count']}")

def main():
    print("="*70)
    print("Supplement Missing Nodes, Relationships and Rules")
    print("="*70)
    
    driver = get_neo4j_driver()
    pg_conn = get_pg_connection()
    pg_cur = pg_conn.cursor()
    
    try:
        # Sync relationships
        sync_missing_employee_relationships(driver, pg_cur)
        sync_currency_relationships(driver, pg_cur)
        
        # Create new node types
        create_organization_nodes(driver)
        create_department_nodes(driver)
        
        # Create additional rules
        create_additional_rules(driver)
        
        # Verify
        verify_supplements(driver)
        
        print("\n" + "="*70)
        print("OK Supplement sync completed!")
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
