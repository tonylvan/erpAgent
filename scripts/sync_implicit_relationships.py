# -*- coding: utf-8 -*-
"""
Sync Implicit Relationships to Neo4j
Includes: CREATED_BY, APPROVED_BY, USES_CURRENCY, MATCHES_PO_LINE, HAS_PAYMENT
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

# Neo4j config
NEO4J_CONFIG = {
    'uri': 'bolt://localhost:7687',
    'user': 'neo4j',
    'password': 'Tony1985'
}

def get_pg_connection():
    conn = psycopg2.connect(**PG_CONFIG)
    conn.autocommit = True  # Enable autocommit to avoid transaction errors
    return conn

def get_neo4j_driver():
    return GraphDatabase.driver(NEO4J_CONFIG['uri'], auth=(NEO4J_CONFIG['user'], NEO4J_CONFIG['password']))

def convert_value(val):
    """Convert Decimal and other types to Neo4j-compatible types"""
    if val is None:
        return None
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, (int, float, str)):
        return val
    return str(val)

def sync_created_by_relationships(driver, pg_cur):
    """Sync CREATED_BY relationships for all entities"""
    print("\n" + "="*70)
    print("Syncing CREATED_BY relationships...")
    print("="*70)
    
    with driver.session() as session:
        count = 0
        
        # PO created_by
        pg_cur.execute("""
            SELECT po_header_id, created_by FROM po_headers_all 
            WHERE created_by IS NOT NULL
        """)
        for row in pg_cur.fetchall():
            session.run("""
                MATCH (po:PurchaseOrder {id: $po_id})
                MATCH (emp:Employee {id: $emp_id})
                MERGE (po)-[:CREATED_BY]->(emp)
            """, po_id=int(row[0]), emp_id=int(row[1]))
            count += 1
        print(f"  PurchaseOrder CREATED_BY: {count}")
        
        # Invoice created_by
        count_inv = 0
        pg_cur.execute("""
            SELECT invoice_id, created_by FROM ap_invoices_all 
            WHERE created_by IS NOT NULL
        """)
        for row in pg_cur.fetchall():
            session.run("""
                MATCH (inv:Invoice {id: $inv_id})
                MATCH (emp:Employee {id: $emp_id})
                MERGE (inv)-[:CREATED_BY]->(emp)
            """, inv_id=int(row[0]), emp_id=int(row[1]))
            count_inv += 1
        print(f"  Invoice CREATED_BY: {count_inv}")
        count += count_inv
        
        # SalesOrder created_by (skip if column doesn't exist)
        count_so = 0
        try:
            pg_cur.execute("""
                SELECT header_id, created_by FROM so_headers_all 
                WHERE created_by IS NOT NULL
            """)
            for row in pg_cur.fetchall():
                session.run("""
                    MATCH (so:SalesOrder {id: $so_id})
                    MATCH (emp:Employee {id: $emp_id})
                    MERGE (so)-[:CREATED_BY]->(emp)
                """, so_id=int(row[0]), emp_id=int(row[1]))
                count_so += 1
            print(f"  SalesOrder CREATED_BY: {count_so}")
        except:
            print(f"  SalesOrder CREATED_BY: skipped (column not exists)")
        count += count_so
        
        print(f"  TOTAL CREATED_BY: {count}")
        return count

def sync_uses_currency_relationships(driver, pg_cur):
    """Sync USES_CURRENCY relationships"""
    print("\n" + "="*70)
    print("Syncing USES_CURRENCY relationships...")
    print("="*70)
    
    with driver.session() as session:
        count = 0
        
        # Supplier currency
        pg_cur.execute("""
            SELECT vendor_id, invoice_currency_code FROM ap_suppliers 
            WHERE invoice_currency_code IS NOT NULL
        """)
        for row in pg_cur.fetchall():
            session.run("""
                MATCH (sup:Supplier {id: $sup_id})
                MATCH (curr:Currency {code: $curr_code})
                MERGE (sup)-[:USES_CURRENCY]->(curr)
            """, sup_id=int(row[0]), curr_code=row[1])
            count += 1
        print(f"  Supplier USES_CURRENCY: {count}")
        
        # PO currency
        count_po = 0
        pg_cur.execute("""
            SELECT po_header_id, currency_code FROM po_headers_all 
            WHERE currency_code IS NOT NULL
        """)
        for row in pg_cur.fetchall():
            session.run("""
                MATCH (po:PurchaseOrder {id: $po_id})
                MATCH (curr:Currency {code: $curr_code})
                MERGE (po)-[:USES_CURRENCY]->(curr)
            """, po_id=int(row[0]), curr_code=row[1])
            count_po += 1
        print(f"  PurchaseOrder USES_CURRENCY: {count_po}")
        count += count_po
        
        # Invoice currency (skip if column doesn't exist)
        count_inv = 0
        try:
            pg_cur.execute("""
                SELECT invoice_id, invoice_currency_code FROM ap_invoices_all 
                WHERE invoice_currency_code IS NOT NULL
            """)
            for row in pg_cur.fetchall():
                session.run("""
                    MATCH (inv:Invoice {id: $inv_id})
                    MATCH (curr:Currency {code: $curr_code})
                    MERGE (inv)-[:USES_CURRENCY]->(curr)
                """, inv_id=int(row[0]), curr_code=row[1])
                count_inv += 1
            print(f"  Invoice USES_CURRENCY: {count_inv}")
        except:
            print(f"  Invoice USES_CURRENCY: skipped (column not exists)")
        count += count_inv
        
        print(f"  TOTAL USES_CURRENCY: {count}")
        return count

def sync_matches_po_line_relationships(driver, pg_cur):
    """Sync MATCHES_PO_LINE relationships (InvoiceLine -> POLine)"""
    print("\n" + "="*70)
    print("Syncing MATCHES_PO_LINE relationships...")
    print("="*70)
    
    with driver.session() as session:
        count = 0
        
        try:
            pg_cur.execute("""
                SELECT invoice_line_id, po_line_id FROM ap_invoice_lines_all 
                WHERE po_line_id IS NOT NULL
            """)
            for row in pg_cur.fetchall():
                session.run("""
                    MATCH (inl:InvoiceLine {id: $inl_id})
                    MATCH (pol:POLine {id: $pol_id})
                    MERGE (inl)-[:MATCHES_PO_LINE]->(pol)
                """, inl_id=int(row[0]), pol_id=int(row[1]))
                count += 1
            print(f"  MATCHES_PO_LINE: {count}")
        except:
            print(f"  MATCHES_PO_LINE: skipped (column not exists)")
        
        return count

def sync_has_payment_relationships(driver, pg_cur):
    """Sync HAS_PAYMENT relationships (Invoice -> Payment)"""
    print("\n" + "="*70)
    print("Syncing HAS_PAYMENT relationships...")
    print("="*70)
    
    with driver.session() as session:
        count = 0
        
        try:
            pg_cur.execute("""
                SELECT invoice_id, check_id FROM ap_invoice_payments_all
            """)
            for row in pg_cur.fetchall():
                session.run("""
                    MATCH (inv:Invoice {id: $inv_id})
                    MATCH (pay:Payment {id: $pay_id})
                    MERGE (inv)-[:HAS_PAYMENT]->(pay)
                """, inv_id=int(row[0]), pay_id=int(row[1]))
                count += 1
            print(f"  HAS_PAYMENT: {count}")
        except:
            print(f"  HAS_PAYMENT: skipped (table empty or not exists)")
        
        return count

def sync_has_distribution_relationships(driver, pg_cur):
    """Sync HAS_DISTRIBUTION relationships (POLine -> PODistribution)"""
    print("\n" + "="*70)
    print("Syncing HAS_DISTRIBUTION relationships...")
    print("="*70)
    
    with driver.session() as session:
        count = 0
        
        try:
            pg_cur.execute("""
                SELECT po_line_id, distribution_id FROM po_distributions_all
                WHERE distribution_id IS NOT NULL
            """)
            for row in pg_cur.fetchall():
                session.run("""
                    MATCH (pol:POLine {id: $pol_id})
                    MATCH (pod:PODistribution {id: $pod_id})
                    MERGE (pol)-[:HAS_DISTRIBUTION]->(pod)
                """, pol_id=int(row[0]), pod_id=int(row[1]))
                count += 1
            print(f"  HAS_DISTRIBUTION: {count}")
        except:
            print(f"  HAS_DISTRIBUTION: skipped (table empty or not exists)")
        
        return count

def sync_has_shipment_relationships(driver, pg_cur):
    """Sync HAS_SHIPMENT relationships (POLine -> POShipment)"""
    print("\n" + "="*70)
    print("Syncing HAS_SHIPMENT relationships...")
    print("="*70)
    
    with driver.session() as session:
        count = 0
        
        try:
            pg_cur.execute("""
                SELECT po_line_id, shipment_id FROM po_shipments_all
                WHERE shipment_id IS NOT NULL
            """)
            for row in pg_cur.fetchall():
                session.run("""
                    MATCH (pol:POLine {id: $pol_id})
                    MATCH (pos:POShipment {id: $pos_id})
                    MERGE (pol)-[:HAS_SHIPMENT]->(pos)
                """, pol_id=int(row[0]), pos_id=int(row[1]))
                count += 1
            print(f"  HAS_SHIPMENT: {count}")
        except:
            print(f"  HAS_SHIPMENT: skipped (table empty or not exists)")
        
        return count

def verify_relationships(driver):
    """Verify all relationships"""
    print("\n" + "="*70)
    print("Verifying all relationships...")
    print("="*70)
    
    with driver.session() as session:
        result = session.run("""
            MATCH ()-[r]->() 
            RETURN type(r) as type, count(*) as count 
            ORDER BY count DESC
        """)
        
        print("\nRelationship Summary:")
        print("-" * 50)
        total = 0
        for record in result:
            rel_type = record['type']
            count = record['count']
            total += count
            print(f"  {rel_type:30s}: {count:5d}")
        
        print("-" * 50)
        print(f"  {'TOTAL':30s}: {total:5d}")
        
        return total

def main():
    print("="*70)
    print("Implicit Relationship Sync to Neo4j")
    print("="*70)
    
    pg_conn = get_pg_connection()
    pg_cur = pg_conn.cursor()
    driver = get_neo4j_driver()
    
    try:
        # Sync all implicit relationships
        sync_created_by_relationships(driver, pg_cur)
        sync_uses_currency_relationships(driver, pg_cur)
        sync_matches_po_line_relationships(driver, pg_cur)
        sync_has_payment_relationships(driver, pg_cur)
        sync_has_distribution_relationships(driver, pg_cur)
        sync_has_shipment_relationships(driver, pg_cur)
        
        # Verify
        verify_relationships(driver)
        
        print("\n" + "="*70)
        print("OK Implicit relationship sync completed!")
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
