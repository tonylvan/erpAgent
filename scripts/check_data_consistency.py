# -*- coding: utf-8 -*-
"""
Check Data Consistency between PostgreSQL and Neo4j
"""

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

# Mapping between PG tables and Neo4j labels
MAPPING = {
    'ap_suppliers': 'Supplier',
    'po_headers_all': 'PurchaseOrder',
    'po_lines_all': 'POLine',
    'ap_invoices_all': 'Invoice',
    'ap_invoice_lines_all': 'InvoiceLine',
    'so_headers_all': 'SalesOrder',
    'so_lines_all': 'SalesOrderLine',
    'mtl_system_items_b': 'InventoryItem',
    'ar_customers': 'Customer',
    'employees': 'Employee',
    'ap_supplier_sites': 'SupplierSite',
    'ap_supplier_contacts': 'SupplierContact',
    'ap_bank_accounts': 'BankAccount',
    'ap_payments_all': 'Payment',
    'po_distributions_all': 'PODistribution',
    'po_shipments_all': 'POShipment',
    'gl_ledgers': 'GLLedger',
    'gl_accounts': 'GLAccount',
    'currencies': 'Currency',
    'gl_je_headers': 'GLJournal',
}

def get_pg_counts():
    """Get counts from PostgreSQL"""
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()
    
    counts = {}
    for table in MAPPING.keys():
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            counts[table] = count
        except Exception as e:
            counts[table] = f"Error: {e}"
    
    cur.close()
    conn.close()
    return counts

def get_neo4j_counts():
    """Get counts from Neo4j"""
    driver = GraphDatabase.driver(**NEO4J_CONFIG)
    
    counts = {}
    with driver.session() as session:
        for label in MAPPING.values():
            try:
                result = session.run(f"MATCH (n:{label}) RETURN count(n) as count")
                count = result.single()['count']
                counts[label] = count
            except Exception as e:
                counts[label] = f"Error: {e}"
    
    driver.close()
    return counts

def check_consistency():
    """Check data consistency"""
    print("="*70)
    print("PostgreSQL vs Neo4j Data Consistency Check")
    print("="*70)
    
    pg_counts = get_pg_counts()
    neo4j_counts = get_neo4j_counts()
    
    print("\n| PostgreSQL Table | Neo4j Label | PG Count | Neo4j Count | Status |")
    print("|-----------------|-------------|----------|-------------|--------|")
    
    consistent = 0
    inconsistent = 0
    errors = 0
    
    for pg_table, neo4j_label in MAPPING.items():
        pg_count = pg_counts.get(pg_table, 0)
        neo4j_count = neo4j_counts.get(neo4j_label, 0)
        
        if isinstance(pg_count, str) or isinstance(neo4j_count, str):
            status = "ERROR"
            errors += 1
        elif pg_count == neo4j_count:
            status = "OK"
            consistent += 1
        else:
            status = "DIFF"
            inconsistent += 1
        
        print(f"| {pg_table:25s} | {neo4j_label:20s} | {pg_count:8d} | {neo4j_count:11d} | {status:6s} |")
    
    print("\nSummary:")
    print(f"  OK Consistent: {consistent} ({consistent*100/(consistent+inconsistent):.1f}%)")
    print(f"  DIFF Inconsistent: {inconsistent} ({inconsistent*100/(consistent+inconsistent):.1f}%)")
    print(f"  ERROR Errors: {errors}")
    print("="*70)
    
    if inconsistent > 0:
        print("\nDIFF Inconsistent Tables:")
        for pg_table, neo4j_label in MAPPING.items():
            pg_count = pg_counts.get(pg_table, 0)
            neo4j_count = neo4j_counts.get(neo4j_label, 0)
            if isinstance(pg_count, int) and isinstance(neo4j_count, int) and pg_count != neo4j_count:
                diff = neo4j_count - pg_count
                sign = "+" if diff > 0 else ""
                print(f"  {pg_table} -> {neo4j_label}: {sign}{diff} ({sign}{diff*100/pg_count:.1f}%)")

if __name__ == '__main__':
    check_consistency()
