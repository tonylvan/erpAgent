# -*- coding: utf-8 -*-
"""
Sync data from PostgreSQL to Neo4j
Based on ERP relational to graph mapping design
"""

import psycopg2
from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

# PostgreSQL config
PG_HOST = os.getenv('POSTGRES_HOST', 'localhost')
PG_PORT = os.getenv('POSTGRES_PORT', '5432')
PG_DB = os.getenv('POSTGRES_DB', 'erp')
PG_USER = os.getenv('POSTGRES_USER', 'postgres')
PG_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'postgres')

# Neo4j config
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'Tony1985')
NEO4J_DATABASE = os.getenv('NEO4J_DATABASE', 'neo4j')

class PostgresToNeo4jSync:
    def __init__(self):
        self.pg_conn = psycopg2.connect(
            host=PG_HOST, port=PG_PORT, database=PG_DB,
            user=PG_USER, password=PG_PASSWORD
        )
        self.pg_cursor = self.pg_conn.cursor()
        self.neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    def close(self):
        self.pg_cursor.close()
        self.pg_conn.close()
        self.neo4j_driver.close()
    
    def run_neo4j_query(self, query, params=None):
        with self.neo4j_driver.session(database=NEO4J_DATABASE) as session:
            result = session.run(query, params or {})
            return [record for record in result]
    
    def sync_suppliers(self):
        """Sync supplier data"""
        print("[INFO] Syncing suppliers...")
        
        self.pg_cursor.execute("SELECT vendor_id, segment1, vendor_name, vendor_type_lookup_code, status, invoice_currency_code, creation_date, created_by FROM ap_suppliers")
        suppliers = self.pg_cursor.fetchall()
        
        for s in suppliers:
            self.run_neo4j_query("""
            MERGE (sup:Supplier {id: $id, code: $code})
            SET sup.name = $name, sup.type = $type, sup.status = $status,
                sup.currencyCode = $currency, sup.createdDate = $createdDate, sup.createdBy = $createdBy
            """, {
                'id': str(s[0]), 'code': s[1], 'name': s[2], 'type': s[3],
                'status': s[4], 'currency': s[5], 'createdDate': str(s[6]) if s[6] else None, 'createdBy': str(s[7]) if s[7] else None
            })
        
        # Supplier Sites
        self.pg_cursor.execute("SELECT vendor_site_id, vendor_id, vendor_site_code, address_line1, city, country FROM ap_supplier_sites")
        sites = self.pg_cursor.fetchall()
        
        for site in sites:
            self.run_neo4j_query("""
            MERGE (ss:SupplierSite {id: $id})
            SET ss.vendorId = $vendorId, ss.code = $code, ss.address = $address, ss.city = $city, ss.country = $country
            WITH ss
            MATCH (sup:Supplier {id: toString($vendorId)})
            MERGE (sup)-[:HAS_SITE]->(ss)
            """, {
                'id': str(site[0]), 'vendorId': site[1], 'code': site[2],
                'address': site[3], 'city': site[4], 'country': site[5]
            })
        
        # Supplier Contacts
        self.pg_cursor.execute("SELECT vendor_contact_id, vendor_id, first_name, last_name, email FROM ap_supplier_contacts")
        contacts = self.pg_cursor.fetchall()
        
        for contact in contacts:
            self.run_neo4j_query("""
            MERGE (sc:SupplierContact {id: $id})
            SET sc.vendorId = $vendorId, sc.firstName = $firstName, sc.lastName = $lastName, sc.email = $email
            WITH sc
            MATCH (sup:Supplier {id: toString($vendorId)})
            MERGE (sup)-[:HAS_CONTACT]->(sc)
            """, {
                'id': str(contact[0]), 'vendorId': contact[1], 'firstName': contact[2],
                'lastName': contact[3], 'email': contact[4]
            })
        
        # Bank Accounts
        self.pg_cursor.execute("SELECT bank_account_id, vendor_id, account_num, bank_name, currency_code FROM ap_bank_accounts")
        banks = self.pg_cursor.fetchall()
        
        for bank in banks:
            self.run_neo4j_query("""
            MERGE (ba:BankAccount {id: $id})
            SET ba.vendorId = $vendorId, ba.accountNum = $accountNum, ba.bankName = $bankName, ba.currencyCode = $currency
            WITH ba
            MATCH (sup:Supplier {id: toString($vendorId)})
            MERGE (sup)-[:HAS_BANK_ACCOUNT]->(ba)
            """, {
                'id': str(bank[0]), 'vendorId': bank[1], 'accountNum': bank[2],
                'bankName': bank[3], 'currency': bank[4]
            })
        
        print(f"[OK] Synced {len(suppliers)} suppliers")
    
    def sync_purchase_orders(self):
        """Sync purchase order data"""
        print("[INFO] Syncing purchase orders...")
        
        self.pg_cursor.execute("SELECT po_header_id, segment1, type_lookup_code, status_lookup_code, vendor_id, amount, currency_code, approved_flag, creation_date, approved_date, created_by FROM po_headers_all")
        pos = self.pg_cursor.fetchall()
        
        for po in pos:
            self.run_neo4j_query("""
            MERGE (po:PurchaseOrder {id: $id, poNumber: $poNumber})
            SET po.type = $type, po.status = $status, po.amount = $amount,
                po.currencyCode = $currency, po.approvedFlag = $approvedFlag,
                po.creationDate = $creationDate, po.approvedDate = $approvedDate, po.createdBy = $createdBy
            """, {
                'id': str(po[0]), 'poNumber': po[1], 'type': po[2], 'status': po[3],
                'vendorId': str(po[4]), 'amount': float(po[5]) if po[5] else 0,
                'currency': po[6], 'approvedFlag': po[7],
                'creationDate': str(po[8]) if po[8] else None,
                'approvedDate': str(po[9]) if po[9] else None,
                'createdBy': str(po[10]) if po[10] else None
            })
            
            # Create relationship to supplier
            self.run_neo4j_query("""
            MATCH (po:PurchaseOrder {poNumber: $poNumber})
            MATCH (sup:Supplier {id: toString($vendorId)})
            MERGE (sup)-[:SUPPLIES_VIA]->(po)
            """, {'poNumber': po[1], 'vendorId': po[4]})
        
        # PO Lines
        self.pg_cursor.execute("SELECT po_line_id, po_header_id, line_num, item_description, quantity, unit_price, amount, currency_code FROM po_lines_all")
        lines = self.pg_cursor.fetchall()
        
        for line in lines:
            self.run_neo4j_query("""
            MERGE (pl:POLine {id: $id})
            SET pl.poHeaderId = $poHeaderId, pl.lineNum = $lineNum, pl.itemDescription = $desc,
                pl.quantity = $qty, pl.unitPrice = $price, pl.amount = $amount, pl.currencyCode = $currency
            WITH pl
            MATCH (po:PurchaseOrder {id: toString($poHeaderId)})
            MERGE (po)-[:HAS_LINE]->(pl)
            """, {
                'id': str(line[0]), 'poHeaderId': line[1], 'lineNum': float(line[2]),
                'desc': line[3], 'qty': float(line[4]) if line[4] else 0,
                'price': float(line[5]) if line[5] else 0,
                'amount': float(line[6]) if line[6] else 0, 'currency': line[7]
            })
        
        print(f"[OK] Synced {len(pos)} purchase orders")
    
    def sync_invoices(self):
        """Sync invoice data"""
        print("[INFO] Syncing invoices...")
        
        self.pg_cursor.execute("SELECT invoice_id, invoice_num, invoice_type_lookup_code, vendor_id, invoice_amount, payment_status, approval_status, invoice_date, due_date, creation_date, created_by FROM ap_invoices_all")
        invoices = self.pg_cursor.fetchall()
        
        for inv in invoices:
            self.run_neo4j_query("""
            MERGE (inv:Invoice {id: $id, invoiceNum: $invoiceNum})
            SET inv.type = $type, inv.vendorId = $vendorId, inv.amount = $amount,
                inv.paymentStatus = $paymentStatus, inv.approvalStatus = $approvalStatus,
                inv.invoiceDate = $invoiceDate, inv.dueDate = $dueDate,
                inv.creationDate = $creationDate, inv.createdBy = $createdBy
            """, {
                'id': str(inv[0]), 'invoiceNum': inv[1], 'type': inv[2],
                'vendorId': str(inv[3]), 'amount': float(inv[4]) if inv[4] else 0,
                'paymentStatus': inv[5], 'approvalStatus': inv[6],
                'invoiceDate': str(inv[7]) if inv[7] else None,
                'dueDate': str(inv[8]) if inv[8] else None,
                'creationDate': str(inv[9]) if inv[9] else None,
                'createdBy': str(inv[10]) if inv[10] else None
            })
            
            # Relationship to supplier
            self.run_neo4j_query("""
            MATCH (inv:Invoice {invoiceNum: $invoiceNum})
            MATCH (sup:Supplier {id: toString($vendorId)})
            MERGE (sup)-[:SENDS_INVOICE]->(inv)
            """, {'invoiceNum': inv[1], 'vendorId': inv[3]})
        
        # Invoice Lines
        self.pg_cursor.execute("SELECT invoice_line_id, invoice_id, line_number, description, quantity, unit_price, amount, tax_amount, po_header_id FROM ap_invoice_lines_all")
        lines = self.pg_cursor.fetchall()
        
        for line in lines:
            self.run_neo4j_query("""
            MERGE (il:InvoiceLine {id: $id})
            SET il.invoiceId = $invoiceId, il.lineNumber = $lineNum, il.description = $desc,
                il.quantity = $qty, il.unitPrice = $price, il.amount = $amount,
                il.taxAmount = $tax, il.poHeaderId = $poHeaderId
            WITH il
            MATCH (inv:Invoice {id: toString($invoiceId)})
            MERGE (inv)-[:HAS_LINE]->(il)
            """, {
                'id': str(line[0]), 'invoiceId': line[1], 'lineNum': float(line[2]),
                'desc': line[3], 'qty': float(line[4]) if line[4] else 0,
                'price': float(line[5]) if line[5] else 0,
                'amount': float(line[6]) if line[6] else 0,
                'tax': float(line[7]) if line[7] else 0,
                'poHeaderId': str(line[8]) if line[8] else None
            })
        
        print(f"[OK] Synced {len(invoices)} invoices")
    
    def sync_payments(self):
        """Sync payment data"""
        print("[INFO] Syncing payments...")
        
        self.pg_cursor.execute("SELECT check_id, check_number, amount, check_date, status, vendor_id, bank_account_id FROM ap_payments_all")
        payments = self.pg_cursor.fetchall()
        
        for pmt in payments:
            self.run_neo4j_query("""
            MERGE (p:Payment {id: $id, checkNumber: $checkNumber})
            SET p.amount = $amount, p.checkDate = $checkDate, p.status = $status,
                p.vendorId = $vendorId, p.bankAccountId = $bankAccountId
            """, {
                'id': str(pmt[0]), 'checkNumber': pmt[1],
                'amount': float(pmt[2]) if pmt[2] else 0,
                'checkDate': str(pmt[3]) if pmt[3] else None,
                'status': pmt[4], 'vendorId': str(pmt[5]),
                'bankAccountId': str(pmt[6]) if pmt[6] else None
            })
        
        print(f"[OK] Synced {len(payments)} payments")
    
    def sync_customers(self):
        """Sync customer data"""
        print("[INFO] Syncing customers...")
        
        self.pg_cursor.execute("SELECT customer_id, customer_number, customer_name, customer_type, status, credit_limit FROM ar_customers")
        customers = self.pg_cursor.fetchall()
        
        for c in customers:
            self.run_neo4j_query("""
            MERGE (c:Customer {id: $id, customerNumber: $customerNumber})
            SET c.name = $name, c.type = $type, c.status = $status, c.creditLimit = $limit
            """, {
                'id': str(c[0]), 'customerNumber': c[1], 'name': c[2],
                'type': c[3], 'status': c[4],
                'limit': float(c[5]) if c[5] else 0
            })
        
        print(f"[OK] Synced {len(customers)} customers")
    
    def sync_gl(self):
        """Sync general ledger data"""
        print("[INFO] Syncing general ledger...")
        
        self.pg_cursor.execute("SELECT ledger_id, ledger_name, currency_code, ledger_type FROM gl_ledgers")
        ledgers = self.pg_cursor.fetchall()
        
        for l in ledgers:
            self.run_neo4j_query("""
            MERGE (gl:GLLedger {id: $id})
            SET gl.ledgerName = $name, gl.currencyCode = $currency, gl.ledgerType = $type
            """, {
                'id': str(l[0]), 'name': l[1], 'currency': l[2], 'type': l[3]
            })
        
        self.pg_cursor.execute("SELECT account_id, segment1, segment2, segment3, segment4, enabled_flag FROM gl_accounts")
        accounts = self.pg_cursor.fetchall()
        
        for a in accounts:
            self.run_neo4j_query("""
            MERGE (acc:GLAccount {id: $id})
            SET acc.segment1 = $s1, acc.segment2 = $s2, acc.segment3 = $s3,
                acc.segment4 = $s4, acc.enabledFlag = $enabled
            """, {
                'id': str(a[0]), 's1': a[1], 's2': a[2], 's3': a[3],
                's4': a[4], 'enabled': a[5]
            })
        
        print(f"[OK] Synced {len(ledgers)} ledgers, {len(accounts)} accounts")
    
    def sync_employees(self):
        """Sync employee data"""
        print("[INFO] Syncing employees...")
        
        self.pg_cursor.execute("SELECT employee_id, employee_name, department FROM employees")
        employees = self.pg_cursor.fetchall()
        
        for e in employees:
            self.run_neo4j_query("""
            MERGE (emp:Employee {id: $id})
            SET emp.name = $name, emp.department = $dept
            """, {
                'id': str(e[0]), 'name': e[1], 'dept': e[2]
            })
        
        print(f"[OK] Synced {len(employees)} employees")
    
    def sync_currencies(self):
        """Sync currency data"""
        print("[INFO] Syncing currencies...")
        
        self.pg_cursor.execute("SELECT currency_code, currency_name FROM currencies")
        currencies = self.pg_cursor.fetchall()
        
        for c in currencies:
            self.run_neo4j_query("""
            MERGE (curr:Currency {code: $code})
            SET curr.name = $name
            """, {'code': c[0], 'name': c[1]})
        
        print(f"[OK] Synced {len(currencies)} currencies")
    
    def verify_sync(self):
        """Verify sync results"""
        print("\n[INFO] Verifying Neo4j data...")
        
        labels = ['Supplier', 'PurchaseOrder', 'Invoice', 'Payment', 'Customer', 'GLLedger', 'GLAccount', 'Employee', 'Currency']
        
        for label in labels:
            result = self.run_neo4j_query(f"MATCH (n:{label}) RETURN count(n) as count")
            count = result[0]['count'] if result else 0
            print(f"  {label}: {count} nodes")
        
        # Count relationships
        result = self.run_neo4j_query("MATCH ()-[r]->() RETURN count(r) as count")
        rel_count = result[0]['count'] if result else 0
        print(f"  Relationships: {rel_count}")
    
    def run(self):
        """Execute full sync"""
        print("=" * 60)
        print("PostgreSQL to Neo4j Data Sync")
        print("=" * 60)
        print(f"PostgreSQL: {PG_HOST}:{PG_PORT}/{PG_DB}")
        print(f"Neo4j: {NEO4J_URI}")
        print("=" * 60)
        
        try:
            self.sync_currencies()
            self.sync_employees()
            self.sync_suppliers()
            self.sync_purchase_orders()
            self.sync_invoices()
            self.sync_payments()
            self.sync_customers()
            self.sync_gl()
            self.verify_sync()
            
            print("\n" + "=" * 60)
            print("[DONE] Data sync complete!")
            print("=" * 60)
            
        except Exception as e:
            print(f"[ERROR] {e}")
            raise
        finally:
            self.close()

if __name__ == "__main__":
    sync = PostgresToNeo4jSync()
    sync.run()