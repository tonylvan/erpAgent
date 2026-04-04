#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Oracle EBS 表关系同步到 Neo4j
同步 PostgreSQL 中的关系数据到 Neo4j 图数据库
"""

import psycopg2
from neo4j import GraphDatabase
from datetime import datetime

# 数据库配置
POSTGRES_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'erp',
    'user': 'postgres',
    'password': 'postgres'
}

NEO4J_CONFIG = {
    'uri': 'bolt://127.0.0.1:7687',
    'user': 'neo4j',
    'password': 'Tony1985'
}

class EBSSyncService:
    def __init__(self):
        self.pg_conn = None
        self.neo4j_driver = None
        
    def connect(self):
        """连接数据库"""
        print("[INFO] 连接 PostgreSQL...")
        self.pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
        
        print("[INFO] 连接 Neo4j...")
        self.neo4j_driver = GraphDatabase.driver(**NEO4J_CONFIG)
        
    def disconnect(self):
        """断开连接"""
        if self.pg_conn:
            self.pg_conn.close()
        if self.neo4j_driver:
            self.neo4j_driver.close()
            
    def sync_ap_relationships(self):
        """同步 AP 模块关系"""
        print("\n[INFO] 同步 AP 模块关系...")
        
        with self.pg_conn.cursor() as pg_cur, self.neo4j_driver.session() as neo4j_session:
            # 1. 发票与 PO 匹配关系
            print("  - 同步发票与 PO 匹配关系...")
            pg_cur.execute("""
                SELECT m.match_id, m.invoice_id, m.po_line_id, m.matched_quantity, 
                       m.matched_amount, m.match_date, m.match_type
                FROM ap_invoice_po_matches m
            """)
            
            matches = pg_cur.fetchall()
            for match in matches:
                neo4j_session.run("""
                    MATCH (inv:APInvoice {invoice_id: $invoice_id})
                    MATCH (pol:POLine {po_line_id: $po_line_id})
                    MERGE (inv)-[r:MATCHES_PO_LINE]->(pol)
                    SET r.match_id = $match_id,
                        r.matched_quantity = $matched_quantity,
                        r.matched_amount = $matched_amount,
                        r.match_date = $match_date,
                        r.match_type = $match_type,
                        r.synced_at = datetime()
                """, {
                    'invoice_id': match[1],
                    'po_line_id': match[2],
                    'match_id': match[0],
                    'matched_quantity': float(match[3]) if match[3] else None,
                    'matched_amount': float(match[4]) if match[4] else None,
                    'match_date': match[5].isoformat() if match[5] else None,
                    'match_type': match[6]
                })
            
            # 2. 发票与总账接口
            print("  - 同步发票与总账接口...")
            pg_cur.execute("""
                SELECT interface_id, invoice_id, gl_batch_name, accounting_date,
                       dr_amount, cr_amount, status
                FROM ap_gl_interface
                WHERE status = 'POSTED'
            """)
            
            interfaces = pg_cur.fetchall()
            for interface in interfaces:
                neo4j_session.run("""
                    MATCH (inv:APInvoice {invoice_id: $invoice_id})
                    MERGE (inv)-[r:POSTS_TO_GL]->(gl:GLInterface {interface_id: $interface_id})
                    SET gl.batch_name = $batch_name,
                        gl.accounting_date = $accounting_date,
                        gl.dr_amount = $dr_amount,
                        gl.cr_amount = $cr_amount,
                        r.synced_at = datetime()
                """, {
                    'invoice_id': interface[1],
                    'interface_id': interface[0],
                    'batch_name': interface[2],
                    'accounting_date': interface[3].isoformat() if interface[3] else None,
                    'dr_amount': float(interface[4]) if interface[4] else 0,
                    'cr_amount': float(interface[5]) if interface[5] else 0
                })
            
            # 3. 付款与发票分配
            print("  - 同步付款与发票分配...")
            pg_cur.execute("""
                SELECT payment_dist_id, payment_id, invoice_id, amount, 
                       discount_amount, payment_date
                FROM ap_payment_invoice_dists
            """)
            
            payments = pg_cur.fetchall()
            for payment in payments:
                neo4j_session.run("""
                    MATCH (pay:Payment {payment_id: $payment_id})
                    MATCH (inv:APInvoice {invoice_id: $invoice_id})
                    MERGE (pay)-[r:APPLIED_TO]->(inv)
                    SET r.amount = $amount,
                        r.discount_amount = $discount_amount,
                        r.payment_date = $payment_date,
                        r.synced_at = datetime()
                """, {
                    'payment_id': payment[1],
                    'invoice_id': payment[2],
                    'amount': float(payment[3]) if payment[3] else 0,
                    'discount_amount': float(payment[4]) if payment[4] else 0,
                    'payment_date': payment[5].isoformat() if payment[5] else None
                })
                
    def sync_po_relationships(self):
        """同步 PO 模块关系"""
        print("\n[INFO] 同步 PO 模块关系...")
        
        with self.pg_conn.cursor() as pg_cur, self.neo4j_driver.session() as neo4j_session:
            # 1. 采购订单审批历史
            print("  - 同步 PO 审批历史...")
            pg_cur.execute("""
                SELECT approval_id, po_header_id, approver_id, approval_level,
                       approval_status, approval_date, comments
                FROM po_approval_history
            """)
            
            approvals = pg_cur.fetchall()
            for approval in approvals:
                neo4j_session.run("""
                    MATCH (po:PurchaseOrder {header_id: $po_header_id})
                    MATCH (emp:Employee {person_id: $approver_id})
                    MERGE (po)-[r:APPROVED_BY]->(emp)
                    SET r.approval_id = $approval_id,
                        r.approval_level = $approval_level,
                        r.approval_status = $approval_status,
                        r.approval_date = $approval_date,
                        r.comments = $comments,
                        r.synced_at = datetime()
                """, {
                    'po_header_id': approval[1],
                    'approver_id': approval[2],
                    'approval_id': approval[0],
                    'approval_level': approval[3],
                    'approval_status': approval[4],
                    'approval_date': approval[5].isoformat() if approval[5] else None,
                    'comments': approval[6]
                })
            
            # 2. 采购申请与 PO 关联
            print("  - 同步采购申请与 PO 关联...")
            pg_cur.execute("""
                SELECT req_link_id, requisition_line_id, po_line_id, 
                       linked_quantity, linked_amount
                FROM po_requisition_links
            """)
            
            links = pg_cur.fetchall()
            for link in links:
                neo4j_session.run("""
                    MATCH (req:RequisitionLine {requisition_line_id: $req_line_id})
                    MATCH (pol:POLine {po_line_id: $po_line_id})
                    MERGE (req)-[r:CONVERTS_TO_PO_LINE]->(pol)
                    SET r.linked_quantity = $linked_quantity,
                        r.linked_amount = $linked_amount,
                        r.synced_at = datetime()
                """, {
                    'req_line_id': link[1],
                    'po_line_id': link[2],
                    'linked_quantity': float(link[3]) if link[3] else None,
                    'linked_amount': float(link[4]) if link[4] else None
                })
                
    def sync_gl_relationships(self):
        """同步 GL 模块关系"""
        print("\n[INFO] 同步 GL 模块关系...")
        
        with self.pg_conn.cursor() as pg_cur, self.neo4j_driver.session() as neo4j_session:
            # 1. 总账日记账行
            print("  - 同步总账日记账行...")
            pg_cur.execute("""
                SELECT jl.line_id, jl.journal_id, jl.code_combination_id, 
                       jl.dr_amount, jl.cr_amount, jl.reference_type, jl.reference_id,
                       gcc.combined_string
                FROM gl_journal_lines jl
                LEFT JOIN gl_code_combinations gcc ON jl.code_combination_id = gcc.code_combination_id
            """)
            
            lines = pg_cur.fetchall()
            for line in lines:
                neo4j_session.run("""
                    MATCH (jr:GLJournal {journal_id: $journal_id})
                    MERGE (jr)-[r:CONTAINS_LINE]->(jl:GLJournalLine {line_id: $line_id})
                    SET jl.code_combination_id = $code_combination_id,
                        jl.account_combination = $account_comb,
                        jl.dr_amount = $dr_amount,
                        jl.cr_amount = $cr_amount,
                        jl.reference_type = $ref_type,
                        jl.reference_id = $ref_id,
                        r.synced_at = datetime()
                """, {
                    'journal_id': line[1],
                    'line_id': line[0],
                    'code_combination_id': line[2],
                    'account_comb': line[7],
                    'dr_amount': float(line[3]) if line[3] else 0,
                    'cr_amount': float(line[4]) if line[4] else 0,
                    'ref_type': line[5],
                    'ref_id': line[6]
                })
            
            # 2. 总账余额
            print("  - 同步总账余额...")
            pg_cur.execute("""
                SELECT balance_id, code_combination_id, period_name, actual_flag,
                       currency_code, end_balance_dr, end_balance_cr
                FROM gl_balances
                WHERE end_balance_dr != 0 OR end_balance_cr != 0
            """)
            
            balances = pg_cur.fetchall()
            for balance in balances:
                neo4j_session.run("""
                    MATCH (acc:GLAccount {code_combination_id: $ccid})
                    MERGE (acc)-[r:HAS_BALANCE]->(bal:GLBalance {balance_id: $balance_id})
                    SET bal.period_name = $period_name,
                        bal.actual_flag = $actual_flag,
                        bal.currency_code = $currency_code,
                        bal.end_balance_dr = $end_dr,
                        bal.end_balance_cr = $end_cr,
                        r.synced_at = datetime()
                """, {
                    'ccid': balance[1],
                    'balance_id': balance[0],
                    'period_name': balance[2],
                    'actual_flag': balance[3],
                    'currency_code': balance[4],
                    'end_dr': float(balance[5]) if balance[5] else 0,
                    'end_cr': float(balance[6]) if balance[6] else 0
                })
                
    def sync_ar_relationships(self):
        """同步 AR 模块关系"""
        print("\n[INFO] 同步 AR 模块关系...")
        
        with self.pg_conn.cursor() as pg_cur, self.neo4j_driver.session() as neo4j_session:
            # 1. 收款与发票应用
            print("  - 同步收款与发票应用...")
            pg_cur.execute("""
                SELECT application_id, receipt_id, invoice_id, applied_amount,
                       discount_amount, application_date, application_type
                FROM ar_receipt_applications
            """)
            
            applications = pg_cur.fetchall()
            for app in applications:
                neo4j_session.run("""
                    MATCH (rcpt:ARReceipt {receipt_id: $receipt_id})
                    MATCH (inv:ARInvoice {invoice_id: $invoice_id})
                    MERGE (rcpt)-[r:APPLIED_TO]->(inv)
                    SET r.applied_amount = $applied_amount,
                        r.discount_amount = $discount_amount,
                        r.application_date = $application_date,
                        r.application_type = $application_type,
                        r.synced_at = datetime()
                """, {
                    'receipt_id': app[1],
                    'invoice_id': app[2],
                    'application_id': app[0],
                    'applied_amount': float(app[3]) if app[3] else 0,
                    'discount_amount': float(app[4]) if app[4] else 0,
                    'application_date': app[5].isoformat() if app[5] else None,
                    'application_type': app[6]
                })
            
            # 2. 客户配置与余额
            print("  - 同步客户配置与余额...")
            pg_cur.execute("""
                SELECT p.profile_id, p.customer_id, p.credit_limit,
                       b.outstanding_balance, b.currency_code
                FROM ar_customer_profiles p
                LEFT JOIN ar_customer_balances b ON p.customer_id = b.customer_id
            """)
            
            profiles = pg_cur.fetchall()
            for profile in profiles:
                neo4j_session.run("""
                    MATCH (cust:Customer {customer_id: $customer_id})
                    MERGE (cust)-[r:HAS_PROFILE]->(prof:CustomerProfile {profile_id: $profile_id})
                    SET prof.credit_limit = $credit_limit,
                        prof.outstanding_balance = $outstanding_balance,
                        prof.currency_code = $currency_code,
                        r.synced_at = datetime()
                """, {
                    'customer_id': profile[1],
                    'profile_id': profile[0],
                    'credit_limit': float(profile[2]) if profile[2] else None,
                    'outstanding_balance': float(profile[3]) if profile[3] else 0,
                    'currency_code': profile[4]
                })
                
    def sync_inv_relationships(self):
        """同步 INV 模块关系"""
        print("\n[INFO] 同步 INV 模块关系...")
        
        with self.pg_conn.cursor() as pg_cur, self.neo4j_driver.session() as neo4j_session:
            # 1. 库存子库
            print("  - 同步库存子库...")
            pg_cur.execute("""
                SELECT subinventory_id, organization_id, subinventory_code, description
                FROM inv_subinventories
            """)
            
            subinvs = pg_cur.fetchall()
            for subinv in subinvs:
                neo4j_session.run("""
                    MATCH (org:Organization {organization_id: $org_id})
                    MERGE (org)-[r:HAS_SUBINVENTORY]->(sub:Subinventory {subinventory_id: $subinv_id})
                    SET sub.subinventory_code = $code,
                        sub.description = $description,
                        r.synced_at = datetime()
                """, {
                    'org_id': subinv[1],
                    'subinv_id': subinv[0],
                    'code': subinv[2],
                    'description': subinv[3]
                })
            
            # 2. 库存货位
            print("  - 同步库存货位...")
            pg_cur.execute("""
                SELECT locator_id, subinventory_id, combined_locator, status
                FROM inv_item_locators
            """)
            
            locators = pg_cur.fetchall()
            for locator in locators:
                neo4j_session.run("""
                    MATCH (sub:Subinventory {subinventory_id: $subinv_id})
                    MERGE (sub)-[r:HAS_LOCATOR]->(loc:ItemLocator {locator_id: $locator_id})
                    SET loc.combined_locator = $combined,
                        loc.status = $status,
                        r.synced_at = datetime()
                """, {
                    'subinv_id': locator[1],
                    'locator_id': locator[0],
                    'combined': locator[2],
                    'status': locator[3]
                })
                
    def sync_om_relationships(self):
        """同步 OM 模块关系"""
        print("\n[INFO] 同步 OM 模块关系...")
        
        with self.pg_conn.cursor() as pg_cur, self.neo4j_driver.session() as neo4j_session:
            # 1. 发运明细
            print("  - 同步发运明细...")
            pg_cur.execute("""
                SELECT shipment_detail_id, shipment_id, line_id, shipped_quantity,
                       ship_date, status
                FROM om_shipment_details
            """)
            
            shipments = pg_cur.fetchall()
            for ship in shipments:
                neo4j_session.run("""
                    MATCH (shp:Shipment {shipment_id: $shipment_id})
                    MATCH (line:OrderLine {line_id: $line_id})
                    MERGE (shp)-[r:CONTAINS_DETAIL]->(line)
                    SET r.shipped_quantity = $shipped_qty,
                        r.ship_date = $ship_date,
                        r.status = $status,
                        r.synced_at = datetime()
                """, {
                    'shipment_id': ship[1],
                    'line_id': ship[2],
                    'shipped_qty': float(ship[3]) if ship[3] else None,
                    'ship_date': ship[4].isoformat() if ship[4] else None,
                    'status': ship[5]
                })
            
            # 2. 订单预留
            print("  - 同步订单预留...")
            pg_cur.execute("""
                SELECT reservation_id, line_id, inventory_item_id, organization_id,
                       reserved_quantity, status
                FROM om_order_reservations
            """)
            
            reservations = pg_cur.fetchall()
            for res in reservations:
                neo4j_session.run("""
                    MATCH (line:OrderLine {line_id: $line_id})
                    MATCH (item:Item {inventory_item_id: $item_id})
                    MERGE (line)-[r:RESERVES]->(item)
                    SET r.reserved_quantity = $qty,
                        r.status = $status,
                        r.synced_at = datetime()
                """, {
                    'line_id': res[1],
                    'item_id': res[2],
                    'qty': float(res[4]) if res[4] else None,
                    'status': res[5]
                })
                
    def run_sync(self):
        """执行完整同步"""
        start_time = datetime.now()
        print(f"=" * 60)
        print(f"EBS 表关系同步开始：{start_time}")
        print(f"=" * 60)
        
        try:
            self.connect()
            
            # 执行各模块同步
            self.sync_ap_relationships()
            self.sync_po_relationships()
            self.sync_gl_relationships()
            self.sync_ar_relationships()
            self.sync_inv_relationships()
            self.sync_om_relationships()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            print(f"\n" + "=" * 60)
            print(f"✅ 同步完成！耗时：{duration:.2f}秒")
            print(f"=" * 60)
            
        except Exception as e:
            print(f"\n❌ 同步失败：{str(e)}")
            raise
        finally:
            self.disconnect()


if __name__ == '__main__':
    sync_service = EBSSyncService()
    sync_service.run_sync()
