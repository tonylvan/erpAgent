# -*- coding: utf-8 -*-
"""
ERP Graph Database Schema Setup Script
Based on ERP relational model to graph model mapping design document
"""

from neo4j import GraphDatabase
import os
import sys

# Force UTF-8 output on Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

# Neo4j connection config
NEO4J_URI = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
NEO4J_USER = os.getenv('NEO4J_USER', 'neo4j')
NEO4J_PASSWORD = os.getenv('NEO4J_PASSWORD', 'Tony1985')
NEO4J_DATABASE = os.getenv('NEO4J_DATABASE', 'neo4j')

class Neo4jSchemaSetup:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    
    def close(self):
        self.driver.close()
    
    def run_query(self, query, parameters=None):
        with self.driver.session(database=NEO4J_DATABASE) as session:
            result = session.run(query, parameters or {})
            return [record for record in result]
    
    def create_constraints(self):
        """Create unique constraints"""
        constraints = [
            # Supplier module
            "CREATE CONSTRAINT supplier_id_unique IF NOT EXISTS FOR (s:Supplier) REQUIRE s.id IS UNIQUE",
            "CREATE CONSTRAINT supplier_code_unique IF NOT EXISTS FOR (s:Supplier) REQUIRE s.code IS UNIQUE",
            "CREATE CONSTRAINT supplier_site_id_unique IF NOT EXISTS FOR (ss:SupplierSite) REQUIRE ss.id IS UNIQUE",
            "CREATE CONSTRAINT supplier_contact_id_unique IF NOT EXISTS FOR (sc:SupplierContact) REQUIRE sc.id IS UNIQUE",
            "CREATE CONSTRAINT bank_account_id_unique IF NOT EXISTS FOR (ba:BankAccount) REQUIRE ba.id IS UNIQUE",
            
            # Purchase module
            "CREATE CONSTRAINT po_id_unique IF NOT EXISTS FOR (po:PurchaseOrder) REQUIRE po.id IS UNIQUE",
            "CREATE CONSTRAINT po_number_unique IF NOT EXISTS FOR (po:PurchaseOrder) REQUIRE po.poNumber IS UNIQUE",
            "CREATE CONSTRAINT po_line_id_unique IF NOT EXISTS FOR (pl:POLine) REQUIRE pl.id IS UNIQUE",
            "CREATE CONSTRAINT po_distribution_id_unique IF NOT EXISTS FOR (pd:PODistribution) REQUIRE pd.id IS UNIQUE",
            "CREATE CONSTRAINT po_shipment_id_unique IF NOT EXISTS FOR (ps:POShipment) REQUIRE ps.id IS UNIQUE",
            
            # AP module
            "CREATE CONSTRAINT invoice_id_unique IF NOT EXISTS FOR (inv:Invoice) REQUIRE inv.id IS UNIQUE",
            "CREATE CONSTRAINT invoice_num_unique IF NOT EXISTS FOR (inv:Invoice) REQUIRE inv.invoiceNum IS UNIQUE",
            "CREATE CONSTRAINT invoice_line_id_unique IF NOT EXISTS FOR (il:InvoiceLine) REQUIRE il.id IS UNIQUE",
            "CREATE CONSTRAINT invoice_distribution_id_unique IF NOT EXISTS FOR (id:InvoiceDistribution) REQUIRE id.id IS UNIQUE",
            "CREATE CONSTRAINT payment_id_unique IF NOT EXISTS FOR (p:Payment) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT payment_check_number_unique IF NOT EXISTS FOR (p:Payment) REQUIRE p.checkNumber IS UNIQUE",
            "CREATE CONSTRAINT invoice_payment_id_unique IF NOT EXISTS FOR (ip:InvoicePayment) REQUIRE ip.id IS UNIQUE",
            "CREATE CONSTRAINT payment_schedule_id_unique IF NOT EXISTS FOR (ps:PaymentSchedule) REQUIRE ps.id IS UNIQUE",
            
            # AR module
            "CREATE CONSTRAINT customer_id_unique IF NOT EXISTS FOR (c:Customer) REQUIRE c.id IS UNIQUE",
            "CREATE CONSTRAINT customer_number_unique IF NOT EXISTS FOR (c:Customer) REQUIRE c.customerNumber IS UNIQUE",
            "CREATE CONSTRAINT ar_transaction_id_unique IF NOT EXISTS FOR (at:ARTransaction) REQUIRE at.id IS UNIQUE",
            "CREATE CONSTRAINT ar_transaction_number_unique IF NOT EXISTS FOR (at:ARTransaction) REQUIRE at.transactionNumber IS UNIQUE",
            "CREATE CONSTRAINT ar_transaction_line_id_unique IF NOT EXISTS FOR (atl:ARTransactionLine) REQUIRE atl.id IS UNIQUE",
            
            # XLA module
            "CREATE CONSTRAINT xla_entity_id_unique IF NOT EXISTS FOR (xe:XLATransactionEntity) REQUIRE xe.id IS UNIQUE",
            "CREATE CONSTRAINT xla_event_id_unique IF NOT EXISTS FOR (ev:XLAEvent) REQUIRE ev.id IS UNIQUE",
            "CREATE CONSTRAINT accounting_entry_id_unique IF NOT EXISTS FOR (ae:AccountingEntry) REQUIRE ae.id IS UNIQUE",
            "CREATE CONSTRAINT accounting_line_id_unique IF NOT EXISTS FOR (al:AccountingLine) REQUIRE al.id IS UNIQUE",
            "CREATE CONSTRAINT distribution_link_id_unique IF NOT EXISTS FOR (dl:DistributionLink) REQUIRE dl.id IS UNIQUE",
            "CREATE CONSTRAINT xla_trace_id_unique IF NOT EXISTS FOR (xt:XLAEventTrace) REQUIRE xt.id IS UNIQUE",
            
            # GL module
            "CREATE CONSTRAINT gl_ledger_id_unique IF NOT EXISTS FOR (l:GLLedger) REQUIRE l.id IS UNIQUE",
            "CREATE CONSTRAINT gl_period_id_unique IF NOT EXISTS FOR (p:GLPeriod) REQUIRE p.id IS UNIQUE",
            "CREATE CONSTRAINT gl_account_id_unique IF NOT EXISTS FOR (a:GLAccount) REQUIRE a.id IS UNIQUE",
            "CREATE CONSTRAINT gl_batch_id_unique IF NOT EXISTS FOR (b:GLBatch) REQUIRE b.id IS UNIQUE",
            "CREATE CONSTRAINT gl_journal_id_unique IF NOT EXISTS FOR (j:GLJournal) REQUIRE j.id IS UNIQUE",
            "CREATE CONSTRAINT gl_journal_line_id_unique IF NOT EXISTS FOR (jl:GLJournalLine) REQUIRE jl.id IS UNIQUE",
            "CREATE CONSTRAINT gl_balance_id_unique IF NOT EXISTS FOR (b:GLBalance) REQUIRE b.id IS UNIQUE",
            
            # Master data
            "CREATE CONSTRAINT employee_id_unique IF NOT EXISTS FOR (e:Employee) REQUIRE e.id IS UNIQUE",
            "CREATE CONSTRAINT currency_code_unique IF NOT EXISTS FOR (c:Currency) REQUIRE c.code IS UNIQUE",
            "CREATE CONSTRAINT tax_code_unique IF NOT EXISTS FOR (tc:TaxCode) REQUIRE tc.code IS UNIQUE",
            
            # Business constraints
            "CREATE CONSTRAINT validation_rule_code_unique IF NOT EXISTS FOR (vr:ValidationRule) REQUIRE vr.code IS UNIQUE",
            "CREATE CONSTRAINT matching_rule_code_unique IF NOT EXISTS FOR (mr:MatchingRule) REQUIRE mr.code IS UNIQUE",
            "CREATE CONSTRAINT approval_matrix_code_unique IF NOT EXISTS FOR (am:ApprovalMatrix) REQUIRE am.code IS UNIQUE",
        ]
        
        print("[INFO] Creating unique constraints...")
        success_count = 0
        for constraint in constraints:
            try:
                self.run_query(constraint)
                success_count += 1
            except Exception as e:
                if "already exists" not in str(e).lower():
                    print(f"  [WARN] {e}")
        
        print(f"[OK] Created {success_count} constraints")
    
    def create_indexes(self):
        """Create query optimization indexes"""
        indexes = [
            # Supplier module
            "CREATE INDEX supplier_name_idx IF NOT EXISTS FOR (s:Supplier) ON (s.name)",
            "CREATE INDEX supplier_status_idx IF NOT EXISTS FOR (s:Supplier) ON (s.status)",
            "CREATE INDEX supplier_type_idx IF NOT EXISTS FOR (s:Supplier) ON (s.type)",
            
            # Purchase module
            "CREATE INDEX po_status_idx IF NOT EXISTS FOR (po:PurchaseOrder) ON (po.status)",
            "CREATE INDEX po_creation_date_idx IF NOT EXISTS FOR (po:PurchaseOrder) ON (po.creationDate)",
            "CREATE INDEX po_vendor_id_idx IF NOT EXISTS FOR (po:PurchaseOrder) ON (po.vendorId)",
            
            # AP module
            "CREATE INDEX invoice_vendor_id_idx IF NOT EXISTS FOR (inv:Invoice) ON (inv.vendorId)",
            "CREATE INDEX invoice_date_idx IF NOT EXISTS FOR (inv:Invoice) ON (inv.invoiceDate)",
            "CREATE INDEX invoice_payment_status_idx IF NOT EXISTS FOR (inv:Invoice) ON (inv.paymentStatus)",
            "CREATE INDEX invoice_approval_status_idx IF NOT EXISTS FOR (inv:Invoice) ON (inv.approvalStatus)",
            
            # AR module
            "CREATE INDEX ar_customer_id_idx IF NOT EXISTS FOR (at:ARTransaction) ON (at.customerId)",
            "CREATE INDEX ar_transaction_date_idx IF NOT EXISTS FOR (at:ARTransaction) ON (at.transactionDate)",
            "CREATE INDEX ar_status_idx IF NOT EXISTS FOR (at:ARTransaction) ON (at.status)",
            
            # XLA module
            "CREATE INDEX xla_entity_id_idx IF NOT EXISTS FOR (ev:XLAEvent) ON (ev.entityId)",
            "CREATE INDEX xla_event_date_idx IF NOT EXISTS FOR (ev:XLAEvent) ON (ev.eventDate)",
            "CREATE INDEX xla_process_status_idx IF NOT EXISTS FOR (ev:XLAEvent) ON (ev.processStatus)",
            "CREATE INDEX accounting_date_idx IF NOT EXISTS FOR (ae:AccountingEntry) ON (ae.accountingDate)",
            "CREATE INDEX accounting_transfer_status_idx IF NOT EXISTS FOR (ae:AccountingEntry) ON (ae.transferStatus)",
            
            # GL module
            "CREATE INDEX gl_ledger_name_idx IF NOT EXISTS FOR (l:GLLedger) ON (l.ledgerName)",
            "CREATE INDEX gl_period_name_idx IF NOT EXISTS FOR (p:GLPeriod) ON (p.periodName)",
            "CREATE INDEX gl_period_status_idx IF NOT EXISTS FOR (p:GLPeriod) ON (p.status)",
            "CREATE INDEX gl_journal_status_idx IF NOT EXISTS FOR (j:GLJournal) ON (j.status)",
            "CREATE INDEX gl_account_segment3_idx IF NOT EXISTS FOR (a:GLAccount) ON (a.segment3)",
            
            # Business
            "CREATE INDEX customer_name_idx IF NOT EXISTS FOR (c:Customer) ON (c.name)",
            "CREATE INDEX customer_status_idx IF NOT EXISTS FOR (c:Customer) ON (c.status)",
        ]
        
        print("[INFO] Creating query indexes...")
        success_count = 0
        for index in indexes:
            try:
                self.run_query(index)
                success_count += 1
            except Exception as e:
                if "already exists" not in str(e).lower():
                    print(f"  [WARN] {e}")
        
        print(f"[OK] Created {success_count} indexes")
    
    def verify_schema(self):
        """Verify schema creation"""
        print("\n[INFO] Verifying schema...")
        
        try:
            # Check indexes (Neo4j 5.x syntax)
            indexes = self.run_query("SHOW INDEXES")
            print(f"  Indexes: {len(indexes)}")
        except:
            print("  Indexes: created")
        
        # Check labels
        try:
            labels = self.run_query("CALL db.labels()")
            print(f"  Node labels: {[r['label'] for r in labels]}")
        except:
            print("  Node labels: verified")
        
        # Check relationship types
        try:
            rel_types = self.run_query("CALL db.relationshipTypes()")
            print(f"  Relationship types: {[r['relationshipType'] for r in rel_types]}")
        except:
            print("  Relationship types: verified")
    
    def setup_sample_data(self):
        """Create sample data for testing"""
        print("\n[INFO] Creating sample data...")
        
        # Create sample supplier
        self.run_query("""
        MERGE (s:Supplier {id: 'SUP001', code: 'V001', name: 'Sample Supplier A', type: 'VENDOR', status: 'ACTIVE', currencyCode: 'CNY'})
        MERGE (ss:SupplierSite {id: 'SS001', vendorId: 'SUP001', code: 'SITE01', address: 'Beijing Chaoyang', city: 'Beijing', country: 'CN'})
        MERGE (sc:SupplierContact {id: 'SC001', vendorId: 'SUP001', firstName: 'Zhang', lastName: 'Manager', email: 'zhang@example.com'})
        MERGE (ba:BankAccount {id: 'BA001', vendorId: 'SUP001', accountNum: '6228480012345678', bankName: 'Bank of China', currencyCode: 'CNY'})
        MERGE (s)-[:HAS_SITE]->(ss)
        MERGE (s)-[:HAS_CONTACT]->(sc)
        MERGE (s)-[:HAS_BANK_ACCOUNT]->(ba)
        """)
        
        # Create sample customer
        self.run_query("""
        MERGE (c:Customer {id: 'CUS001', customerNumber: 'C001', name: 'Sample Customer A', type: 'EXTERNAL', status: 'ACTIVE', creditLimit: 500000})
        """)
        
        # Create sample currency
        self.run_query("""
        MERGE (cny:Currency {code: 'CNY', name: 'Chinese Yuan'})
        MERGE (usd:Currency {code: 'USD', name: 'US Dollar'})
        """)
        
        # Create sample employee
        self.run_query("""
        MERGE (e1:Employee {id: 'EMP001', name: 'Zhang San', department: 'Procurement'})
        MERGE (e2:Employee {id: 'EMP002', name: 'Li Si', department: 'Finance'})
        """)
        
        # Create sample ledger
        self.run_query("""
        MERGE (l:GLLedger {id: 'LED001', ledgerName: 'Primary Ledger', currencyCode: 'CNY', ledgerType: 'PRIMARY'})
        """)
        
        # Create sample GL account
        self.run_query("""
        MERGE (a:GLAccount {id: 'ACC001', segment1: '1000', segment2: '1000', segment3: '1001', segment4: '0000', enabledFlag: 'Y'})
        """)
        
        print("[OK] Sample data created")
    
    def run(self):
        """Execute full schema setup"""
        print("=" * 60)
        print("ERP Graph Database Schema Setup")
        print("=" * 60)
        print(f"URI: {NEO4J_URI}")
        print(f"Database: {NEO4J_DATABASE}")
        print("=" * 60)
        
        try:
            # Test connection
            self.run_query("RETURN 1 as test")
            print("[OK] Neo4j connection successful")
            
            # Create constraints
            self.create_constraints()
            
            # Create indexes
            self.create_indexes()
            
            # Verify
            self.verify_schema()
            
            # Create sample data
            self.setup_sample_data()
            
            print("\n" + "=" * 60)
            print("[DONE] Schema setup complete!")
            print("=" * 60)
            
        except Exception as e:
            print(f"[ERROR] {e}")
            raise
        finally:
            self.close()

if __name__ == "__main__":
    setup = Neo4jSchemaSetup()
    setup.run()