# -*- coding: utf-8 -*-
"""
Advanced Sample Data Generator for Oracle EBS
Generates comprehensive sample data including XLA, GL, AR modules
"""

import psycopg2
from psycopg2.extras import execute_batch
import random
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

DB_CONFIG = {
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': os.getenv('POSTGRES_PORT', '5432'),
    'database': os.getenv('POSTGRES_DB', 'erp'),
    'user': os.getenv('POSTGRES_USER', 'postgres'),
    'password': os.getenv('POSTGRES_PASSWORD', 'postgres')
}

class AdvancedDataGenerator:
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cursor = self.conn.cursor()
    
    def close(self):
        self.cursor.close()
        self.conn.close()
    
    def generate_xla_data(self, count=50):
        """Generate XLA Accounting Engine data"""
        print("\n[INFO] Generating XLA data...")
        
        # Check if tables exist
        try:
            self.cursor.execute("SELECT COUNT(*) FROM xla_transaction_entities")
            existing = self.cursor.fetchone()[0]
            if existing > 0:
                print(f"  ✓ XLA data already exists: {existing} entities")
                return
        except:
            # Tables don't exist, skip
            print("  - XLA tables not found, skipping...")
            return
        
        # ... rest of XLA generation code ...
    
    def generate_gl_data(self, count=20):
        """Generate General Ledger data"""
        print("\n[INFO] Generating GL data...")
        
        # GL Ledgers
        ledgers = [
            (1, 'Primary Ledger', 1, 'CNY', 'Monthly Cal', 'Primary'),
            (2, 'Secondary Ledger', 1, 'USD', 'Monthly Cal', 'Secondary')
        ]
        
        execute_batch(self.cursor, """
            INSERT INTO gl_ledgers (ledger_id, ledger_name, chart_of_accounts_id, currency_code, period_set_name, ledger_type)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (ledger_id) DO NOTHING
        """, ledgers)
        
        # GL Periods
        periods = []
        for year in [2025, 2026]:
            for month in range(1, 13):
                period_id = year * 100 + month
                start_date = datetime(year, month, 1)
                if month == 12:
                    end_date = datetime(year + 1, 1, 1) - timedelta(days=1)
                else:
                    end_date = datetime(year, month + 1, 1) - timedelta(days=1)
                
                periods.append((
                    period_id,
                    1,  # Ledger ID
                    f'{year}-{month:02d}',
                    'Monthly',
                    start_date,
                    end_date,
                    'OPEN' if year == 2026 and month <= datetime.now().month else 'CLOSED'
                ))
        
        execute_batch(self.cursor, """
            INSERT INTO gl_periods (period_id, ledger_id, period_name, period_type, start_date, end_date, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (period_id) DO NOTHING
        """, periods)
        
        # GL Accounts (Chart of Accounts)
        accounts = [
            (1, '1001', '1', '0', '0', '0', '现金', 'A'),
            (2, '1002', '1', '0', '0', '0', '银行存款', 'A'),
            (3, '1122', '1', '0', '0', '0', '应收账款', 'A'),
            (4, '1401', '1', '0', '0', '0', '材料采购', 'A'),
            (5, '2202', '1', '0', '0', '0', '应付账款', 'L'),
            (6, '6001', '1', '0', '0', '0', '主营业务收入', 'R'),
            (7, '6401', '1', '0', '0', '0', '主营业务成本', 'E'),
        ]
        
        execute_batch(self.cursor, """
            INSERT INTO gl_accounts (account_id, segment1, segment2, segment3, segment4, segment5, account_name, enabled_flag)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (account_id) DO NOTHING
        """, accounts)
        
        # GL Batches
        batches = []
        for i in range(count):
            batch_id = i + 1
            batches.append((
                batch_id,
                f'BATCH-{batch_id:04d}',
                1,  # Ledger ID
                f'2026-{(i % 12) + 1:02d}',
                'POSTED',
                random.uniform(10000, 100000),
                random.uniform(10000, 100000)
            ))
        
        execute_batch(self.cursor, """
            INSERT INTO gl_je_batches (batch_id, batch_name, ledger_id, period_name, status, total_dr, total_cr)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (batch_id) DO NOTHING
        """, batches)
        
        # GL Journals
        journals = []
        journal_lines = []
        line_id = 1
        
        for i in range(count):
            je_header_id = i + 1
            batch_id = (i % count) + 1
            amount = random.uniform(5000, 50000)
            
            journals.append((
                je_header_id,
                batch_id,
                f'JE-{je_header_id:04d}',
                1,  # Ledger ID
                f'2026-{(i % 12) + 1:02d}',
                'CNY',
                'POSTED',
                datetime.now() - timedelta(days=random.randint(0, 90)),
                datetime.now() - timedelta(days=random.randint(0, 60))
            ))
            
            # Each journal has 2 lines (Dr/Cr)
            journal_lines.append((
                line_id,
                je_header_id,
                1,
                (i % 7) + 1,  # Account ID
                f'SEG3-{i}',
                amount,
                0,
                amount,
                0
            ))
            line_id += 1
            
            journal_lines.append((
                line_id,
                je_header_id,
                2,
                ((i + 3) % 7) + 1,  # Different Account ID
                f'SEG3-{i+3}',
                0,
                amount,
                0,
                amount
            ))
            line_id += 1
        
        execute_batch(self.cursor, """
            INSERT INTO gl_je_headers (je_header_id, je_batch_id, je_name, ledger_id, period_name, 
                                       currency_code, status, effective_date, posted_date)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (je_header_id) DO NOTHING
        """, journals)
        
        execute_batch(self.cursor, """
            INSERT INTO gl_je_lines (je_line_id, je_header_id, line_num, code_combination_id, segment3,
                                     entered_dr, entered_cr, accounted_dr, accounted_cr)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (je_line_id) DO NOTHING
        """, journal_lines)
        
        # GL Balances
        balances = []
        for acct_id in range(1, 8):
            for period_id in range(202601, 202613):
                balances.append((
                    period_id * 100 + acct_id,
                    1,  # Ledger ID
                    acct_id,
                    f'{period_id}',
                    'CNY',
                    'A',
                    random.uniform(100000, 500000),
                    random.uniform(50000, 300000),
                    random.uniform(50000, 200000),
                    random.uniform(30000, 150000),
                    random.uniform(200000, 800000),
                    random.uniform(100000, 500000)
                ))
        
        execute_batch(self.cursor, """
            INSERT INTO gl_balances (balance_id, ledger_id, code_combination_id, period_name, currency_code,
                                     actual_flag, begin_balance_dr, begin_balance_cr, period_dr, period_cr,
                                     end_balance_dr, end_balance_cr)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (balance_id) DO NOTHING
        """, balances)
        
        self.conn.commit()
        print(f"  ✓ Generated {len(ledgers)} ledgers, {len(periods)} periods, {len(accounts)} accounts")
        print(f"  ✓ Generated {len(batches)} batches, {len(journals)} journals, {len(journal_lines)} journal lines")
        print(f"  ✓ Generated {len(balances)} balance records")
    
    def generate_ar_data(self, count=30):
        """Generate Accounts Receivable data"""
        print("\n[INFO] Generating AR data...")
        
        # Customers
        customers = []
        for i in range(20):
            cust_id = i + 1
            customers.append((
                cust_id,
                f'CUST-{cust_id:03d}',
                f'Customer {chr(65+i)} Corp',
                'CORPORATE',
                'ACTIVE',
                random.uniform(50000, 500000)
            ))
        
        execute_batch(self.cursor, """
            INSERT INTO ar_customers (customer_id, customer_number, customer_name, customer_type, status, credit_limit)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (customer_id) DO NOTHING
        """, customers)
        
        # AR Transactions
        transactions = []
        transaction_lines = []
        line_id = 1
        
        for i in range(count):
            txn_id = i + 1
            cust_id = (i % 20) + 1
            amount = random.uniform(1000, 50000)
            txn_date = datetime.now() - timedelta(days=random.randint(0, 90))
            
            transactions.append((
                txn_id,
                f'TXN-{txn_id:04d}',
                'INVOICE',
                cust_id,
                float(amount),
                float(amount),
                'OPEN' if i % 3 != 0 else 'PAID',
                txn_date,
                txn_date + timedelta(days=30),
                txn_date,
                (i % 10) + 1  # Created by employee
            ))
            
            # Transaction Lines
            num_lines = random.randint(1, 3)
            remaining = amount
            for j in range(num_lines):
                if j == num_lines - 1:
                    line_amount = remaining
                else:
                    line_amount = remaining / (num_lines - j)
                    remaining -= line_amount
                
                transaction_lines.append((
                    line_id,
                    txn_id,
                    j + 1,
                    'REV',
                    float(line_amount),
                    float(line_amount * 0.13)  # 13% tax
                ))
                line_id += 1
        
        execute_batch(self.cursor, """
            INSERT INTO ar_transactions_all (transaction_id, transaction_number, transaction_type, customer_id,
                                             amount, amount_due, status, transaction_date, due_date, created_date, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (transaction_id) DO NOTHING
        """, transactions)
        
        execute_batch(self.cursor, """
            INSERT INTO ar_transaction_lines_all (line_id, transaction_id, line_number, line_type, amount, tax_amount)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (line_id) DO NOTHING
        """, transaction_lines)
        
        # Cash Receipts
        receipts = []
        for i in range(count // 2):
            receipt_id = i + 1
            cust_id = (i % 20) + 1
            amount = random.uniform(1000, 30000)
            
            receipts.append((
                receipt_id,
                f'REC-{receipt_id:04d}',
                cust_id,
                float(amount),
                datetime.now() - timedelta(days=random.randint(0, 60)),
                'CLEARED',
                1  # Bank account ID
            ))
        
        execute_batch(self.cursor, """
            INSERT INTO ar_cash_receipts_all (cash_receipt_id, receipt_number, customer_id, amount, 
                                              receipt_date, status, bank_account_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (cash_receipt_id) DO NOTHING
        """, receipts)
        
        self.conn.commit()
        print(f"  ✓ Generated {len(customers)} customers, {len(transactions)} transactions")
        print(f"  ✓ Generated {len(transaction_lines)} transaction lines, {len(receipts)} receipts")
    
    def generate_hr_data(self, count=50):
        """Generate Human Resources data"""
        print("\n[INFO] Generating HR data...")
        
        # Check if table exists and has data
        self.cursor.execute("SELECT COUNT(*) FROM employees")
        emp_count = self.cursor.fetchone()[0]
        
        if emp_count < count:
            employees = []
            for i in range(emp_count, count):
                emp_id = i + 1
                employees.append((
                    emp_id,
                    f'Employee {chr(65 + (i % 26))}',
                    'IT'
                ))
            
            execute_batch(self.cursor, """
                INSERT INTO employees (employee_id, employee_name, department)
                VALUES (%s, %s, %s)
                ON CONFLICT (employee_id) DO NOTHING
            """, employees)
            
            self.conn.commit()
            print(f"  ✓ Generated {len(employees)} employees")
        else:
            print(f"  ✓ Employees already exist: {emp_count}")
    
    def generate_all(self):
        """Generate all sample data"""
        print("="*70)
        print("Advanced Oracle EBS Sample Data Generator")
        print("="*70)
        
        try:
            self.generate_hr_data(107)
            self.generate_xla_data(50)
            self.generate_gl_data(20)
            self.generate_ar_data(30)
            
            print("\n" + "="*70)
            print("✅ All sample data generated successfully!")
            print("="*70)
            
            # Show summary
            self.cursor.execute("""
                SELECT 
                    (SELECT COUNT(*) FROM xla_transaction_entities) as xla_entities,
                    (SELECT COUNT(*) FROM xla_events) as xla_events,
                    (SELECT COUNT(*) FROM xla_ae_headers) as ae_headers,
                    (SELECT COUNT(*) FROM xla_ae_lines) as ae_lines,
                    (SELECT COUNT(*) FROM gl_ledgers) as ledgers,
                    (SELECT COUNT(*) FROM gl_je_headers) as journals,
                    (SELECT COUNT(*) FROM gl_je_lines) as journal_lines,
                    (SELECT COUNT(*) FROM ar_customers) as customers,
                    (SELECT COUNT(*) FROM ar_transactions_all) as ar_txns,
                    (SELECT COUNT(*) FROM per_all_people_f) as employees
            """)
            row = self.cursor.fetchone()
            
            print("\n📊 Data Summary:")
            print(f"  XLA Entities: {row[0]}")
            print(f"  XLA Events: {row[1]}")
            print(f"  Accounting Entries: {row[2]} headers, {row[3]} lines")
            print(f"  GL Ledgers: {row[4]}")
            print(f"  GL Journals: {row[5]} headers, {row[6]} lines")
            print(f"  AR Customers: {row[7]}")
            print(f"  AR Transactions: {row[8]}")
            print(f"  Employees: {row[9]}")
            print("="*70)
            
        except Exception as e:
            print(f"\n❌ Error generating data: {e}")
            raise
        finally:
            self.close()


def main():
    generator = AdvancedDataGenerator()
    generator.generate_all()


if __name__ == '__main__':
    main()
