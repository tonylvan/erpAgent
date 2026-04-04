#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
EBS 关系表同步到 Neo4j - 新增表同步脚本
同步新增的 35 张关系表到 Neo4j 图数据库
"""

import psycopg2
from neo4j import GraphDatabase
from datetime import datetime
import sys
import os

# 数据库配置
POSTGRES_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'erp',
    'user': 'postgres',
    'password': 'postgres'
}

NEO4J_URI = 'bolt://127.0.0.1:7687'
NEO4J_USER = 'neo4j'
NEO4J_PASSWORD = 'Tony1985'

class EBSRelationshipSync:
    def __init__(self):
        self.pg_conn = None
        self.neo4j_driver = None
        
    def connect(self):
        """连接数据库"""
        print("=" * 60)
        print("EBS 关系表同步到 Neo4j")
        print("=" * 60)
        
        print("\n[1/2] 连接 PostgreSQL...")
        self.pg_conn = psycopg2.connect(**POSTGRES_CONFIG)
        print("[OK] PostgreSQL 连接成功")
        
        print("\n[2/2] 连接 Neo4j...")
        self.neo4j_driver = GraphDatabase.driver(
            NEO4J_URI,
            auth=(NEO4J_USER, NEO4J_PASSWORD)
        )
        print("[OK] Neo4j 连接成功")
        
    def disconnect(self):
        """断开连接"""
        if self.pg_conn:
            self.pg_conn.close()
        if self.neo4j_driver:
            self.neo4j_driver.close()
            
    def clear_existing_relationships(self):
        """清理现有关系（可选）"""
        print("\n" + "=" * 60)
        print("清理现有关系")
        print("=" * 60)
        
        with self.neo4j_driver.session() as session:
            # 删除所有关系（保留节点）
            result = session.run("""
                MATCH ()-[r]-()
                DELETE r
                RETURN count(r) as deleted_count
            """)
            record = result.single()
            count = record['deleted_count'] if record else 0
            print(f"已删除 {count} 个关系")
            
    def sync_ap_relationships(self):
        """同步 AP 模块关系"""
        print("\n" + "=" * 60)
        print("[AP] 同步应付模块关系")
        print("=" * 60)
        
        with self.pg_conn.cursor() as pg_cur, self.neo4j_driver.session() as neo4j_session:
            # 1. 发票与 PO 匹配关系
            print("\n[AP-1] 同步发票与 PO 匹配关系...")
            pg_cur.execute("""
                SELECT match_id, invoice_id, po_line_id, matched_amount, match_date, match_type
                FROM ap_invoice_po_matches
                WHERE invoice_id IS NOT NULL AND po_line_id IS NOT NULL
            """)
            
            count = 0
            for row in pg_cur.fetchall():
                neo4j_session.run("""
                    MATCH (inv:APInvoice {invoice_id: $invoice_id})
                    MATCH (pol:POLine {po_line_id: $po_line_id})
                    MERGE (inv)-[r:MATCHES_PO_LINE]->(pol)
                    SET r.match_id = $match_id,
                        r.matched_amount = $matched_amount,
                        r.match_type = $match_type,
                        r.synced_at = datetime()
                """, {
                    'invoice_id': row[1],
                    'po_line_id': row[2],
                    'match_id': row[0],
                    'matched_amount': float(row[3]) if row[3] else None,
                    'match_type': row[5]
                })
                count += 1
            
            print(f"[OK] 同步 {count} 条发票 -PO 匹配关系")
            
            # 2. 发票与总账接口
            print("\n[AP-2] 同步发票与总账接口关系...")
            pg_cur.execute("""
                SELECT interface_id, invoice_id, gl_batch_name, status
                FROM ap_gl_interface
                WHERE invoice_id IS NOT NULL
            """)
            
            count = 0
            for row in pg_cur.fetchall():
                neo4j_session.run("""
                    MATCH (inv:APInvoice {invoice_id: $invoice_id})
                    MERGE (gl:GLInterface {interface_id: $interface_id})
                    MERGE (inv)-[r:POSTS_TO_GL]->(gl)
                    SET gl.batch_name = $batch_name,
                        gl.status = $status,
                        r.synced_at = datetime()
                """, {
                    'invoice_id': row[1],
                    'interface_id': row[0],
                    'batch_name': row[2],
                    'status': row[3]
                })
                count += 1
            
            print(f"[OK] 同步 {count} 条发票 - 总账接口关系")
            
    def sync_po_relationships(self):
        """同步 PO 模块关系"""
        print("\n" + "=" * 60)
        print("[PO] 同步采购模块关系")
        print("=" * 60)
        
        with self.pg_conn.cursor() as pg_cur, self.neo4j_driver.session() as neo4j_session:
            # 1. 采购申请与 PO 关联
            print("\n[PO-1] 同步采购申请与 PO 关联...")
            pg_cur.execute("""
                SELECT req_link_id, requisition_line_id, po_line_id, linked_amount, status
                FROM po_requisition_links
                WHERE requisition_line_id IS NOT NULL AND po_line_id IS NOT NULL
            """)
            
            count = 0
            for row in pg_cur.fetchall():
                neo4j_session.run("""
                    MATCH (req:RequisitionLine {requisition_line_id: $req_line_id})
                    MATCH (pol:POLine {po_line_id: $po_line_id})
                    MERGE (req)-[r:CONVERTS_TO_PO_LINE]->(pol)
                    SET r.req_link_id = $req_link_id,
                        r.linked_amount = $linked_amount,
                        r.status = $status,
                        r.synced_at = datetime()
                """, {
                    'req_line_id': row[1],
                    'po_line_id': row[2],
                    'req_link_id': row[0],
                    'linked_amount': float(row[3]) if row[3] else None,
                    'status': row[4]
                })
                count += 1
            
            print(f"[OK] 同步 {count} 条申请-PO 转换关系")
            
            # 2. 采购订单审批历史
            print("\n[PO-2] 同步采购订单审批关系...")
            pg_cur.execute("""
                SELECT approval_id, po_header_id, approver_id, approval_status, approval_date
                FROM po_approval_history
                WHERE po_header_id IS NOT NULL AND approver_id IS NOT NULL
            """)
            
            count = 0
            for row in pg_cur.fetchall():
                neo4j_session.run("""
                    MATCH (po:PurchaseOrder {po_header_id: $po_header_id})
                    MATCH (emp:Employee {employee_id: $approver_id})
                    MERGE (po)-[r:APPROVED_BY]->(emp)
                    SET r.approval_id = $approval_id,
                        r.approval_status = $approval_status,
                        r.approval_date = $approval_date,
                        r.synced_at = datetime()
                """, {
                    'po_header_id': row[1],
                    'approver_id': row[2],
                    'approval_id': row[0],
                    'approval_status': row[3],
                    'approval_date': row[4]
                })
                count += 1
            
            print(f"[OK] 同步 {count} 条 PO 审批关系")
            
    def sync_gl_relationships(self):
        """同步 GL 模块关系"""
        print("\n" + "=" * 60)
        print("[GL] 同步总账模块关系")
        print("=" * 60)
        
        with self.pg_conn.cursor() as pg_cur, self.neo4j_driver.session() as neo4j_session:
            # 1. 总账日记账行
            print("\n[GL-1] 同步总账日记账关系...")
            pg_cur.execute("""
                SELECT line_id, je_header_id, code_combination_id, dr_amount, cr_amount
                FROM gl_journal_lines
                WHERE je_header_id IS NOT NULL
            """)
            
            count = 0
            for row in pg_cur.fetchall():
                neo4j_session.run("""
                    MATCH (journal:GLJournal {je_header_id: $je_header_id})
                    MATCH (account:GLAccount {code_combination_id: $code_combination_id})
                    MERGE (journal)-[r:CONTAINS_LINE]->(line:GLJournalLine {line_id: $line_id})
                    SET line.dr_amount = $dr_amount,
                        line.cr_amount = $cr_amount,
                        r.synced_at = datetime()
                """, {
                    'je_header_id': row[1],
                    'line_id': row[0],
                    'code_combination_id': row[2],
                    'dr_amount': float(row[3]) if row[3] else None,
                    'cr_amount': float(row[4]) if row[4] else None
                })
                count += 1
            
            print(f"[OK] 同步 {count} 条日记账行关系")
            
            # 2. 总账余额
            print("\n[GL-2] 同步总账余额关系...")
            pg_cur.execute("""
                SELECT balance_id, code_combination_id, period_name, end_balance
                FROM gl_balances
                WHERE code_combination_id IS NOT NULL
            """)
            
            count = 0
            for row in pg_cur.fetchall():
                neo4j_session.run("""
                    MATCH (account:GLAccount {code_combination_id: $code_combination_id})
                    MERGE (account)-[r:HAS_BALANCE]->(balance:GLBalance {balance_id: $balance_id})
                    SET balance.end_balance = $end_balance,
                        balance.period_name = $period_name,
                        r.synced_at = datetime()
                """, {
                    'code_combination_id': row[1],
                    'balance_id': row[0],
                    'period_name': row[2],
                    'end_balance': float(row[3]) if row[3] else None
                })
                count += 1
            
            print(f"[OK] 同步 {count} 条余额关系")
            
            # 3. 科目组合段
            print("\n[GL-3] 同步科目组合段关系...")
            pg_cur.execute("""
                SELECT segment_id, code_combination_id, segment_num, segment_name, segment_value
                FROM gl_code_combination_segments
                WHERE code_combination_id IS NOT NULL
            """)
            
            count = 0
            for row in pg_cur.fetchall():
                neo4j_session.run("""
                    MATCH (account:GLAccount {code_combination_id: $code_combination_id})
                    MERGE (account)-[r:HAS_SEGMENT]->(segment:GLSegment {segment_id: $segment_id})
                    SET segment.segment_num = $segment_num,
                        segment.segment_name = $segment_name,
                        segment.segment_value = $segment_value,
                        r.synced_at = datetime()
                """, {
                    'code_combination_id': row[1],
                    'segment_id': row[0],
                    'segment_num': row[2],
                    'segment_name': row[3],
                    'segment_value': row[4]
                })
                count += 1
            
            print(f"[OK] 同步 {count} 条科目段关系")
            
    def sync_ar_relationships(self):
        """同步 AR 模块关系"""
        print("\n" + "=" * 60)
        print("[AR] 同步应收模块关系")
        print("=" * 60)
        
        with self.pg_conn.cursor() as pg_cur, self.neo4j_driver.session() as neo4j_session:
            # 1. 收款与发票应用
            print("\n[AR-1] 同步收款与发票应用关系...")
            pg_cur.execute("""
                SELECT application_id, receipt_id, invoice_id, applied_amount, application_date
                FROM ar_receipt_applications_extended
                WHERE receipt_id IS NOT NULL AND invoice_id IS NOT NULL
            """)
            
            count = 0
            for row in pg_cur.fetchall():
                neo4j_session.run("""
                    MATCH (receipt:ARReceipt {receipt_id: $receipt_id})
                    MATCH (invoice:ARInvoice {invoice_id: $invoice_id})
                    MERGE (receipt)-[r:APPLIED_TO]->(invoice)
                    SET r.application_id = $application_id,
                        r.applied_amount = $applied_amount,
                        r.application_date = $application_date,
                        r.synced_at = datetime()
                """, {
                    'receipt_id': row[1],
                    'invoice_id': row[2],
                    'application_id': row[0],
                    'applied_amount': float(row[3]) if row[3] else None,
                    'application_date': row[4]
                })
                count += 1
            
            print(f"[OK] 同步 {count} 条收款 - 发票应用关系")
            
            # 2. 客户与配置
            print("\n[AR-2] 同步客户配置关系...")
            pg_cur.execute("""
                SELECT profile_id, customer_id, credit_limit, payment_terms_id
                FROM ar_customer_profiles_extended
                WHERE customer_id IS NOT NULL
            """)
            
            count = 0
            for row in pg_cur.fetchall():
                neo4j_session.run("""
                    MATCH (cust:Customer {customer_id: $customer_id})
                    MERGE (cust)-[r:HAS_PROFILE]->(profile:CustomerProfile {profile_id: $profile_id})
                    SET profile.credit_limit = $credit_limit,
                        profile.payment_terms_id = $payment_terms_id,
                        r.synced_at = datetime()
                """, {
                    'customer_id': row[1],
                    'profile_id': row[0],
                    'credit_limit': float(row[2]) if row[2] else None,
                    'payment_terms_id': row[3]
                })
                count += 1
            
            print(f"[OK] 同步 {count} 条客户配置关系")
            
            # 3. 客户余额
            print("\n[AR-3] 同步客户余额关系...")
            pg_cur.execute("""
                SELECT balance_id, customer_id, outstanding_balance, balance_date
                FROM ar_customer_balances
                WHERE customer_id IS NOT NULL
            """)
            
            count = 0
            for row in pg_cur.fetchall():
                neo4j_session.run("""
                    MATCH (cust:Customer {customer_id: $customer_id})
                    MERGE (cust)-[r:HAS_BALANCE]->(balance:ARCustomerBalance {balance_id: $balance_id})
                    SET balance.outstanding_balance = $outstanding_balance,
                        balance.balance_date = $balance_date,
                        r.synced_at = datetime()
                """, {
                    'customer_id': row[1],
                    'balance_id': row[0],
                    'outstanding_balance': float(row[2]) if row[2] else None,
                    'balance_date': row[3]
                })
                count += 1
            
            print(f"[OK] 同步 {count} 条客户余额关系")
            
            # 4. 催收案例
            print("\n[AR-4] 同步催收案例关系...")
            pg_cur.execute("""
                SELECT case_id, customer_id, invoice_id, case_status, priority, total_amount
                FROM ar_collection_cases
                WHERE customer_id IS NOT NULL
            """)
            
            count = 0
            for row in pg_cur.fetchall():
                neo4j_session.run("""
                    MATCH (cust:Customer {customer_id: $customer_id})
                    MERGE (cust)-[r:HAS_COLLECTION_CASE]->(case:CollectionCase {case_id: $case_id})
                    SET case.case_status = $case_status,
                        case.priority = $priority,
                        case.total_amount = $total_amount,
                        r.synced_at = datetime()
                """, {
                    'customer_id': row[1],
                    'case_id': row[0],
                    'case_status': row[3],
                    'priority': row[4],
                    'total_amount': float(row[5]) if row[5] else None
                })
                count += 1
            
            print(f"[OK] 同步 {count} 条催收案例关系")
            
    def sync_inv_relationships(self):
        """同步 INV 模块关系"""
        print("\n" + "=" * 60)
        print("[INV] 同步库存模块关系")
        print("=" * 60)
        
        with self.pg_conn.cursor() as pg_cur, self.neo4j_driver.session() as neo4j_session:
            # 1. 组织与子库存
            print("\n[INV-1] 同步组织与子库存关系...")
            pg_cur.execute("""
                SELECT subinv_id, organization_id, subinventory_code, description
                FROM inv_subinventories_extended
                WHERE organization_id IS NOT NULL
            """)
            
            count = 0
            for row in pg_cur.fetchall():
                neo4j_session.run("""
                    MATCH (org:Organization {organization_id: $organization_id})
                    MERGE (org)-[r:HAS_SUBINVENTORY]->(subinv:Subinventory {subinv_id: $subinv_id})
                    SET subinv.subinventory_code = $subinventory_code,
                        subinv.description = $description,
                        r.synced_at = datetime()
                """, {
                    'organization_id': row[1],
                    'subinv_id': row[0],
                    'subinventory_code': row[2],
                    'description': row[3]
                })
                count += 1
            
            print(f"[OK] 同步 {count} 条组织 - 子库存关系")
            
            # 2. 子库存与货位
            print("\n[INV-2] 同步子库存与货位关系...")
            pg_cur.execute("""
                SELECT locator_id, subinventory_id, locator_code, segment1, segment2
                FROM inv_item_locators_extended
                WHERE subinventory_id IS NOT NULL
            """)
            
            count = 0
            for row in pg_cur.fetchall():
                neo4j_session.run("""
                    MATCH (subinv:Subinventory {subinv_id: $subinventory_id})
                    MERGE (subinv)-[r:HAS_LOCATOR]->(locator:ItemLocator {locator_id: $locator_id})
                    SET locator.locator_code = $locator_code,
                        locator.segment1 = $segment1,
                        locator.segment2 = $segment2,
                        r.synced_at = datetime()
                """, {
                    'subinventory_id': row[1],
                    'locator_id': row[0],
                    'locator_code': row[2],
                    'segment1': row[3],
                    'segment2': row[4]
                })
                count += 1
            
            print(f"[OK] 同步 {count} 条子库存 - 货位关系")
            
            # 3. 物料与批次
            print("\n[INV-3] 同步物料与批次关系...")
            pg_cur.execute("""
                SELECT lot_id, item_id, lot_number, generation_date, expiration_date
                FROM inv_lot_numbers_extended
                WHERE item_id IS NOT NULL
            """)
            
            count = 0
            for row in pg_cur.fetchall():
                neo4j_session.run("""
                    MATCH (item:Item {item_id: $item_id})
                    MERGE (item)-[r:HAS_LOT]->(lot:LotNumber {lot_id: $lot_id})
                    SET lot.lot_number = $lot_number,
                        lot.generation_date = $generation_date,
                        lot.expiration_date = $expiration_date,
                        r.synced_at = datetime()
                """, {
                    'item_id': row[1],
                    'lot_id': row[0],
                    'lot_number': row[2],
                    'generation_date': row[3],
                    'expiration_date': row[4]
                })
                count += 1
            
            print(f"[OK] 同步 {count} 条物料 - 批次关系")
            
            # 4. 物料与序列号
            print("\n[INV-4] 同步物料与序列号关系...")
            pg_cur.execute("""
                SELECT serial_id, item_id, serial_number, status
                FROM inv_serial_numbers_extended
                WHERE item_id IS NOT NULL
            """)
            
            count = 0
            for row in pg_cur.fetchall():
                neo4j_session.run("""
                    MATCH (item:Item {item_id: $item_id})
                    MERGE (item)-[r:HAS_SERIAL]->(serial:SerialNumber {serial_id: $serial_id})
                    SET serial.serial_number = $serial_number,
                        serial.status = $status,
                        r.synced_at = datetime()
                """, {
                    'item_id': row[1],
                    'serial_id': row[0],
                    'serial_number': row[2],
                    'status': row[3]
                })
                count += 1
            
            print(f"[OK] 同步 {count} 条物料 - 序列号关系")
            
    def sync_om_relationships(self):
        """同步 OM 模块关系"""
        print("\n" + "=" * 60)
        print("[OM] 同步销售模块关系")
        print("=" * 60)
        
        with self.pg_conn.cursor() as pg_cur, self.neo4j_driver.session() as neo4j_session:
            # 1. 发运与订单明细
            print("\n[OM-1] 同步发运与订单明细关系...")
            pg_cur.execute("""
                SELECT shipment_detail_id, shipment_id, order_line_id, shipped_quantity, status
                FROM om_shipment_details_extended
                WHERE shipment_id IS NOT NULL AND order_line_id IS NOT NULL
            """)
            
            count = 0
            for row in pg_cur.fetchall():
                neo4j_session.run("""
                    MATCH (shipment:Shipment {shipment_id: $shipment_id})
                    MATCH (orderline:OrderLine {order_line_id: $order_line_id})
                    MERGE (shipment)-[r:CONTAINS_DETAIL]->(detail:ShipmentDetail {shipment_detail_id: $shipment_detail_id})
                    SET detail.shipped_quantity = $shipped_quantity,
                        detail.status = $status,
                        r.synced_at = datetime()
                """, {
                    'shipment_id': row[1],
                    'order_line_id': row[2],
                    'shipment_detail_id': row[0],
                    'shipped_quantity': float(row[3]) if row[3] else None,
                    'status': row[4]
                })
                count += 1
            
            print(f"[OK] 同步 {count} 条发运 - 订单明细关系")
            
            # 2. 订单预留
            print("\n[OM-2] 同步订单预留关系...")
            pg_cur.execute("""
                SELECT reservation_id, order_line_id, item_id, reserved_quantity, status
                FROM om_order_reservations
                WHERE order_line_id IS NOT NULL AND item_id IS NOT NULL
            """)
            
            count = 0
            for row in pg_cur.fetchall():
                neo4j_session.run("""
                    MATCH (orderline:OrderLine {order_line_id: $order_line_id})
                    MATCH (item:Item {item_id: $item_id})
                    MERGE (orderline)-[r:RESERVES]->(reservation:OrderReservation {reservation_id: $reservation_id})
                    SET reservation.reserved_quantity = $reserved_quantity,
                        reservation.status = $status,
                        r.synced_at = datetime()
                """, {
                    'order_line_id': row[1],
                    'item_id': row[2],
                    'reservation_id': row[0],
                    'reserved_quantity': float(row[3]) if row[3] else None,
                    'status': row[4]
                })
                count += 1
            
            print(f"[OK] 同步 {count} 条订单预留关系")
            
            # 3. 价格列表
            print("\n[OM-3] 同步价格列表关系...")
            pg_cur.execute("""
                SELECT price_list_id, price_list_name, currency_code, price_type
                FROM om_price_lists_extended
                WHERE price_list_id IS NOT NULL
            """)
            
            count = 0
            for row in pg_cur.fetchall():
                neo4j_session.run("""
                    CREATE (price_list:PriceList {
                        price_list_id: $price_list_id,
                        price_list_name: $price_list_name,
                        currency_code: $currency_code,
                        price_type: $price_type
                    })
                """, {
                    'price_list_id': row[0],
                    'price_list_name': row[1],
                    'currency_code': row[2],
                    'price_type': row[3]
                })
                count += 1
            
            print(f"[OK] 创建 {count} 个价格列表节点")
            
    def get_statistics(self):
        """获取同步统计"""
        print("\n" + "=" * 60)
        print("同步统计")
        print("=" * 60)
        
        with self.neo4j_driver.session() as session:
            # 节点统计
            result = session.run("""
                MATCH (n)
                RETURN labels(n)[0] as label, count(n) as count
                ORDER BY count DESC
            """)
            
            print("\n[节点统计]")
            for record in result:
                print(f"  {record['label']}: {record['count']}")
            
            # 关系统计
            result = session.run("""
                MATCH ()-[r]->()
                RETURN type(r) as type, count(r) as count
                ORDER BY count DESC
            """)
            
            print("\n[关系统计]")
            for record in result:
                print(f"  {record['type']}: {record['count']}")
            
    def run(self):
        """执行同步"""
        try:
            self.connect()
            
            # 可选：清理现有关系
            # self.clear_existing_relationships()
            
            # 同步各模块关系
            self.sync_ap_relationships()
            self.sync_po_relationships()
            self.sync_gl_relationships()
            self.sync_ar_relationships()
            self.sync_inv_relationships()
            self.sync_om_relationships()
            
            # 显示统计
            self.get_statistics()
            
            print("\n" + "=" * 60)
            print("[SUCCESS] 所有关系同步完成！")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n[ERROR] 同步失败：{e}")
            import traceback
            traceback.print_exc()
            return False
        finally:
            self.disconnect()
        
        return True


if __name__ == '__main__':
    syncer = EBSRelationshipSync()
    success = syncer.run()
    sys.exit(0 if success else 1)
