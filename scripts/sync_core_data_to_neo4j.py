# -*- coding: utf-8 -*-
"""
Sync Missing Core Data to Neo4j
Priority: PODistribution, POShipment, Employee
"""

from decimal import Decimal
import psycopg2
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
    'auth': ('neo4j', 'Tony1985')
}

def get_pg_connection():
    return psycopg2.connect(**PG_CONFIG)

def get_neo4j_driver():
    return GraphDatabase.driver(**NEO4J_CONFIG)

def convert_decimal(val):
    """Convert Decimal to float for Neo4j compatibility"""
    if val is None:
        return None
    if isinstance(val, Decimal):
        return float(val)
    return val

def sync_podistribution_to_neo4j(driver, pg_cur):
    """Sync PODistribution nodes and HAS_DISTRIBUTION relationships"""
    print("="*70)
    print("Syncing PODistribution to Neo4j...")
    print("="*70)
    
    with driver.session() as session:
        # Get PODistributions from PostgreSQL
        pg_cur.execute("""
            SELECT distribution_id, po_line_id, po_header_id, 
                   distribution_num, quantity_ordered, amount_ordered
            FROM po_distributions_all
        """)
        distributions = pg_cur.fetchall()
        
        count = 0
        for dist in distributions:
            dist_id, po_line_id, po_header_id, dist_num, qty, amount = dist
            
            # Create PODistribution node
            session.run("""
                MERGE (pod:PODistribution {id: $dist_id})
                SET pod.poLineId = $po_line_id,
                    pod.poHeaderId = $po_header_id,
                    pod.distributionNum = $dist_num,
                    pod.quantityOrdered = $qty,
                    pod.amountOrdered = $amount
            """, dist_id=int(dist_id), po_line_id=int(po_line_id), po_header_id=int(po_header_id),
                dist_num=convert_decimal(dist_num), qty=convert_decimal(qty), amount=convert_decimal(amount))
            
            # Create HAS_DISTRIBUTION relationship
            session.run("""
                MATCH (pol:POLine {id: $po_line_id})
                MATCH (pod:PODistribution {id: $dist_id})
                MERGE (pol)-[:HAS_DISTRIBUTION]->(pod)
            """, po_line_id=int(po_line_id), dist_id=int(dist_id))
            
            count += 1
            if count % 500 == 0:
                print(f"  Processed {count}/{len(distributions)}...")
        
        print(f"  OK Synced {count} PODistribution nodes")
        print(f"  OK Created {count} HAS_DISTRIBUTION relationships")
        return count

def sync_poshipment_to_neo4j(driver, pg_cur):
    """Sync POShipment nodes and HAS_SHIPMENT relationships"""
    print("\n" + "="*70)
    print("Syncing POShipment to Neo4j...")
    print("="*70)
    
    with driver.session() as session:
        # Get POShipments from PostgreSQL
        pg_cur.execute("""
            SELECT shipment_id, po_line_id, po_header_id, 
                   shipment_num, quantity, need_by_date
            FROM po_shipments_all
        """)
        shipments = pg_cur.fetchall()
        
        count = 0
        for ship in shipments:
            ship_id, po_line_id, po_header_id, ship_num, qty, need_date = ship
            
            # Create POShipment node
            session.run("""
                MERGE (pos:POShipment {id: $ship_id})
                SET pos.poLineId = $po_line_id,
                    pos.poHeaderId = $po_header_id,
                    pos.shipmentNum = $ship_num,
                    pos.quantity = $qty,
                    pos.needByDate = $need_date
            """, ship_id=int(ship_id), po_line_id=int(po_line_id), po_header_id=int(po_header_id),
                ship_num=int(ship_num), qty=convert_decimal(qty), need_date=need_date)
            
            # Create HAS_SHIPMENT relationship
            session.run("""
                MATCH (pol:POLine {id: $po_line_id})
                MATCH (pos:POShipment {id: $ship_id})
                MERGE (pol)-[:HAS_SHIPMENT]->(pos)
            """, po_line_id=int(po_line_id), ship_id=int(ship_id))
            
            count += 1
            if count % 500 == 0:
                print(f"  Processed {count}/{len(shipments)}...")
        
        print(f"  OK Synced {count} POShipment nodes")
        print(f"  OK Created {count} HAS_SHIPMENT relationships")
        return count

def sync_remaining_employees(driver, pg_cur):
    """Sync remaining Employee nodes"""
    print("\n" + "="*70)
    print("Syncing remaining Employees to Neo4j...")
    print("="*70)
    
    with driver.session() as session:
        # Get all employees from PostgreSQL
        pg_cur.execute("""
            SELECT employee_id, employee_name, department
            FROM employees
        """)
        employees = pg_cur.fetchall()
        
        count = 0
        for emp in employees:
            emp_id, emp_name, dept = emp
            
            # Create Employee node
            session.run("""
                MERGE (emp:Employee {id: $emp_id})
                SET emp.name = $emp_name,
                    emp.department = $dept
            """, emp_id=emp_id, emp_name=emp_name, dept=dept)
            
            count += 1
            if count % 100 == 0:
                print(f"  Processed {count}/{len(employees)}...")
        
        print(f"  OK Synced {count} Employee nodes")
        return count

def sync_employee_relationships(driver, pg_cur):
    """Sync CREATED_BY relationships for all entities"""
    print("\n" + "="*70)
    print("Syncing Employee CREATED_BY relationships...")
    print("="*70)
    
    with driver.session() as session:
        count = 0
        
        # PO created_by
        pg_cur.execute("""
            SELECT po_header_id, created_by 
            FROM po_headers_all 
            WHERE created_by IS NOT NULL
        """)
        for row in pg_cur.fetchall():
            session.run("""
                MATCH (po:PurchaseOrder {id: $po_id})
                MATCH (emp:Employee {id: $emp_id})
                MERGE (po)-[:CREATED_BY]->(emp)
            """, po_id=row[0], emp_id=row[1])
            count += 1
        print(f"  PO CREATED_BY: {count}")
        
        # Invoice created_by
        count_inv = 0
        pg_cur.execute("""
            SELECT invoice_id, created_by 
            FROM ap_invoices_all 
            WHERE created_by IS NOT NULL
        """)
        for row in pg_cur.fetchall():
            session.run("""
                MATCH (inv:Invoice {id: $inv_id})
                MATCH (emp:Employee {id: $emp_id})
                MERGE (inv)-[:CREATED_BY]->(emp)
            """, inv_id=row[0], emp_id=row[1])
            count_inv += 1
        print(f"  Invoice CREATED_BY: {count_inv}")
        count += count_inv
        
        return count

def verify_sync(driver):
    """Verify sync results"""
    print("\n" + "="*70)
    print("Verifying Sync Results...")
    print("="*70)
    
    with driver.session() as session:
        # Count new nodes
        result = session.run("""
            MATCH (n)
            WHERE labels(n)[0] IN ['PODistribution', 'POShipment', 'Employee']
            RETURN labels(n)[0] as label, count(n) as count
            ORDER BY label
        """)
        
        print("\nNew Node Counts:")
        print("-" * 50)
        for record in result:
            print(f"  {record['label']:25s}: {record['count']}")
        
        # Count new relationships
        result = session.run("""
            MATCH ()-[r]->()
            WHERE type(r) IN ['HAS_DISTRIBUTION', 'HAS_SHIPMENT', 'CREATED_BY']
            RETURN type(r) as type, count(r) as count
            ORDER BY type
        """)
        
        print("\nNew Relationship Counts:")
        print("-" * 50)
        for record in result:
            print(f"  {record['type']:25s}: {record['count']}")

def main():
    print("="*70)
    print("Sync Missing Core Data to Neo4j")
    print("="*70)
    
    pg_conn = get_pg_connection()
    pg_cur = pg_conn.cursor()
    driver = get_neo4j_driver()
    
    try:
        # Sync PODistribution
        pod_count = sync_podistribution_to_neo4j(driver, pg_cur)
        
        # Sync POShipment
        pos_count = sync_poshipment_to_neo4j(driver, pg_cur)
        
        # Sync remaining Employees
        emp_count = sync_remaining_employees(driver, pg_cur)
        
        # Sync Employee relationships
        rel_count = sync_employee_relationships(driver, pg_cur)
        
        # Verify
        verify_sync(driver)
        
        print("\n" + "="*70)
        print("OK Sync completed successfully!")
        print("="*70)
        print(f"\nSummary:")
        print(f"  PODistribution: {pod_count} nodes + relationships")
        print(f"  POShipment: {pos_count} nodes + relationships")
        print(f"  Employee: {emp_count} nodes")
        print(f"  CREATED_BY: {rel_count} relationships")
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
