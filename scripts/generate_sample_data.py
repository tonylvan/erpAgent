# -*- coding: utf-8 -*-
"""
ERP Sample Data Generator for PostgreSQL
Generates sample data based on Oracle EBS table structures from ETRM
"""

import psycopg2
from psycopg2.extras import execute_batch
import random
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

# PostgreSQL connection config
DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'erp')
DB_USER = os.getenv('POSTGRES_USER', 'postgres')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')

class SampleDataGenerator:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        self.conn.autocommit = False
        self.cursor = self.conn.cursor()
    
    def close(self):
        self.cursor.close()
        self.conn.close()
    
    def create_tables(self):
        """Create tables based on Oracle EBS structure"""
        print("[INFO] Creating tables...")
        
        tables = [
            # Supplier tables (AP module)
            """
            CREATE TABLE IF NOT EXISTS ap_suppliers (
                vendor_id BIGINT PRIMARY KEY,
                segment1 VARCHAR(30) UNIQUE,
                vendor_name VARCHAR(240),
                vendor_type_lookup_code VARCHAR(25),
                status VARCHAR(20),
                invoice_currency_code VARCHAR(15),
                creation_date TIMESTAMP,
                created_by BIGINT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS ap_supplier_sites (
                vendor_site_id BIGINT PRIMARY KEY,
                vendor_id BIGINT REFERENCES ap_suppliers(vendor_id),
                vendor_site_code VARCHAR(50),
                address_line1 VARCHAR(240),
                city VARCHAR(80),
                country VARCHAR(80)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS ap_supplier_contacts (
                vendor_contact_id BIGINT PRIMARY KEY,
                vendor_id BIGINT REFERENCES ap_suppliers(vendor_id),
                first_name VARCHAR(50),
                last_name VARCHAR(80),
                email VARCHAR(200)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS ap_bank_accounts (
                bank_account_id BIGINT PRIMARY KEY,
                vendor_id BIGINT REFERENCES ap_suppliers(vendor_id),
                account_num VARCHAR(50),
                bank_name VARCHAR(100),
                currency_code VARCHAR(15)
            )
            """,
            
            # Purchase Order tables (PO module)
            """
            CREATE TABLE IF NOT EXISTS po_headers_all (
                po_header_id BIGINT PRIMARY KEY,
                segment1 VARCHAR(30) UNIQUE,
                type_lookup_code VARCHAR(25),
                status_lookup_code VARCHAR(25),
                vendor_id BIGINT REFERENCES ap_suppliers(vendor_id),
                amount NUMERIC(15,2),
                currency_code VARCHAR(15),
                approved_flag VARCHAR(1),
                creation_date TIMESTAMP,
                approved_date TIMESTAMP,
                created_by BIGINT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS po_lines_all (
                po_line_id BIGINT PRIMARY KEY,
                po_header_id BIGINT REFERENCES po_headers_all(po_header_id),
                line_num NUMERIC,
                item_description VARCHAR(240),
                quantity NUMERIC,
                unit_price NUMERIC(15,2),
                amount NUMERIC(15,2),
                currency_code VARCHAR(15)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS po_distributions_all (
                distribution_id BIGINT PRIMARY KEY,
                po_line_id BIGINT REFERENCES po_lines_all(po_line_id),
                po_header_id BIGINT REFERENCES po_headers_all(po_header_id),
                distribution_num NUMERIC,
                quantity_ordered NUMERIC,
                amount_ordered NUMERIC(15,2)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS po_shipments_all (
                shipment_id BIGINT PRIMARY KEY,
                po_line_id BIGINT REFERENCES po_lines_all(po_line_id),
                po_header_id BIGINT REFERENCES po_headers_all(po_header_id),
                shipment_num NUMERIC,
                quantity NUMERIC,
                need_by_date DATE
            )
            """,
            
            # Invoice tables (AP module)
            """
            CREATE TABLE IF NOT EXISTS ap_invoices_all (
                invoice_id BIGINT PRIMARY KEY,
                invoice_num VARCHAR(50),
                invoice_type_lookup_code VARCHAR(25),
                vendor_id BIGINT REFERENCES ap_suppliers(vendor_id),
                invoice_amount NUMERIC(15,2),
                payment_status VARCHAR(20),
                approval_status VARCHAR(20),
                invoice_date DATE,
                due_date DATE,
                creation_date TIMESTAMP,
                created_by BIGINT,
                UNIQUE(invoice_num, vendor_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS ap_invoice_lines_all (
                invoice_line_id BIGINT PRIMARY KEY,
                invoice_id BIGINT REFERENCES ap_invoices_all(invoice_id),
                line_number NUMERIC,
                description VARCHAR(240),
                quantity NUMERIC,
                unit_price NUMERIC(15,2),
                amount NUMERIC(15,2),
                tax_amount NUMERIC(15,2),
                po_header_id BIGINT REFERENCES po_headers_all(po_header_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS ap_invoice_distributions_all (
                distribution_id BIGINT PRIMARY KEY,
                invoice_id BIGINT REFERENCES ap_invoices_all(invoice_id),
                distribution_num NUMERIC,
                amount NUMERIC(15,2),
                accounting_date DATE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS ap_payments_all (
                check_id BIGINT PRIMARY KEY,
                check_number VARCHAR(50) UNIQUE,
                amount NUMERIC(15,2),
                check_date DATE,
                status VARCHAR(20),
                vendor_id BIGINT REFERENCES ap_suppliers(vendor_id),
                bank_account_id BIGINT REFERENCES ap_bank_accounts(bank_account_id)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS ap_invoice_payments_all (
                invoice_payment_id BIGINT PRIMARY KEY,
                invoice_id BIGINT REFERENCES ap_invoices_all(invoice_id),
                check_id BIGINT REFERENCES ap_payments_all(check_id),
                amount NUMERIC(15,2)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS ap_payment_schedules_all (
                schedule_id BIGINT PRIMARY KEY,
                invoice_id BIGINT REFERENCES ap_invoices_all(invoice_id),
                payment_num NUMERIC,
                due_date DATE,
                amount_due NUMERIC(15,2),
                amount_paid NUMERIC(15,2)
            )
            """,
            
            # AR module
            """
            CREATE TABLE IF NOT EXISTS ar_customers (
                customer_id BIGINT PRIMARY KEY,
                customer_number VARCHAR(30) UNIQUE,
                customer_name VARCHAR(360),
                customer_type VARCHAR(30),
                status VARCHAR(20),
                credit_limit NUMERIC(15,2)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS ar_transactions_all (
                transaction_id BIGINT PRIMARY KEY,
                transaction_number VARCHAR(50) UNIQUE,
                transaction_type VARCHAR(30),
                customer_id BIGINT REFERENCES ar_customers(customer_id),
                amount NUMERIC(15,2),
                amount_due NUMERIC(15,2),
                status VARCHAR(20),
                transaction_date DATE,
                due_date DATE,
                creation_date TIMESTAMP,
                created_by BIGINT
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS ar_transaction_lines_all (
                line_id BIGINT PRIMARY KEY,
                transaction_id BIGINT REFERENCES ar_transactions_all(transaction_id),
                line_number NUMERIC,
                line_type VARCHAR(30),
                amount NUMERIC(15,2),
                tax_amount NUMERIC(15,2)
            )
            """,
            
            # GL module
            """
            CREATE TABLE IF NOT EXISTS gl_ledgers (
                ledger_id BIGINT PRIMARY KEY,
                ledger_name VARCHAR(100),
                chart_of_accounts_id BIGINT,
                currency_code VARCHAR(15),
                period_set_name VARCHAR(30),
                ledger_type VARCHAR(30)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS gl_accounts (
                account_id BIGINT PRIMARY KEY,
                segment1 VARCHAR(30),
                segment2 VARCHAR(30),
                segment3 VARCHAR(30),
                segment4 VARCHAR(30),
                enabled_flag VARCHAR(1)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS gl_je_batches (
                batch_id BIGINT PRIMARY KEY,
                batch_name VARCHAR(100),
                ledger_id BIGINT REFERENCES gl_ledgers(ledger_id),
                period_name VARCHAR(30),
                status VARCHAR(20),
                total_dr NUMERIC(15,2),
                total_cr NUMERIC(15,2)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS gl_je_headers (
                je_header_id BIGINT PRIMARY KEY,
                je_batch_id BIGINT REFERENCES gl_je_batches(batch_id),
                je_name VARCHAR(100),
                ledger_id BIGINT REFERENCES gl_ledgers(ledger_id),
                period_name VARCHAR(30),
                currency_code VARCHAR(15),
                status VARCHAR(20),
                effective_date DATE,
                posted_date DATE
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS gl_je_lines (
                je_line_id BIGINT PRIMARY KEY,
                je_header_id BIGINT REFERENCES gl_je_headers(je_header_id),
                line_num NUMERIC,
                code_combination_id BIGINT REFERENCES gl_accounts(account_id),
                segment3 VARCHAR(30),
                entered_dr NUMERIC(15,2),
                entered_cr NUMERIC(15,2),
                accounted_dr NUMERIC(15,2),
                accounted_cr NUMERIC(15,2)
            )
            """,
            
            # Master data
            """
            CREATE TABLE IF NOT EXISTS employees (
                employee_id BIGINT PRIMARY KEY,
                employee_name VARCHAR(100),
                department VARCHAR(50)
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS currencies (
                currency_code VARCHAR(15) PRIMARY KEY,
                currency_name VARCHAR(50)
            )
            """
        ]
        
        for table_sql in tables:
            try:
                self.cursor.execute(table_sql)
            except Exception as e:
                print(f"  [WARN] Table creation warning: {e}")
        
        print("[OK] Tables created")
    
    def generate_sample_data(self):
        """Generate sample data"""
        print("[INFO] Generating sample data...")
        
        # Currencies
        currencies = [
            ('CNY', 'Chinese Yuan'),
            ('USD', 'US Dollar'),
            ('EUR', 'Euro'),
            ('GBP', 'British Pound'),
            ('JPY', 'Japanese Yen')
        ]
        execute_batch(
            self.cursor,
            "INSERT INTO currencies (currency_code, currency_name) VALUES (%s, %s) ON CONFLICT (currency_code) DO NOTHING",
            currencies
        )
        
        # Employees
        employees = [
            (1001, 'Zhang San', 'Procurement'),
            (1002, 'Li Si', 'Finance'),
            (1003, 'Wang Wu', 'Sales'),
            (1004, 'Zhao Liu', 'Warehouse'),
            (1005, 'Sun Qi', 'IT')
        ]
        execute_batch(
            self.cursor,
            "INSERT INTO employees (employee_id, employee_name, department) VALUES (%s, %s, %s) ON CONFLICT (employee_id) DO NOTHING",
            employees
        )
        
        # Suppliers
        suppliers = []
        for i in range(1, 51):
            suppliers.append((
                i,
                f'V{i:05d}',
                f'Supplier {chr(65+i%26)}{i}',
                random.choice(['VENDOR', 'EMPLOYEE', 'ONE TIME']),
                random.choice(['ACTIVE', 'INACTIVE', 'PENDING']),
                random.choice(['CNY', 'USD', 'EUR']),
                datetime.now() - timedelta(days=random.randint(0, 365)),
                random.choice([1001, 1002, 1003])
            ))
        execute_batch(
            self.cursor,
            "INSERT INTO ap_suppliers (vendor_id, segment1, vendor_name, vendor_type_lookup_code, status, invoice_currency_code, creation_date, created_by) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (vendor_id) DO NOTHING",
            suppliers
        )
        
        # Supplier Sites
        sites = []
        for i in range(1, 101):
            sites.append((
                i,
                (i % 50) + 1,
                f'SITE{i:03d}',
                f'Address Line {i}',
                random.choice(['Beijing', 'Shanghai', 'Guangzhou', 'Shenzhen', 'Chengdu']),
                'CN'
            ))
        execute_batch(
            self.cursor,
            "INSERT INTO ap_supplier_sites (vendor_site_id, vendor_id, vendor_site_code, address_line1, city, country) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (vendor_site_id) DO NOTHING",
            sites
        )
        
        # Supplier Contacts
        contacts = []
        for i in range(1, 101):
            contacts.append((
                i,
                (i % 50) + 1,
                f'First{i}',
                f'Last{i}',
                f'contact{i}@supplier{i}.com'
            ))
        execute_batch(
            self.cursor,
            "INSERT INTO ap_supplier_contacts (vendor_contact_id, vendor_id, first_name, last_name, email) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (vendor_contact_id) DO NOTHING",
            contacts
        )
        
        # Bank Accounts
        bank_accounts = []
        for i in range(1, 51):
            bank_accounts.append((
                i,
                i,
                f'62284800{i:08d}',
                random.choice(['Bank of China', 'ICBC', 'China Construction Bank', 'Agricultural Bank of China']),
                random.choice(['CNY', 'USD'])
            ))
        execute_batch(
            self.cursor,
            "INSERT INTO ap_bank_accounts (bank_account_id, vendor_id, account_num, bank_name, currency_code) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (bank_account_id) DO NOTHING",
            bank_accounts
        )
        
        # Customers
        customers = []
        for i in range(1, 21):
            customers.append((
                i,
                f'C{i:05d}',
                f'Customer {chr(65+i%26)}{i}',
                random.choice(['EXTERNAL', 'INTERNAL', 'PARTNER']),
                random.choice(['ACTIVE', 'INACTIVE']),
                random.uniform(100000, 1000000)
            ))
        execute_batch(
            self.cursor,
            "INSERT INTO ar_customers (customer_id, customer_number, customer_name, customer_type, status, credit_limit) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (customer_id) DO NOTHING",
            customers
        )
        
        # Purchase Orders
        pos = []
        for i in range(1, 101):
            amount = round(random.uniform(1000, 100000), 2)
            pos.append((
                i,
                f'PO{i:07d}',
                random.choice(['STANDARD', 'BLANKET', 'CONTRACT']),
                random.choice(['APPROVED', 'PENDING', 'CLOSED']),
                (i % 50) + 1,
                amount,
                'CNY',
                'Y' if random.random() > 0.3 else 'N',
                datetime.now() - timedelta(days=random.randint(0, 180)),
                datetime.now() - timedelta(days=random.randint(0, 90)) if random.random() > 0.3 else None,
                random.choice([1001, 1002])
            ))
        execute_batch(
            self.cursor,
            "INSERT INTO po_headers_all (po_header_id, segment1, type_lookup_code, status_lookup_code, vendor_id, amount, currency_code, approved_flag, creation_date, approved_date, created_by) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (po_header_id) DO NOTHING",
            pos
        )
        
        # PO Lines
        po_lines = []
        line_id = 1
        for po_id in range(1, 101):
            for line_num in range(1, random.randint(2, 6)):
                qty = random.randint(1, 100)
                price = round(random.uniform(10, 1000), 2)
                po_lines.append((
                    line_id,
                    po_id,
                    line_num,
                    f'Item Description {line_id}',
                    qty,
                    price,
                    round(qty * price, 2),
                    'CNY'
                ))
                line_id += 1
        execute_batch(
            self.cursor,
            "INSERT INTO po_lines_all (po_line_id, po_header_id, line_num, item_description, quantity, unit_price, amount, currency_code) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (po_line_id) DO NOTHING",
            po_lines
        )
        
        # Invoices
        invoices = []
        for i in range(1, 201):
            amount = round(random.uniform(500, 50000), 2)
            invoices.append((
                i,
                f'INV{i:08d}',
                random.choice(['STANDARD', 'DEBIT MEMO', 'CREDIT MEMO']),
                (i % 50) + 1,
                amount,
                random.choice(['PAID', 'UNPAID', 'PARTIALLY PAID']),
                random.choice(['APPROVED', 'PENDING', 'REJECTED']),
                datetime.now().date() - timedelta(days=random.randint(0, 90)),
                datetime.now().date() + timedelta(days=random.randint(0, 60)),
                datetime.now() - timedelta(days=random.randint(0, 90)),
                random.choice([1001, 1002])
            ))
        execute_batch(
            self.cursor,
            "INSERT INTO ap_invoices_all (invoice_id, invoice_num, invoice_type_lookup_code, vendor_id, invoice_amount, payment_status, approval_status, invoice_date, due_date, creation_date, created_by) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (invoice_id) DO NOTHING",
            invoices
        )
        
        # Invoice Lines
        invoice_lines = []
        line_id = 1
        for inv_id in range(1, 201):
            for line_num in range(1, random.randint(1, 4)):
                amount = round(random.uniform(100, 10000), 2)
                invoice_lines.append((
                    line_id,
                    inv_id,
                    line_num,
                    f'Line Item {line_id}',
                    random.randint(1, 50),
                    round(amount / random.randint(1, 50), 2),
                    amount,
                    round(amount * 0.13, 2),
                    random.randint(1, 100) if random.random() > 0.5 else None
                ))
                line_id += 1
        execute_batch(
            self.cursor,
            "INSERT INTO ap_invoice_lines_all (invoice_line_id, invoice_id, line_number, description, quantity, unit_price, amount, tax_amount, po_header_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT (invoice_line_id) DO NOTHING",
            invoice_lines
        )
        
        # Payments
        payments = []
        for i in range(1, 151):
            amount = round(random.uniform(500, 30000), 2)
            payments.append((
                i,
                f'CHK{i:07d}',
                amount,
                datetime.now().date() - timedelta(days=random.randint(0, 60)),
                random.choice(['ISSUED', 'CLEARED', 'VOID']),
                (i % 50) + 1,
                (i % 50) + 1
            ))
        execute_batch(
            self.cursor,
            "INSERT INTO ap_payments_all (check_id, check_number, amount, check_date, status, vendor_id, bank_account_id) VALUES (%s, %s, %s, %s, %s, %s, %s) ON CONFLICT (check_id) DO NOTHING",
            payments
        )
        
        # GL Ledger
        ledgers = [(1, 'Primary Ledger', 1, 'CNY', 'Monthly', 'PRIMARY')]
        execute_batch(
            self.cursor,
            "INSERT INTO gl_ledgers (ledger_id, ledger_name, chart_of_accounts_id, currency_code, period_set_name, ledger_type) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (ledger_id) DO NOTHING",
            ledgers
        )
        
        # GL Accounts
        accounts = [
            (1001, '1000', '1000', '1001', '0000', 'Y'),
            (1002, '1000', '1000', '1002', '0000', 'Y'),
            (2001, '2000', '2000', '2001', '0000', 'Y'),
            (3001, '3000', '3000', '3001', '0000', 'Y'),
            (4001, '4000', '4000', '4001', '0000', 'Y'),
            (5001, '5000', '5000', '5001', '0000', 'Y')
        ]
        execute_batch(
            self.cursor,
            "INSERT INTO gl_accounts (account_id, segment1, segment2, segment3, segment4, enabled_flag) VALUES (%s, %s, %s, %s, %s, %s) ON CONFLICT (account_id) DO NOTHING",
            accounts
        )
        
        self.conn.commit()
        print("[OK] Sample data generated")
    
    def verify_data(self):
        """Verify data import"""
        print("\n[INFO] Verifying data...")
        
        tables = [
            'ap_suppliers', 'ap_supplier_sites', 'ap_supplier_contacts', 'ap_bank_accounts',
            'po_headers_all', 'po_lines_all',
            'ap_invoices_all', 'ap_invoice_lines_all', 'ap_payments_all',
            'ar_customers', 'ar_transactions_all',
            'gl_ledgers', 'gl_accounts',
            'employees', 'currencies'
        ]
        
        for table in tables:
            self.cursor.execute(f"SELECT COUNT(*) FROM {table}")
            count = self.cursor.fetchone()[0]
            print(f"  {table}: {count} rows")
        
        print("[OK] Verification complete")
    
    def run(self):
        """Execute full data generation"""
        print("=" * 60)
        print("ERP Sample Data Generator for PostgreSQL")
        print("=" * 60)
        print(f"Database: {DB_HOST}:{DB_PORT}/{DB_NAME}")
        print("=" * 60)
        
        try:
            self.create_tables()
            self.generate_sample_data()
            self.verify_data()
            
            print("\n" + "=" * 60)
            print("[DONE] Sample data generation complete!")
            print("=" * 60)
            
        except Exception as e:
            print(f"[ERROR] {e}")
            self.conn.rollback()
            raise
        finally:
            self.close()

if __name__ == "__main__":
    generator = SampleDataGenerator()
    generator.run()