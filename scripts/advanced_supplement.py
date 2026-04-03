# -*- coding: utf-8 -*-
"""
Advanced Supplement - More Data, Rules and Relationships
"""

from neo4j import GraphDatabase
import psycopg2
from datetime import datetime, timedelta
import random

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

def create_uom_nodes(driver):
    """Create Unit of Measure nodes"""
    print("="*70)
    print("Creating UOM (Unit of Measure) nodes...")
    print("="*70)
    
    with driver.session() as session:
        uoms = [
            {'code': 'EA', 'name': 'Each', 'description': 'Individual unit'},
            {'code': 'BOX', 'name': 'Box', 'description': 'Box of items'},
            {'code': 'KG', 'name': 'Kilogram', 'description': 'Weight in kilograms'},
            {'code': 'L', 'name': 'Liter', 'description': 'Volume in liters'},
            {'code': 'M', 'name': 'Meter', 'description': 'Length in meters'},
            {'code': 'SET', 'name': 'Set', 'description': 'Set of items'},
            {'code': 'PAIR', 'name': 'Pair', 'description': 'Pair of items'},
            {'code': 'DOZEN', 'name': 'Dozen', 'description': '12 items'},
        ]
        
        for uom in uoms:
            session.run("""
                MERGE (u:UOM {code: $code})
                SET u.name = $name,
                    u.description = $description
            """, **uom)
        
        print(f"  Created {len(uoms)} UOM nodes")
        
        # Link InventoryItems to UOMs
        session.run("""
            MATCH (item:InventoryItem)
            MATCH (u:UOM)
            WHERE item.uomCode = u.code
            MERGE (item)-[:USES_UOM]->(u)
        """)
        print("  Linked InventoryItems to UOMs")
        
        return len(uoms)

def create_location_nodes(driver):
    """Create Location/Warehouse nodes"""
    print("\n" + "="*70)
    print("Creating Location nodes...")
    print("="*70)
    
    with driver.session() as session:
        locations = [
            {'id': 1, 'code': 'WH-BJ-01', 'name': 'Beijing Warehouse 1', 'type': 'WAREHOUSE', 'orgId': 5},
            {'id': 2, 'code': 'WH-SH-01', 'name': 'Shanghai Warehouse 1', 'type': 'WAREHOUSE', 'orgId': 5},
            {'id': 3, 'code': 'WH-GZ-01', 'name': 'Guangzhou Warehouse 1', 'type': 'WAREHOUSE', 'orgId': 5},
            {'id': 4, 'code': 'LOC-BJ-A1', 'name': 'Beijing Office A1', 'type': 'OFFICE', 'orgId': 2},
            {'id': 5, 'code': 'LOC-SH-A1', 'name': 'Shanghai Office A1', 'type': 'OFFICE', 'orgId': 3},
        ]
        
        for loc in locations:
            session.run("""
                MERGE (l:Location {id: $id})
                SET l.code = $code,
                    l.name = $name,
                    l.type = $type,
                    l.orgId = $orgId
            """, **loc)
        
        print(f"  Created {len(locations)} Location nodes")
        
        # Link locations to organizations
        session.run("""
            MATCH (l:Location)
            MATCH (o:Organization {id: l.orgId})
            MERGE (l)-[:LOCATED_AT]->(o)
        """)
        print("  Linked locations to organizations")
        
        # Link inventory items to locations
        session.run("""
            MATCH (item:InventoryItem)
            MATCH (l:Location {type: 'WAREHOUSE'})
            WITH item, l
            LIMIT 100
            MERGE (item)-[:STORED_IN]->(l)
        """)
        print("  Linked inventory items to locations")
        
        return len(locations)

def create_payment_term_nodes(driver):
    """Create Payment Term nodes"""
    print("\n" + "="*70)
    print("Creating Payment Term nodes...")
    print("="*70)
    
    with driver.session() as session:
        payment_terms = [
            {'id': 1, 'code': 'NET30', 'name': 'Net 30 Days', 'days': 30, 'discount': None, 'discountDays': None},
            {'id': 2, 'code': 'NET60', 'name': 'Net 60 Days', 'days': 60, 'discount': None, 'discountDays': None},
            {'id': 3, 'code': 'NET90', 'name': 'Net 90 Days', 'days': 90, 'discount': None, 'discountDays': None},
            {'id': 4, 'code': 'COD', 'name': 'Cash on Delivery', 'days': 0, 'discount': None, 'discountDays': None},
            {'id': 5, 'code': 'PREPAID', 'name': 'Prepaid', 'days': -1, 'discount': None, 'discountDays': None},
            {'id': 6, 'code': '2_10_NET30', 'name': '2% 10 Days, Net 30', 'days': 30, 'discount': 0.02, 'discountDays': 10},
        ]
        
        for pt in payment_terms:
            session.run("""
                MERGE (pt:PaymentTerm {id: $id})
                SET pt.code = $code,
                    pt.name = $name,
                    pt.days = $days,
                    pt.discount = $discount,
                    pt.discountDays = $discountDays
            """, **pt)
        
        print(f"  Created {len(payment_terms)} Payment Term nodes")
        
        return len(payment_terms)

def create_tax_code_nodes(driver):
    """Create Tax Code nodes"""
    print("\n" + "="*70)
    print("Creating Tax Code nodes...")
    print("="*70)
    
    with driver.session() as session:
        tax_codes = [
            {'code': 'VAT13', 'name': 'VAT 13%', 'rate': 0.13, 'type': 'VAT'},
            {'code': 'VAT9', 'name': 'VAT 9%', 'rate': 0.09, 'type': 'VAT'},
            {'code': 'VAT6', 'name': 'VAT 6%', 'rate': 0.06, 'type': 'VAT'},
            {'code': 'TAX0', 'name': 'Tax Exempt', 'rate': 0.0, 'type': 'EXEMPT'},
            {'code': 'GST5', 'name': 'GST 5%', 'rate': 0.05, 'type': 'GST'},
        ]
        
        for tax in tax_codes:
            session.run("""
                MERGE (t:TaxCode {code: $code})
                SET t.name = $name,
                    t.rate = $rate,
                    t.type = $type
            """, **tax)
        
        print(f"  Created {len(tax_codes)} Tax Code nodes")
        
        return len(tax_codes)

def create_additional_relationships(driver, pg_cur):
    """Create additional relationships between existing nodes"""
    print("\n" + "="*70)
    print("Creating Additional Relationships...")
    print("="*70)
    
    with driver.session() as session:
        # Link Suppliers to Organizations
        session.run("""
            MATCH (sup:Supplier)
            MATCH (org:Organization {type: 'HEADQUARTER'})
            MERGE (sup)-[:SUPPLIED_TO]->(org)
        """)
        print("  Linked Suppliers to Organizations")
        
        # Link Customers to Organizations
        session.run("""
            MATCH (cust:Customer)
            MATCH (org:Organization {type: 'HEADQUARTER'})
            MERGE (cust)-[:SERVED_BY]->(org)
        """)
        print("  Linked Customers to Organizations")
        
        # Link POs to Departments (Procurement)
        session.run("""
            MATCH (po:PurchaseOrder)
            MATCH (dept:Department {name: 'Procurement'})
            MERGE (po)-[:MANAGED_BY]->(dept)
        """)
        print("  Linked PurchaseOrders to Procurement Department")
        
        # Link Invoices to Departments (Finance)
        session.run("""
            MATCH (inv:Invoice)
            MATCH (dept:Department {name: 'Finance'})
            MERGE (inv)-[:PROCESSED_BY]->(dept)
        """)
        print("  Linked Invoices to Finance Department")
        
        # Link SalesOrders to Departments (Sales)
        session.run("""
            MATCH (so:SalesOrder)
            MATCH (dept:Department {name: 'Sales'})
            MERGE (so)-[:HANDLED_BY]->(dept)
        """)
        print("  Linked SalesOrders to Sales Department")
        
        # Create APPROVED_BY relationships (random for demo)
        session.run("""
            MATCH (po:PurchaseOrder)
            WHERE po.approvedFlag = 'Y'
            MATCH (emp:Employee)
            WITH po, emp
            LIMIT 70
            MERGE (po)-[:APPROVED_BY]->(emp)
        """)
        print("  Created APPROVED_BY relationships for POs")
        
        # Create SHIPMENT relationships (for demo, link to locations)
        session.run("""
            MATCH (pol:POLine)
            MATCH (l:Location {type: 'WAREHOUSE'})
            WITH pol, l
            LIMIT 100
            MERGE (pol)-[:SHIP_TO]->(l)
        """)
        print("  Created SHIP_TO relationships for PO Lines")

def create_workflow_status_nodes(driver):
    """Create Workflow Status nodes"""
    print("\n" + "="*70)
    print("Creating Workflow Status nodes...")
    print("="*70)
    
    with driver.session() as session:
        # PO Status
        po_statuses = [
            {'code': 'DRAFT', 'name': 'Draft', 'sequence': 1},
            {'code': 'PENDING_APPROVAL', 'name': 'Pending Approval', 'sequence': 2},
            {'code': 'APPROVED', 'name': 'Approved', 'sequence': 3},
            {'code': 'CLOSED', 'name': 'Closed', 'sequence': 4},
            {'code': 'CANCELLED', 'name': 'Cancelled', 'sequence': 5},
        ]
        
        for status in po_statuses:
            session.run("""
                MERGE (s:POStatus {code: $code})
                SET s.name = $name,
                    s.sequence = $sequence,
                    s.category = 'PURCHASE_ORDER'
            """, **status)
        
        print(f"  Created {len(po_statuses)} PO Status nodes")
        
        # Invoice Status
        inv_statuses = [
            {'code': 'DRAFT', 'name': 'Draft', 'sequence': 1},
            {'code': 'VALIDATED', 'name': 'Validated', 'sequence': 2},
            {'code': 'APPROVED', 'name': 'Approved', 'sequence': 3},
            {'code': 'PAID', 'name': 'Paid', 'sequence': 4},
            {'code': 'CANCELLED', 'name': 'Cancelled', 'sequence': 5},
        ]
        
        for status in inv_statuses:
            session.run("""
                MERGE (s:InvoiceStatus {code: $code})
                SET s.name = $name,
                    s.sequence = $sequence,
                    s.category = 'INVOICE'
            """, **status)
        
        print(f"  Created {len(inv_statuses)} Invoice Status nodes")
        
        # Link entities to status nodes
        session.run("""
            MATCH (po:PurchaseOrder)
            MATCH (s:POStatus {code: po.status})
            MERGE (po)-[:HAS_STATUS]->(s)
        """)
        print("  Linked PurchaseOrders to Status nodes")
        
        session.run("""
            MATCH (inv:Invoice)
            MATCH (s:InvoiceStatus {code: inv.paymentStatus})
            MERGE (inv)-[:HAS_STATUS]->(s)
        """)
        print("  Linked Invoices to Status nodes")

def create_audit_trail_nodes(driver):
    """Create Audit Trail nodes for key entities"""
    print("\n" + "="*70)
    print("Creating Audit Trail nodes...")
    print("="*70)
    
    with driver.session() as session:
        # Create audit trail for sample POs
        session.run("""
            MATCH (po:PurchaseOrder)
            WITH po
            LIMIT 20
            CREATE (audit:AuditTrail {
                id: 'AUDIT_PO_' + toString(po.id),
                entityType: 'PurchaseOrder',
                entityId: po.id,
                action: 'CREATE',
                actionDate: po.creationDate,
                performedBy: 'System'
            })
            MERGE (audit)-[:AUDITS]->(po)
        """)
        print("  Created AuditTrail for 20 PurchaseOrders")
        
        # Create audit trail for sample Invoices
        session.run("""
            MATCH (inv:Invoice)
            WITH inv
            LIMIT 20
            CREATE (audit:AuditTrail {
                id: 'AUDIT_INV_' + toString(inv.id),
                entityType: 'Invoice',
                entityId: inv.id,
                action: 'CREATE',
                actionDate: inv.creationDate,
                performedBy: 'System'
            })
            MERGE (audit)-[:AUDITS]->(inv)
        """)
        print("  Created AuditTrail for 20 Invoices")
        
        return 40

def verify_all_supplements(driver):
    """Verify all supplements"""
    print("\n" + "="*70)
    print("Verifying All Supplements...")
    print("="*70)
    
    with driver.session() as session:
        # Count all new node types
        result = session.run("""
            MATCH (n)
            WITH labels(n)[0] as label, count(n) as count
            WHERE label IN ['UOM', 'Location', 'PaymentTerm', 'TaxCode', 
                           'POStatus', 'InvoiceStatus', 'AuditTrail']
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
            WHERE type IN ['USES_UOM', 'STORED_IN', 'LOCATED_AT', 'SUPPLIED_TO', 
                          'SERVED_BY', 'MANAGED_BY', 'PROCESSED_BY', 'HANDLED_BY',
                          'APPROVED_BY', 'SHIP_TO', 'HAS_STATUS', 'AUDITS']
            RETURN type, count
            ORDER BY type
        """)
        
        print("\nNew Relationships:")
        print("-" * 50)
        for record in result:
            print(f"  {record['type']:25s}: {record['count']}")
        
        # Total counts
        result = session.run("MATCH (n) RETURN count(n) as total")
        total_nodes = result.single()['total']
        
        result = session.run("MATCH ()-[r]->() RETURN count(r) as total")
        total_rels = result.single()['total']
        
        print("\n" + "="*50)
        print(f"  Total Nodes: {total_nodes:,}")
        print(f"  Total Relationships: {total_rels:,}")
        print("="*50)

def main():
    print("="*70)
    print("Advanced Supplement - More Data, Rules and Relationships")
    print("="*70)
    
    driver = get_neo4j_driver()
    pg_conn = get_pg_connection()
    pg_cur = pg_conn.cursor()
    
    try:
        # Create new node types
        create_uom_nodes(driver)
        create_location_nodes(driver)
        create_payment_term_nodes(driver)
        create_tax_code_nodes(driver)
        create_workflow_status_nodes(driver)
        
        # Create additional relationships
        create_additional_relationships(driver, pg_cur)
        
        # Create audit trail
        create_audit_trail_nodes(driver)
        
        # Verify
        verify_all_supplements(driver)
        
        print("\n" + "="*70)
        print("OK Advanced supplement completed!")
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
