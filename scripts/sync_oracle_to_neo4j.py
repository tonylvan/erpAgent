# -*- coding: utf-8 -*-
"""
Sync Oracle EBS data from PostgreSQL to Neo4j
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
    return psycopg2.connect(**PG_CONFIG)

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

def sync_inventory(driver, pg_cur):
    """Sync inventory data"""
    print("Syncing inventory...")
    
    with driver.session() as session:
        # MtlSystemItems
        pg_cur.execute("SELECT * FROM mtl_system_items_b")
        for row in pg_cur.fetchall():
            session.run("""
                MERGE (item:InventoryItem {id: $id})
                SET item.organizationId = $org_id,
                    item.segment1 = $segment1,
                    item.description = $description,
                    item.statusCode = $status,
                    item.uomCode = $uom,
                    item.createdDate = $created
            """, id=int(row[0]), org_id=int(row[1]) if row[1] else None,
                segment1=row[2], description=row[3], status=row[4],
                uom=row[5], created=row[6])
        
        # Inventory Locations
        pg_cur.execute("SELECT * FROM mtl_item_locations")
        for row in pg_cur.fetchall():
            session.run("""
                MERGE (loc:InventoryLocation {id: $id})
                SET loc.organizationId = $org_id,
                    loc.subinventory = $subinv,
                    loc.maxUnits = $max_units,
                    loc.x = $x, loc.y = $y, loc.z = $z
            """, id=int(row[0]), org_id=int(row[1]) if row[1] else None,
                subinv=row[2], max_units=row[3], x=row[4], y=row[5], z=row[6])
        
        # Material Transactions
        pg_cur.execute("SELECT * FROM mtl_material_transactions")
        for row in pg_cur.fetchall():
            session.run("""
                MERGE (txn:MaterialTransaction {id: $id})
                SET txn.typeId = $type_id,
                    txn.transactionDate = $txn_date,
                    txn.organizationId = $org_id,
                    txn.inventoryItemId = $item_id,
                    txn.quantity = $qty,
                    txn.reference = $ref
            """, id=int(row[0]), type_id=int(row[1]) if row[1] else None,
                txn_date=row[2], org_id=int(row[3]) if row[3] else None,
                item_id=int(row[4]) if row[4] else None, qty=row[5], ref=row[7])
        
        # Create relationships
        session.run("""
            MATCH (item:InventoryItem), (loc:InventoryLocation)
            WHERE item.organizationId = loc.organizationId
            MERGE (item)-[:STORED_IN]->(loc)
        """)
        
        session.run("""
            MATCH (txn:MaterialTransaction), (item:InventoryItem)
            WHERE txn.inventoryItemId = item.id
            MERGE (txn)-[:INVOLVES_ITEM]->(item)
        """)

def sync_sales_orders(driver, pg_cur):
    """Sync sales order data"""
    print("Syncing sales orders...")
    
    with driver.session() as session:
        # Sales Orders
        pg_cur.execute("SELECT * FROM so_headers_all")
        for row in pg_cur.fetchall():
            session.run("""
                MERGE (so:SalesOrder {id: $id})
                SET so.orderNumber = $order_num,
                    so.orderTypeId = $type_id,
                    so.customerId = $cust_id,
                    so.orderDate = $order_date,
                    so.statusCode = $status,
                    so.salesRepId = $rep_id
            """, id=int(row[0]), order_num=row[1], type_id=int(row[2]) if row[2] else None,
                cust_id=int(row[3]) if row[3] else None, order_date=row[4],
                status=row[5], rep_id=int(row[6]) if row[6] else None)
        
        # Sales Order Lines
        pg_cur.execute("SELECT * FROM so_lines_all")
        for row in pg_cur.fetchall():
            session.run("""
                MERGE (line:SalesOrderLine {id: $id})
                SET line.headerId = $header_id,
                    line.lineNumber = $line_num,
                    line.inventoryItemId = $item_id,
                    line.quantity = $qty,
                    line.unitPrice = $price,
                    line.statusCode = $status
            """, id=int(row[0]), header_id=int(row[1]) if row[1] else None,
                line_num=convert_value(row[2]), item_id=int(row[3]) if row[3] else None,
                qty=convert_value(row[4]), price=convert_value(row[5]), status=row[6])
        
        # Create relationships
        session.run("""
            MATCH (so:SalesOrder), (line:SalesOrderLine)
            WHERE line.headerId = so.id
            MERGE (so)-[:HAS_LINE]->(line)
        """)
        
        session.run("""
            MATCH (line:SalesOrderLine), (item:InventoryItem)
            WHERE line.inventoryItemId = item.id
            MERGE (line)-[:ORDERS_ITEM]->(item)
        """)

def sync_employees(driver, pg_cur):
    """Sync employee data"""
    print("Syncing employees...")
    
    with driver.session() as session:
        pg_cur.execute("SELECT * FROM per_all_people_f")
        for row in pg_cur.fetchall():
            session.run("""
                MERGE (emp:Employee {id: $id})
                SET emp.employeeNumber = $emp_num,
                    emp.fullName = $full_name,
                    emp.firstName = $first_name,
                    emp.lastName = $last_name,
                    emp.email = $email,
                    emp.phone = $phone,
                    emp.hireDate = $hire_date
            """, id=int(row[0]), emp_num=row[1], full_name=row[2],
                first_name=row[3], last_name=row[4], email=row[6],
                phone=row[7], hire_date=row[8])

def sync_fixed_assets(driver, pg_cur):
    """Sync fixed assets data"""
    print("Syncing fixed assets...")
    
    with driver.session() as session:
        pg_cur.execute("SELECT * FROM fa_additions_b")
        for row in pg_cur.fetchall():
            session.run("""
                MERGE (asset:FixedAsset {id: $id})
                SET asset.assetNumber = $asset_num,
                    asset.assetType = $asset_type,
                    asset.categoryId = $cat_id,
                    asset.bookType = $book_type,
                    asset.inServiceDate = $in_service,
                    asset.cost = $cost,
                    asset.deprMethod = $depr_method,
                    asset.lifeMonths = $life
            """, id=int(row[0]), asset_num=row[1], asset_type=row[2],
                cat_id=int(row[3]) if row[3] else None, book_type=row[4],
                in_service=row[5], cost=convert_value(row[6]), depr_method=row[7], life=int(row[8]) if row[8] else None)

def sync_bank_accounts(driver, pg_cur):
    """Sync bank accounts data"""
    print("Syncing bank accounts...")
    
    with driver.session() as session:
        pg_cur.execute("SELECT * FROM ce_bank_accounts")
        for row in pg_cur.fetchall():
            session.run("""
                MERGE (bank:BankAccount {id: $id})
                SET bank.accountName = $name,
                    bank.accountNum = $num,
                    bank.bankId = $bank_id,
                    bank.branchId = $branch_id,
                    bank.currencyCode = $currency,
                    bank.accountType = $type
            """, id=int(row[0]), name=row[1], num=row[2],
                bank_id=int(row[3]) if row[3] else None,
                branch_id=int(row[4]) if row[4] else None,
                currency=row[5], type=row[6])

def main():
    print("Starting Oracle EBS sync to Neo4j...")
    
    pg_conn = get_pg_connection()
    pg_cur = pg_conn.cursor()
    driver = get_neo4j_driver()
    
    try:
        sync_inventory(driver, pg_cur)
        sync_sales_orders(driver, pg_cur)
        sync_employees(driver, pg_cur)
        sync_fixed_assets(driver, pg_cur)
        sync_bank_accounts(driver, pg_cur)
        
        print("Sync completed successfully!")
        
    finally:
        pg_cur.close()
        pg_conn.close()
        driver.close()

if __name__ == '__main__':
    main()
