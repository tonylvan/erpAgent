# -*- coding: utf-8 -*-
"""
Supplement Sample Data Generator
Generates additional data for XLA, GL, AR, HR modules
"""

import psycopg2
from psycopg2.extras import execute_batch
import random
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

DB_CONFIG = {
    'host': 'localhost',
    'port': '5432',
    'database': 'erp',
    'user': 'postgres',
    'password': 'postgres'
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def generate_employees():
    """Generate more employees"""
    print("\n[1/5] Generating employees...")
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("SELECT MAX(employee_id) FROM employees")
    max_id = cur.fetchone()[0] or 1000
    
    employees = []
    for i in range(max_id + 1, max_id + 108):
        employees.append((
            i,
            f'Employee {chr(65 + ((i - max_id) % 26))}',
            random.choice(['IT', 'Finance', 'Sales', 'HR', 'Operations'])
        ))
    
    execute_batch(cur, """
        INSERT INTO employees (employee_id, employee_name, department)
        VALUES (%s, %s, %s)
        ON CONFLICT (employee_id) DO NOTHING
    """, employees)
    
    conn.commit()
    print(f"  Generated {len(employees)} employees")
    cur.close()
    conn.close()

def generate_ar_data():
    """Generate AR customers and transactions"""
    print("\n[2/5] Generating AR data...")
    conn = get_connection()
    cur = conn.cursor()
    
    # Customers
    cur.execute("SELECT MAX(customer_id) FROM ar_customers")
    max_id = cur.fetchone()[0] or 0
    
    if max_id < 20:
        customers = []
        for i in range(max_id + 1, 21):
            customers.append((
                i,
                f'CUST-{i:03d}',
                f'Customer {chr(65+i)} Corp',
                'CORPORATE',
                'ACTIVE',
                random.uniform(50000, 500000)
            ))
        
        execute_batch(cur, """
            INSERT INTO ar_customers (customer_id, customer_number, customer_name, customer_type, status, credit_limit)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (customer_id) DO NOTHING
        """, customers)
        print(f"  Generated {len(customers)} customers")
    
    # AR Transactions
    cur.execute("SELECT MAX(transaction_id) FROM ar_transactions_all")
    max_id = cur.fetchone()[0] or 0
    
    if max_id < 30:
        transactions = []
        txn_lines = []
        line_id = 1
        
        for i in range(max_id + 1, 31):
            cust_id = random.randint(1, 20)
            amount = round(random.uniform(1000, 50000), 2)
            txn_date = datetime.now() - timedelta(days=random.randint(0, 90))
            
            transactions.append((
                i,
                f'TXN-{i:04d}',
                'INVOICE',
                cust_id,
                amount,
                amount,
                'OPEN' if i % 3 != 0 else 'PAID',
                txn_date.date(),
                (txn_date + timedelta(days=30)).date(),
                txn_date,
                random.randint(1001, 1107)
            ))
            
            # 1-3 lines per transaction
            for j in range(random.randint(1, 3)):
                line_amount = round(amount / (j + 1), 2)
                txn_lines.append((
                    line_id,
                    i,
                    j + 1,
                    'REV',
                    line_amount,
                    round(line_amount * 0.13, 2)
                ))
                line_id += 1
        
        execute_batch(cur, """
            INSERT INTO ar_transactions_all (transaction_id, transaction_number, transaction_type, customer_id,
                                             amount, amount_due, status, transaction_date, due_date, creation_date, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (transaction_id) DO NOTHING
        """, transactions)
        
        execute_batch(cur, """
            INSERT INTO ar_transaction_lines_all (line_id, transaction_id, line_number, line_type, amount, tax_amount)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (line_id) DO NOTHING
        """, txn_lines)
        
        print(f"  Generated {len(transactions)} transactions, {len(txn_lines)} lines")
    
    cur.close()
    conn.close()

def generate_gl_data():
    """Generate GL data"""
    print("\n[3/5] Generating GL data...")
    conn = get_connection()
    cur = conn.cursor()
    
    # GL Ledgers
    ledgers = [
        (1, 'Primary Ledger', 1, 'CNY', 'Monthly', 'Primary'),
        (2, 'Secondary Ledger', 1, 'USD', 'Monthly', 'Secondary')
    ]
    execute_batch(cur, """
        INSERT INTO gl_ledgers (ledger_id, ledger_name, chart_of_accounts_id, currency_code, period_set_name, ledger_type)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (ledger_id) DO NOTHING
    """, ledgers)
    print("  Generated 2 ledgers")
    
    # GL Accounts
    accounts = [
        (1, '1001', '0', '0', '0', 'Y'),
        (2, '1002', '0', '0', '0', 'Y'),
        (3, '1122', '0', '0', '0', 'Y'),
        (4, '1401', '0', '0', '0', 'Y'),
        (5, '2202', '0', '0', '0', 'Y'),
        (6, '6001', '0', '0', '0', 'Y'),
        (7, '6401', '0', '0', '0', 'Y'),
    ]
    execute_batch(cur, """
        INSERT INTO gl_accounts (account_id, segment1, segment2, segment3, segment4, enabled_flag)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (account_id) DO NOTHING
    """, accounts)
    print("  Generated 7 accounts")
    
    # GL Journals
    # First create batches
    batches = []
    for i in range(1, 6):
        batches.append((
            i,
            f'BATCH-{i:04d}',
            1,
            f'2026-{i:02d}',
            'POSTED',
            random.uniform(10000, 100000),
            random.uniform(10000, 100000)
        ))
    
    execute_batch(cur, """
        INSERT INTO gl_je_batches (batch_id, batch_name, ledger_id, period_name, status, total_dr, total_cr)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (batch_id) DO NOTHING
    """, batches)
    print(f"  Generated {len(batches)} batches")
    
    cur.execute("SELECT MAX(je_header_id) FROM gl_je_headers")
    max_id = cur.fetchone()[0] or 0
    
    if max_id < 20:
        journals = []
        journal_lines = []
        line_id = 1
        
        for i in range(max_id + 1, 21):
            batch_id = ((i - 1) % 5) + 1
            amount = round(random.uniform(5000, 50000), 2)
            
            journals.append((
                i,
                batch_id,
                f'JE-{i:04d}',
                1,
                f'2026-{((i-1) % 12) + 1:02d}',
                'CNY',
                'POSTED',
                (datetime.now() - timedelta(days=random.randint(0, 90))).date(),
                (datetime.now() - timedelta(days=random.randint(0, 60))).date()
            ))
            
            # Dr/Cr lines
            journal_lines.append((
                line_id,
                i,
                1,
                random.randint(1, 7),
                f'SEG3-{i}',
                amount,
                0,
                amount,
                0
            ))
            line_id += 1
            
            journal_lines.append((
                line_id,
                i,
                2,
                random.randint(1, 7),
                f'SEG3-{i}',
                0,
                amount,
                0,
                amount
            ))
            line_id += 1
        
        execute_batch(cur, """
            INSERT INTO gl_je_headers (je_header_id, je_batch_id, je_name, ledger_id, period_name,
                                       currency_code, status, effective_date, posted_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (je_header_id) DO NOTHING
        """, journals)
        
        execute_batch(cur, """
            INSERT INTO gl_je_lines (je_line_id, je_header_id, line_num, code_combination_id, segment3,
                                     entered_dr, entered_cr, accounted_dr, accounted_cr)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (je_line_id) DO NOTHING
        """, journal_lines)
        
        print(f"  Generated {len(journals)} journals, {len(journal_lines)} lines")
    
    cur.close()
    conn.close()

def update_existing_data():
    """Update existing data with more realistic values"""
    print("\n[4/5] Updating existing data...")
    conn = get_connection()
    cur = conn.cursor()
    
    # Update PO amounts to match line totals
    cur.execute("""
        UPDATE po_headers_all po
        SET amount = (
            SELECT COALESCE(SUM(amount), 0)
            FROM po_lines_all pol
            WHERE pol.po_header_id = po.po_header_id
        )
        WHERE po_header_id IN (
            SELECT DISTINCT po_header_id FROM po_lines_all
        )
    """)
    updated = cur.rowcount
    print(f"  Updated {updated} PO amounts")
    
    # Update Invoice amounts to match line totals
    cur.execute("""
        UPDATE ap_invoices_all inv
        SET invoice_amount = (
            SELECT COALESCE(SUM(amount), 0)
            FROM ap_invoice_lines_all inl
            WHERE inl.invoice_id = inv.invoice_id
        )
        WHERE invoice_id IN (
            SELECT DISTINCT invoice_id FROM ap_invoice_lines_all
        )
    """)
    updated = cur.rowcount
    print(f"  Updated {updated} Invoice amounts")
    
    conn.commit()
    cur.close()
    conn.close()

def show_summary():
    """Show data summary"""
    print("\n[5/5] Data Summary")
    conn = get_connection()
    cur = conn.cursor()
    
    tables = [
        ('employees', 'Employees'),
        ('ap_suppliers', 'Suppliers'),
        ('ap_supplier_sites', 'Supplier Sites'),
        ('ap_supplier_contacts', 'Supplier Contacts'),
        ('ap_bank_accounts', 'Bank Accounts'),
        ('po_headers_all', 'Purchase Orders'),
        ('po_lines_all', 'PO Lines'),
        ('ap_invoices_all', 'Invoices'),
        ('ap_invoice_lines_all', 'Invoice Lines'),
        ('ar_customers', 'Customers'),
        ('ar_transactions_all', 'AR Transactions'),
        ('ar_transaction_lines_all', 'AR Lines'),
        ('gl_ledgers', 'GL Ledgers'),
        ('gl_accounts', 'GL Accounts'),
        ('gl_je_headers', 'GL Journals'),
        ('gl_je_lines', 'GL Journal Lines'),
    ]
    
    print("\n  Table Record Counts:")
    print("  " + "-" * 50)
    for table, name in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"  {name:25s}: {count:5d}")
        except:
            print(f"  {name:25s}: N/A")
    
    print("  " + "-" * 50)
    cur.close()
    conn.close()

def main():
    print("="*70)
    print("Supplement Sample Data Generator")
    print("="*70)
    
    generate_employees()
    generate_ar_data()
    generate_gl_data()
    update_existing_data()
    show_summary()
    
    print("\n" + "="*70)
    print("OK All data generated successfully!")
    print("="*70)

if __name__ == '__main__':
    main()
