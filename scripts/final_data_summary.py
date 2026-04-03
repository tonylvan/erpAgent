# -*- coding: utf-8 -*-
"""
Final Data Summary Report
"""

import psycopg2

DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'database': 'erp',
    'user': 'postgres',
    'password': 'postgres'
}

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

print("="*70)
print("PostgreSQL ERP Database - Final Data Summary")
print("="*70)

tables = {
    # Supplier Module
    'ap_suppliers': 'Suppliers',
    'ap_supplier_sites': 'Supplier Sites',
    'ap_supplier_contacts': 'Supplier Contacts',
    'ap_bank_accounts': 'Bank Accounts',
    
    # Purchase Order Module
    'po_headers_all': 'Purchase Orders',
    'po_lines_all': 'PO Lines',
    'po_distributions_all': 'PO Distributions',
    'po_shipments_all': 'PO Shipments',
    
    # Accounts Payable
    'ap_invoices_all': 'Invoices',
    'ap_invoice_lines_all': 'Invoice Lines',
    'ap_payments_all': 'Payments',
    'ap_invoice_payments_all': 'Invoice Payments',
    'ap_payment_schedules_all': 'Payment Schedules',
    
    # Accounts Receivable
    'ar_customers': 'Customers',
    'ar_transactions_all': 'AR Transactions',
    'ar_transaction_lines_all': 'AR Lines',
    'ar_cash_receipts_all': 'Cash Receipts',
    
    # Sales Orders
    'so_headers_all': 'Sales Orders',
    'so_lines_all': 'SO Lines',
    
    # Inventory
    'mtl_system_items_b': 'Inventory Items',
    'mtl_material_transactions': 'Inventory Transactions',
    
    # General Ledger
    'gl_ledgers': 'GL Ledgers',
    'gl_periods': 'GL Periods',
    'gl_accounts': 'GL Accounts',
    'gl_je_batches': 'GL Batches',
    'gl_je_headers': 'GL Journals',
    'gl_je_lines': 'GL Journal Lines',
    'gl_balances': 'GL Balances',
    
    # Human Resources
    'employees': 'Employees',
    'per_all_people_f': 'HR Employees',
    
    # Master Data
    'currencies': 'Currencies',
}

print("\nModule: Supplier Management (AP)")
print("-" * 50)
for table, name in tables.items():
    if 'supplier' in table.lower() or 'bank' in table.lower():
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"  {name:30s}: {count:5d}")
        except:
            pass

print("\nModule: Procurement (PO)")
print("-" * 50)
for table, name in tables.items():
    if 'po_' in table.lower():
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"  {name:30s}: {count:5d}")
        except:
            pass

print("\nModule: Accounts Payable (AP)")
print("-" * 50)
for table, name in tables.items():
    if 'invoice' in table.lower() or 'payment' in table.lower():
        if 'ap_' in table.lower():
            try:
                cur.execute(f"SELECT COUNT(*) FROM {table}")
                count = cur.fetchone()[0]
                print(f"  {name:30s}: {count:5d}")
            except:
                pass

print("\nModule: Accounts Receivable (AR)")
print("-" * 50)
for table, name in tables.items():
    if 'ar_' in table.lower() or 'customer' in table.lower():
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"  {name:30s}: {count:5d}")
        except:
            pass

print("\nModule: Sales & Inventory")
print("-" * 50)
for table, name in tables.items():
    if 'so_' in table.lower() or 'mtl_' in table.lower():
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"  {name:30s}: {count:5d}")
        except:
            pass

print("\nModule: General Ledger (GL)")
print("-" * 50)
for table, name in tables.items():
    if 'gl_' in table.lower():
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"  {name:30s}: {count:5d}")
        except:
            pass

print("\nModule: Human Resources")
print("-" * 50)
for table, name in tables.items():
    if 'employee' in table.lower() or 'per_' in table.lower():
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"  {name:30s}: {count:5d}")
        except:
            pass

print("\nMaster Data")
print("-" * 50)
try:
    cur.execute("SELECT COUNT(*) FROM currencies")
    print(f"  {'Currencies':30s}: {cur.fetchone()[0]:5d}")
except:
    pass

# Total
print("\n" + "="*70)
print("Grand Total")
print("="*70)
total = 0
for table in tables.keys():
    try:
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        total += cur.fetchone()[0]
    except:
        pass

print(f"\n  Total Records: {total:,}")

cur.close()
conn.close()

print("\n" + "="*70)
