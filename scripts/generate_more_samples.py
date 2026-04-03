# -*- coding: utf-8 -*-
"""
Generate More Sample Data for PostgreSQL
Focus on missing tables and relationships
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

def generate_po_distributions(count=300):
    """Generate PO Distribution data"""
    print("\n[1/6] Generating PO Distributions...")
    conn = get_connection()
    cur = conn.cursor()
    
    # Get existing PO lines
    cur.execute("SELECT po_line_id, po_header_id FROM po_lines_all")
    po_lines = cur.fetchall()
    
    distributions = []
    dist_id = 1
    
    cur.execute("SELECT MAX(distribution_id) FROM po_distributions_all")
    max_id = cur.fetchone()[0]
    if max_id:
        dist_id = max_id + 1
    
    for po_line_id, po_header_id in po_lines:
        # Create 1-2 distributions per line
        for _ in range(random.randint(1, 2)):
            distributions.append((
                dist_id,
                po_line_id,
                po_header_id,
                random.randint(1, 10),  # distribution_num
                random.randint(1, 100),  # quantity_ordered
                round(random.uniform(100, 5000), 2)  # amount_ordered
            ))
            dist_id += 1
            
            if len(distributions) >= count:
                break
        
        if len(distributions) >= count:
            break
    
    if distributions:
        execute_batch(cur, """
            INSERT INTO po_distributions_all 
            (distribution_id, po_line_id, po_header_id, distribution_num, quantity_ordered, amount_ordered)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (distribution_id) DO NOTHING
        """, distributions)
        conn.commit()
        print(f"  Generated {len(distributions)} PO distributions")
    else:
        print("  PO distributions already exist")
    
    cur.close()
    conn.close()

def generate_po_shipments(count=200):
    """Generate PO Shipment data"""
    print("\n[2/6] Generating PO Shipments...")
    conn = get_connection()
    cur = conn.cursor()
    
    # Get existing PO lines
    cur.execute("SELECT po_line_id, po_header_id FROM po_lines_all")
    po_lines = cur.fetchall()
    
    shipments = []
    ship_id = 1
    
    cur.execute("SELECT MAX(shipment_id) FROM po_shipments_all")
    max_id = cur.fetchone()[0]
    if max_id:
        ship_id = max_id + 1
    
    for po_line_id, po_header_id in po_lines:
        # Create 1 shipment per line
        need_by_date = datetime.now() + timedelta(days=random.randint(10, 90))
        shipments.append((
            ship_id,
            po_line_id,
            po_header_id,
            random.randint(1, 5),  # shipment_num
            random.randint(1, 100),  # quantity
            need_by_date
        ))
        ship_id += 1
        
        if len(shipments) >= count:
            break
    
    if shipments:
        execute_batch(cur, """
            INSERT INTO po_shipments_all 
            (shipment_id, po_line_id, po_header_id, shipment_num, quantity, need_by_date)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (shipment_id) DO NOTHING
        """, shipments)
        conn.commit()
        print(f"  Generated {len(shipments)} PO shipments")
    else:
        print("  PO shipments already exist")
    
    cur.close()
    conn.close()

def generate_invoice_payments(count=100):
    """Generate Invoice Payment relationships"""
    print("\n[3/6] Generating Invoice Payments...")
    conn = get_connection()
    cur = conn.cursor()
    
    # Get existing invoices and payments
    cur.execute("SELECT invoice_id, invoice_amount, payment_status FROM ap_invoices_all WHERE payment_status = 'PAID'")
    invoices = cur.fetchall()
    
    cur.execute("SELECT check_id FROM ap_payments_all")
    payments = [row[0] for row in cur.fetchall()]
    
    if not payments:
        print("  No payments available, creating some first...")
        # Create some payments
        payment_id = 1
        cur.execute("SELECT MAX(check_id) FROM ap_payments_all")
        max_id = cur.fetchone()[0]
        if max_id:
            payment_id = max_id + 1
        
        new_payments = []
        for i in range(50):
            new_payments.append((
                payment_id + i,
                f'CHK-{payment_id + i:06d}',
                round(random.uniform(1000, 30000), 2),
                datetime.now() - timedelta(days=random.randint(0, 60)),
                'CLEARED',
                random.randint(1, 50),  # vendor_id
                random.randint(1, 50)   # bank_account_id
            ))
        
        execute_batch(cur, """
            INSERT INTO ap_payments_all (check_id, check_number, amount, check_date, status, vendor_id, bank_account_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (check_id) DO NOTHING
        """, new_payments)
        conn.commit()
        payments = [p[0] for p in new_payments]
    
    # Create invoice payment relationships
    invoice_payments = []
    invoice_payment_id = 1
    
    cur.execute("SELECT MAX(invoice_payment_id) FROM ap_invoice_payments_all")
    max_id = cur.fetchone()[0]
    if max_id:
        invoice_payment_id = max_id + 1
    
    for i, (inv_id, inv_amount, status) in enumerate(invoices[:count]):
        if payments:
            payment_id = payments[i % len(payments)]
            invoice_payments.append((
                invoice_payment_id,
                inv_id,
                payment_id,
                round(float(inv_amount) * random.uniform(0.8, 1.0), 2)  # payment amount
            ))
            invoice_payment_id += 1
    
    if invoice_payments:
        execute_batch(cur, """
            INSERT INTO ap_invoice_payments_all 
            (invoice_payment_id, invoice_id, check_id, amount)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (invoice_payment_id) DO NOTHING
        """, invoice_payments)
        conn.commit()
        print(f"  Generated {len(invoice_payments)} invoice payment relationships")
    else:
        print("  No invoice payments to create")
    
    cur.close()
    conn.close()

def generate_inventory_transactions(count=500):
    """Generate Inventory Transaction data"""
    print("\n[4/6] Generating Inventory Transactions...")
    conn = get_connection()
    cur = conn.cursor()
    
    # Get existing inventory items
    cur.execute("SELECT inventory_item_id FROM mtl_system_items_b")
    items = [row[0] for row in cur.fetchall()]
    
    if not items:
        print("  No inventory items found, skipping...")
        cur.close()
        conn.close()
        return
    
    # Skip if table doesn't exist or is complex
    print("  Skipping inventory transactions (table structure varies)")
    
    cur.close()
    conn.close()

def generate_payment_schedules(count=150):
    """Generate Payment Schedule data"""
    print("\n[5/6] Generating Payment Schedules...")
    conn = get_connection()
    cur = conn.cursor()
    
    # Get existing invoices
    cur.execute("SELECT invoice_id, invoice_amount, due_date FROM ap_invoices_all")
    invoices = cur.fetchall()
    
    schedules = []
    schedule_id = 1
    
    cur.execute("SELECT MAX(schedule_id) FROM ap_payment_schedules_all")
    max_id = cur.fetchone()[0]
    if max_id:
        schedule_id = max_id + 1
    
    for inv_id, inv_amount, due_date in invoices[:count]:
        schedules.append((
            schedule_id,
            inv_id,
            1,  # payment_num
            due_date,
            round(float(inv_amount) * 0.3, 2),  # amount_due
            round(float(inv_amount) * 0.2, 2)   # amount_paid
        ))
        schedule_id += 1
    
    if schedules:
        execute_batch(cur, """
            INSERT INTO ap_payment_schedules_all 
            (schedule_id, invoice_id, payment_num, due_date, amount_due, amount_paid)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (schedule_id) DO NOTHING
        """, schedules)
        conn.commit()
        print(f"  Generated {len(schedules)} payment schedules")
    else:
        print("  No payment schedules to create")
    
    cur.close()
    conn.close()

def generate_ar_cash_receipts(count=80):
    """Generate AR Cash Receipts"""
    print("\n[6/6] Generating AR Cash Receipts...")
    conn = get_connection()
    cur = conn.cursor()
    
    # Get existing customers
    cur.execute("SELECT customer_id FROM ar_customers")
    customers = [row[0] for row in cur.fetchall()]
    
    if not customers:
        print("  No customers found, skipping...")
        cur.close()
        conn.close()
        return
    
    # Skip if table doesn't exist
    try:
        cur.execute("SELECT 1 FROM ar_cash_receipts_all LIMIT 1")
    except:
        print("  ar_cash_receipts_all table not found, skipping...")
        cur.close()
        conn.close()
        return
    
    receipts = []
    receipt_id = 1
    
    cur.execute("SELECT MAX(cash_receipt_id) FROM ar_cash_receipts_all")
    max_id = cur.fetchone()[0]
    if max_id:
        receipt_id = max_id + 1
    
    for _ in range(count):
        cust_id = random.choice(customers)
        receipt_date = datetime.now() - timedelta(days=random.randint(0, 90))
        receipts.append((
            receipt_id,
            f'REC-{receipt_id:06d}',
            cust_id,
            round(random.uniform(500, 20000), 2),
            receipt_date.date(),
            'CLEARED',
            1  # bank_account_id
        ))
        receipt_id += 1
    
    if receipts:
        execute_batch(cur, """
            INSERT INTO ar_cash_receipts_all 
            (cash_receipt_id, receipt_number, customer_id, amount, receipt_date, status, bank_account_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (cash_receipt_id) DO NOTHING
        """, receipts)
        conn.commit()
        print(f"  Generated {len(receipts)} AR cash receipts")
    else:
        print("  No AR cash receipts to create")
    
    cur.close()
    conn.close()

def show_summary():
    """Show data summary"""
    print("\n" + "="*70)
    print("Data Summary")
    print("="*70)
    
    conn = get_connection()
    cur = conn.cursor()
    
    tables = {
        'po_distributions_all': 'PO Distributions',
        'po_shipments_all': 'PO Shipments',
        'ap_invoice_payments_all': 'Invoice Payments',
        'ap_payment_schedules_all': 'Payment Schedules',
        'mtl_material_transactions': 'Inventory Transactions',
        'ar_cash_receipts_all': 'AR Cash Receipts',
        'ap_payments_all': 'Payments',
    }
    
    print("\nNew Data Counts:")
    print("-" * 50)
    for table, name in tables.items():
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"  {name:30s}: {count:5d}")
        except:
            print(f"  {name:30s}: N/A")
    
    print("-" * 50)
    cur.close()
    conn.close()

def main():
    print("="*70)
    print("Generate More Sample Data for PostgreSQL")
    print("="*70)
    
    generate_po_distributions(300)
    generate_po_shipments(200)
    generate_invoice_payments(100)
    generate_inventory_transactions(500)
    generate_payment_schedules(150)
    generate_ar_cash_receipts(80)
    
    show_summary()
    
    print("\n" + "="*70)
    print("OK Sample data generation completed!")
    print("="*70)

if __name__ == '__main__':
    main()
