#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GSD 智能问数 API v2.7 - EBS 关系扩展端点

新增 18 个端点，支持 AP/PO/GL/AR/INV/OM 模块的关系查询
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

# 数据库连接
from app.core.database import get_db
from app.core.config import postgres_config, neo4j_config
import psycopg2
from neo4j import GraphDatabase

router = APIRouter(tags=["智能问数 V2.7 - EBS 关系扩展"])


# ==================== 响应模型 ====================

class APInvoicePOMatch(BaseModel):
    match_id: int
    invoice_id: int
    po_line_id: int
    matched_amount: float
    match_type: str
    match_date: datetime


class GLJournalLine(BaseModel):
    line_id: int
    je_header_id: int
    code_combination_id: int
    dr_amount: float
    cr_amount: float


class GLBalance(BaseModel):
    balance_id: int
    code_combination_id: int
    period_name: str
    begin_balance: float
    debit: float
    credit: float
    end_balance: float


class ARCustomerBalance(BaseModel):
    balance_id: int
    customer_id: int
    balance_date: datetime
    currency_code: str
    outstanding_balance: float
    current_balance: float
    balance_1_30: float
    balance_31_60: float
    balance_61_90: float
    balance_over_90: float


class INVLocator(BaseModel):
    locator_id: int
    subinventory_id: int
    locator_code: str
    segment1: str
    segment2: str


class OMShipmentDetail(BaseModel):
    shipment_detail_id: int
    shipment_id: int
    order_line_id: int
    shipped_quantity: float
    shipped_date: datetime
    tracking_number: str
    status: str


# ==================== AP 模块端点 ====================

@router.get("/ap/invoice-po-matches/{invoice_id}", response_model=List[APInvoicePOMatch])
async def get_invoice_po_matches(invoice_id: int, db=Depends(get_db)):
    """
    查询发票与 PO 匹配关系
    
    - **invoice_id**: 发票 ID
    - **返回**: 发票与 PO 的匹配明细
    """
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT match_id, invoice_id, po_line_id, matched_amount, 
                   match_type, match_date
            FROM ap_invoice_po_matches
            WHERE invoice_id = %s
            ORDER BY match_date DESC
        """, (invoice_id,))
        
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append(APInvoicePOMatch(
                match_id=row[0],
                invoice_id=row[1],
                po_line_id=row[2],
                matched_amount=float(row[3]) if row[3] else 0,
                match_type=row[4],
                match_date=row[5]
            ))
        
        cursor.close()
        return {"success": True, "data": results, "count": len(results)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")


@router.get("/ap/gl-interface/{invoice_id}")
async def get_ap_gl_interface(invoice_id: int, db=Depends(get_db)):
    """
    查询应付总账接口数据
    
    - **invoice_id**: 发票 ID
    - **返回**: 应付总账接口记录
    """
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT interface_id, invoice_id, gl_batch_name, 
                   dr_amount, cr_amount, status, creation_date
            FROM ap_gl_interface
            WHERE invoice_id = %s
            ORDER BY creation_date DESC
        """, (invoice_id,))
        
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append({
                "interface_id": row[0],
                "invoice_id": row[1],
                "gl_batch_name": row[2],
                "dr_amount": float(row[3]) if row[3] else 0,
                "cr_amount": float(row[4]) if row[4] else 0,
                "status": row[5],
                "creation_date": row[6]
            })
        
        cursor.close()
        return {"success": True, "data": results, "count": len(results)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")


@router.get("/ap/payments/{payment_id}")
async def get_payment_details(payment_id: int, db=Depends(get_db)):
    """
    查询付款与发票分配明细
    
    - **payment_id**: 付款 ID
    - **返回**: 付款分配记录
    """
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT dist_id, payment_id, invoice_id, amount, 
                   discount_amount, payment_date
            FROM ap_payment_invoice_dists
            WHERE payment_id = %s
            ORDER BY payment_date DESC
        """, (payment_id,))
        
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append({
                "dist_id": row[0],
                "payment_id": row[1],
                "invoice_id": row[2],
                "amount": float(row[3]) if row[3] else 0,
                "discount_amount": float(row[4]) if row[4] else 0,
                "payment_date": row[5]
            })
        
        cursor.close()
        return {"success": True, "data": results, "count": len(results)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")


# ==================== PO 模块端点 ====================

@router.get("/po/approval-history/{po_header_id}")
async def get_po_approval_history(po_header_id: int, db=Depends(get_db)):
    """
    查询采购订单审批历史
    
    - **po_header_id**: 采购订单头 ID
    - **返回**: 审批历史记录
    """
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT approval_id, po_header_id, approver_id, 
                   approval_level, approval_status, approval_date
            FROM po_approval_history
            WHERE po_header_id = %s
            ORDER BY approval_level ASC
        """, (po_header_id,))
        
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append({
                "approval_id": row[0],
                "po_header_id": row[1],
                "approver_id": row[2],
                "approval_level": row[3],
                "approval_status": row[4],
                "approval_date": row[5]
            })
        
        cursor.close()
        return {"success": True, "data": results, "count": len(results)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")


@router.get("/po/requisition-links/{req_line_id}")
async def get_requisition_links(req_line_id: int, db=Depends(get_db)):
    """
    查询采购申请转 PO 关联
    
    - **req_line_id**: 申请行 ID
    - **返回**: 申请转 PO 关联记录
    """
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT link_id, requisition_line_id, po_line_id, 
                   linked_amount, status, creation_date
            FROM po_requisition_links
            WHERE requisition_line_id = %s
        """, (req_line_id,))
        
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append({
                "link_id": row[0],
                "requisition_line_id": row[1],
                "po_line_id": row[2],
                "linked_amount": float(row[3]) if row[3] else 0,
                "status": row[4],
                "creation_date": row[5]
            })
        
        cursor.close()
        return {"success": True, "data": results, "count": len(results)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")


@router.get("/vendor-performance/{supplier_id}")
async def get_vendor_performance(supplier_id: int, db=Depends(get_db)):
    """
    查询供应商绩效评估
    
    - **supplier_id**: 供应商 ID
    - **返回**: 供应商绩效评分
    """
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT perf_id, supplier_id, quality_score, delivery_score, 
                   price_score, service_score, overall_score, evaluation_period
            FROM vendor_performance_scores
            WHERE supplier_id = %s
            ORDER BY evaluation_period DESC
        """, (supplier_id,))
        
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append({
                "perf_id": row[0],
                "supplier_id": row[1],
                "quality_score": float(row[2]) if row[2] else 0,
                "delivery_score": float(row[3]) if row[3] else 0,
                "price_score": float(row[4]) if row[4] else 0,
                "service_score": float(row[5]) if row[5] else 0,
                "overall_score": float(row[6]) if row[6] else 0,
                "evaluation_period": row[7]
            })
        
        cursor.close()
        return {"success": True, "data": results, "count": len(results)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")


# ==================== GL 模块端点 ====================

@router.get("/gl/journal-lines/{je_header_id}", response_model=List[GLJournalLine])
async def get_gl_journal_lines(je_header_id: int, db=Depends(get_db)):
    """
    查询总账日记账行
    
    - **je_header_id**: 日记账头 ID
    - **返回**: 日记账行明细
    """
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT line_id, je_header_id, code_combination_id, 
                   dr_amount, cr_amount, description
            FROM gl_journal_lines
            WHERE je_header_id = %s
            ORDER BY line_number ASC
        """, (je_header_id,))
        
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append(GLJournalLine(
                line_id=row[0],
                je_header_id=row[1],
                code_combination_id=row[2],
                dr_amount=float(row[3]) if row[3] else 0,
                cr_amount=float(row[4]) if row[4] else 0
            ))
        
        cursor.close()
        return {"success": True, "data": results, "count": len(results)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")


@router.get("/gl/balances/{code_combination_id}", response_model=List[GLBalance])
async def get_gl_balances(code_combination_id: int, db=Depends(get_db)):
    """
    查询总账余额
    
    - **code_combination_id**: 科目组合 ID
    - **返回**: 总账余额记录
    """
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT balance_id, code_combination_id, period_name, 
                   begin_balance, debit, credit, end_balance
            FROM gl_balances
            WHERE code_combination_id = %s
            ORDER BY period_name DESC
        """, (code_combination_id,))
        
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append(GLBalance(
                balance_id=row[0],
                code_combination_id=row[1],
                period_name=row[2],
                begin_balance=float(row[3]) if row[3] else 0,
                debit=float(row[4]) if row[4] else 0,
                credit=float(row[5]) if row[5] else 0,
                end_balance=float(row[6]) if row[6] else 0
            ))
        
        cursor.close()
        return {"success": True, "data": results, "count": len(results)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")


@router.get("/gl/account-segments/{code_combination_id}")
async def get_account_segments(code_combination_id: int, db=Depends(get_db)):
    """
    查询科目组合段
    
    - **code_combination_id**: 科目组合 ID
    - **返回**: 科目段明细（公司/成本中心/科目等）
    """
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT segment_id, code_combination_id, segment_num, 
                   segment_name, segment_value
            FROM gl_code_combination_segments
            WHERE code_combination_id = %s
            ORDER BY segment_num ASC
        """, (code_combination_id,))
        
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append({
                "segment_id": row[0],
                "code_combination_id": row[1],
                "segment_num": row[2],
                "segment_name": row[3],
                "segment_value": row[4]
            })
        
        cursor.close()
        return {"success": True, "data": results, "count": len(results)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")


# ==================== AR 模块端点 ====================

@router.get("/ar/receipt-applications/{receipt_id}")
async def get_receipt_applications(receipt_id: int, db=Depends(get_db)):
    """
    查询收款与发票应用
    
    - **receipt_id**: 收款 ID
    - **返回**: 收款应用记录
    """
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT application_id, receipt_id, invoice_id, 
                   applied_amount, application_date
            FROM ar_receipt_applications_extended
            WHERE receipt_id = %s
            ORDER BY application_date DESC
        """, (receipt_id,))
        
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append({
                "application_id": row[0],
                "receipt_id": row[1],
                "invoice_id": row[2],
                "applied_amount": float(row[3]) if row[3] else 0,
                "application_date": row[4]
            })
        
        cursor.close()
        return {"success": True, "data": results, "count": len(results)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")


@router.get("/ar/customer-profile/{customer_id}")
async def get_customer_profile(customer_id: int, db=Depends(get_db)):
    """
    查询客户配置
    
    - **customer_id**: 客户 ID
    - **返回**: 客户配置信息（信用额度/付款条款）
    """
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT profile_id, customer_id, credit_limit, 
                   discount_percent, payment_terms_id, statement_cycle
            FROM ar_customer_profiles_extended
            WHERE customer_id = %s
        """, (customer_id,))
        
        row = cursor.fetchone()
        if row:
            result = {
                "profile_id": row[0],
                "customer_id": row[1],
                "credit_limit": float(row[2]) if row[2] else 0,
                "discount_percent": float(row[3]) if row[3] else 0,
                "payment_terms_id": row[4],
                "statement_cycle": row[5]
            }
        else:
            result = None
        
        cursor.close()
        return {"success": True, "data": result}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")


@router.get("/ar/customer-balances/{customer_id}", response_model=List[ARCustomerBalance])
async def get_customer_balances(customer_id: int, db=Depends(get_db)):
    """
    查询客户余额账龄
    
    - **customer_id**: 客户 ID
    - **返回**: 客户余额及账龄分析
    """
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT balance_id, customer_id, balance_date, currency_code,
                   outstanding_balance, current_balance, 
                   balance_1_30, balance_31_60, balance_61_90, balance_over_90
            FROM ar_customer_balances
            WHERE customer_id = %s
            ORDER BY balance_date DESC
        """, (customer_id,))
        
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append(ARCustomerBalance(
                balance_id=row[0],
                customer_id=row[1],
                balance_date=row[2],
                currency_code=row[3],
                outstanding_balance=float(row[4]) if row[4] else 0,
                current_balance=float(row[5]) if row[5] else 0,
                balance_1_30=float(row[6]) if row[6] else 0,
                balance_31_60=float(row[7]) if row[7] else 0,
                balance_61_90=float(row[8]) if row[8] else 0,
                balance_over_90=float(row[9]) if row[9] else 0
            ))
        
        cursor.close()
        return {"success": True, "data": results, "count": len(results)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")


@router.get("/ar/collection-cases/{customer_id}")
async def get_collection_cases(customer_id: int, db=Depends(get_db)):
    """
    查询催收案例
    
    - **customer_id**: 客户 ID
    - **返回**: 催收案例记录
    """
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT case_id, customer_id, invoice_id, case_status, 
                   priority, total_amount, resolved_amount, creation_date
            FROM ar_collection_cases
            WHERE customer_id = %s
            ORDER BY creation_date DESC
        """, (customer_id,))
        
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append({
                "case_id": row[0],
                "customer_id": row[1],
                "invoice_id": row[2],
                "case_status": row[3],
                "priority": row[4],
                "total_amount": float(row[5]) if row[5] else 0,
                "resolved_amount": float(row[6]) if row[6] else 0,
                "creation_date": row[7]
            })
        
        cursor.close()
        return {"success": True, "data": results, "count": len(results)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")


# ==================== INV 模块端点 ====================

@router.get("/inv/subinventories/{organization_id}")
async def get_subinventories(organization_id: int, db=Depends(get_db)):
    """
    查询子库存
    
    - **organization_id**: 组织 ID
    - **返回**: 子库存列表
    """
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT subinv_id, organization_id, subinventory_code, 
                   subinventory_type, locator_control, description
            FROM inv_subinventories_extended
            WHERE organization_id = %s
            ORDER BY subinventory_code ASC
        """, (organization_id,))
        
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append({
                "subinv_id": row[0],
                "organization_id": row[1],
                "subinventory_code": row[2],
                "subinventory_type": row[3],
                "locator_control": row[4],
                "description": row[5]
            })
        
        cursor.close()
        return {"success": True, "data": results, "count": len(results)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")


@router.get("/inv/locators/{subinventory_id}", response_model=List[INVLocator])
async def get_locators(subinventory_id: int, db=Depends(get_db)):
    """
    查询库存货位
    
    - **subinventory_id**: 子库存 ID
    - **返回**: 库存货位列表
    """
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT locator_id, subinventory_id, locator_code, 
                   segment1, segment2
            FROM inv_item_locators_extended
            WHERE subinventory_id = %s
            ORDER BY locator_code ASC
        """, (subinventory_id,))
        
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append(INVLocator(
                locator_id=row[0],
                subinventory_id=row[1],
                locator_code=row[2],
                segment1=row[3],
                segment2=row[4]
            ))
        
        cursor.close()
        return {"success": True, "data": results, "count": len(results)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")


@router.get("/inv/lots/{item_id}")
async def get_lot_numbers(item_id: int, db=Depends(get_db)):
    """
    查询批次号
    
    - **item_id**: 物料 ID
    - **返回**: 批次号列表
    """
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT lot_id, item_id, lot_number, 
                   generation_date, expiration_date, supplier_id
            FROM inv_lot_numbers_extended
            WHERE item_id = %s
            ORDER BY generation_date DESC
        """, (item_id,))
        
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append({
                "lot_id": row[0],
                "item_id": row[1],
                "lot_number": row[2],
                "generation_date": row[3],
                "expiration_date": row[4],
                "supplier_id": row[5]
            })
        
        cursor.close()
        return {"success": True, "data": results, "count": len(results)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")


@router.get("/inv/serials/{item_id}")
async def get_serial_numbers(item_id: int, db=Depends(get_db)):
    """
    查询序列号
    
    - **item_id**: 物料 ID
    - **返回**: 序列号列表
    """
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT serial_id, item_id, serial_number, 
                   status, receipt_date
            FROM inv_serial_numbers_extended
            WHERE item_id = %s
            ORDER BY receipt_date DESC
        """, (item_id,))
        
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append({
                "serial_id": row[0],
                "item_id": row[1],
                "serial_number": row[2],
                "status": row[3],
                "receipt_date": row[4]
            })
        
        cursor.close()
        return {"success": True, "data": results, "count": len(results)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")


# ==================== OM 模块端点 ====================

@router.get("/om/shipments/{shipment_id}", response_model=List[OMShipmentDetail])
async def get_shipment_details(shipment_id: int, db=Depends(get_db)):
    """
    查询发运明细
    
    - **shipment_id**: 发运 ID
    - **返回**: 发运明细列表
    """
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT shipment_detail_id, shipment_id, order_line_id, 
                   shipped_quantity, shipped_date, tracking_number, status
            FROM om_shipment_details_extended
            WHERE shipment_id = %s
            ORDER BY shipped_date DESC
        """, (shipment_id,))
        
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append(OMShipmentDetail(
                shipment_detail_id=row[0],
                shipment_id=row[1],
                order_line_id=row[2],
                shipped_quantity=float(row[3]) if row[3] else 0,
                shipped_date=row[4],
                tracking_number=row[5],
                status=row[6]
            ))
        
        cursor.close()
        return {"success": True, "data": results, "count": len(results)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")


@router.get("/om/reservations/{order_line_id}")
async def get_order_reservations(order_line_id: int, db=Depends(get_db)):
    """
    查询订单预留
    
    - **order_line_id**: 订单行 ID
    - **返回**: 订单预留记录
    """
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT reservation_id, order_line_id, item_id, 
                   reserved_quantity, status, organization_id
            FROM om_order_reservations
            WHERE order_line_id = %s
        """, (order_line_id,))
        
        rows = cursor.fetchall()
        results = []
        for row in rows:
            results.append({
                "reservation_id": row[0],
                "order_line_id": row[1],
                "item_id": row[2],
                "reserved_quantity": float(row[3]) if row[3] else 0,
                "status": row[4],
                "organization_id": row[5]
            })
        
        cursor.close()
        return {"success": True, "data": results, "count": len(results)}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")


# ==================== Neo4j 图查询端点 ====================

@router.get("/neo4j/customer-360/{customer_id}")
async def get_customer_360(customer_id: int):
    """
    查询客户 360 视图（Neo4j 图数据库）
    
    - **customer_id**: 客户 ID
    - **返回**: 客户关联的所有节点和关系
    """
    try:
        driver = GraphDatabase.driver(
            neo4j_config.uri,
            auth=(neo4j_config.user, neo4j_config.password)
        )
        
        with driver.session() as session:
            result = session.run("""
                MATCH (cust:Customer {customer_id: $customer_id})
                OPTIONAL MATCH (cust)-[:HAS_PROFILE]-(profile)
                OPTIONAL MATCH (cust)-[:HAS_BALANCE]-(balance)
                OPTIONAL MATCH (cust)-[:HAS_COLLECTION_CASE]-(cases)
                RETURN cust, collect(DISTINCT profile) as profiles,
                       collect(DISTINCT balance) as balances,
                       collect(DISTINCT cases) as collection_cases
            """, {"customer_id": customer_id})
            
            record = result.single()
            if record:
                customer = dict(record["cust"])
                profiles = [dict(p) for p in record["profiles"]]
                balances = [dict(b) for b in record["balances"]]
                cases = [dict(c) for c in record["collection_cases"]]
                
                return {
                    "success": True,
                    "data": {
                        "customer": customer,
                        "profiles": profiles,
                        "balances": balances,
                        "collection_cases": cases
                    }
                }
            else:
                return {"success": False, "data": None, "message": "客户不存在"}
        
        driver.close()
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Neo4j 查询失败：{str(e)}")


@router.get("/neo4j/end-to-end/{process_type}")
async def get_end_to_end_process(process_type: str):
    """
    查询端到端流程（Neo4j 图数据库）
    
    - **process_type**: 流程类型（quote-to-cash / procure-to-pay / record-to-report）
    - **返回**: 完整流程路径
    """
    try:
        driver = GraphDatabase.driver(
            neo4j_config.uri,
            auth=(neo4j_config.user, neo4j_config.password)
        )
        
        with driver.session() as session:
            if process_type == "quote-to-cash":
                cypher = """
                    MATCH path = (:Quote)-[:CONVERTS_TO_ORDER|TRIGGERS_SHIPMENT|GENERATES_INVOICE|RESULT_IN|DEPOSITED_TO|POSTS_TO_GL*]->(:GLJournal)
                    RETURN path LIMIT 5
                """
            elif process_type == "procure-to-pay":
                cypher = """
                    MATCH path = (:PurchaseRequisition)-[:CONVERTS_TO_PO|TRIGGERS_RECEIPT|GENERATES_INVOICE|RESULT_IN|PAID_FROM|POSTS_TO_GL*]->(:GLJournal)
                    RETURN path LIMIT 5
                """
            elif process_type == "record-to-report":
                cypher = """
                    MATCH path = (:SubledgerTransaction)-[:CREATES_JOURNAL|POSTS_TO_LEDGER|ROLLS_UP_TO|GENERATES_REPORT*]->(:FinancialReport)
                    RETURN path LIMIT 5
                """
            else:
                return {"success": False, "message": "不支持的流程类型"}
            
            result = session.run(cypher)
            paths = []
            for record in result:
                path = record["path"]
                paths.append({
                    "nodes": [dict(node) for node in path.nodes],
                    "relationships": [dict(rel) for rel in path.relationships]
                })
            
            return {
                "success": True,
                "data": paths,
                "count": len(paths)
            }
        
        driver.close()
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Neo4j 查询失败：{str(e)}")


# ==================== 统计端点 ====================

@router.get("/stats/summary")
async def get_stats_summary(db=Depends(get_db)):
    """
    获取关系统计摘要
    
    - **返回**: 各模块表数量和记录数统计
    """
    try:
        cursor = db.cursor()
        
        # 统计各模块表数量
        modules = {
            "AP": ["ap_invoice_po_matches", "ap_gl_interface", "ap_payment_invoice_dists"],
            "PO": ["po_approval_history", "po_requisition_links", "vendor_performance_scores"],
            "GL": ["gl_journal_lines", "gl_balances", "gl_code_combination_segments"],
            "AR": ["ar_receipt_applications_extended", "ar_customer_profiles_extended", 
                   "ar_customer_balances", "ar_collection_cases"],
            "INV": ["inv_subinventories_extended", "inv_item_locators_extended",
                    "inv_lot_numbers_extended", "inv_serial_numbers_extended"],
            "OM": ["om_shipment_details_extended", "om_order_reservations"]
        }
        
        stats = {}
        for module, tables in modules.items():
            module_stats = {}
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                module_stats[table] = count
            
            stats[module] = module_stats
        
        cursor.close()
        
        return {
            "success": True,
            "data": stats,
            "total_tables": sum(len(tables) for tables in modules.values())
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"统计失败：{str(e)}")
