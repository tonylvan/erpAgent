"""
Agent 风险检测 API 路由 - 简化版（用于测试）
暂时不依赖 Neo4j，直接返回测试结果
"""

import logging
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException
from datetime import datetime

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/agents", tags=["Agent 风险检测"])


@router.get("/business-risk")
async def check_business_risk():
    """业务风险检测 - 测试版本"""
    try:
        # 测试数据：模拟检测到负库存
        findings = [
            {
                "risk_id": "business_risk_inventory_low_999999",
                "risk_type": "INVENTORY_LOW",
                "severity": "CRITICAL",
                "entity_id": "999999",
                "entity_name": "英伟达 H100 芯片",
                "description": "库存低于安全线：当前 -100 个，安全库存 100 个",
                "recommendation": "立即补货 200 件，联系供应商确认交货时间",
                "data": {
                    "product_id": 999999,
                    "current_stock": -100,
                    "safety_stock": 100,
                    "shortage": 200
                },
                "detected_at": datetime.now().isoformat(),
                "agent": "business_risk",
                "agent_version": "1.0.0"
            },
            {
                "risk_id": "business_risk_po_price_555555",
                "risk_type": "PURCHASE_PRICE_ABNORMAL",
                "severity": "HIGH",
                "entity_id": "555555",
                "entity_name": "EXP-PO-001",
                "description": "采购价格异常：单价 $190,000.00，超出正常范围 200%",
                "recommendation": "核实价格，确认是否为英伟达 H100 芯片的市场价格",
                "data": {
                    "po_id": -555555,
                    "unit_price": 190000.00,
                    "normal_price": 50000.00,
                    "variance": 280
                },
                "detected_at": datetime.now().isoformat(),
                "agent": "business_risk",
                "agent_version": "1.0.0"
            }
        ]
        
        return {
            "success": True,
            "agent": "business_risk",
            "findings": findings,
            "summary": {
                "total": 2,
                "critical": 1,
                "high": 1,
                "medium": 0,
                "low": 0
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Business risk check failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"业务风险检测失败：{str(e)}")


@router.get("/financial-risk")
async def check_financial_risk():
    """财务风险检测 - 测试版本"""
    try:
        # 测试数据：模拟检测到异常付款
        findings = [
            {
                "risk_id": "financial_risk_huge_payment_666666",
                "risk_type": "HUGE_PAYMENT",
                "severity": "CRITICAL",
                "entity_id": "666666",
                "entity_name": "HUGE-PAY-001",
                "description": "异常大额付款：金额 $150,000,000.00，超出正常阈值 100 倍",
                "recommendation": "立即人工审核，确认付款真实性，防止欺诈",
                "data": {
                    "payment_id": -666666,
                    "amount": 150000000.00,
                    "threshold": 1000000.00,
                    "vendor_id": 888888,
                    "vendor_name": "异常付款测试供应商 - 英伟达"
                },
                "detected_at": datetime.now().isoformat(),
                "agent": "financial_risk",
                "agent_version": "1.0.0"
            }
        ]
        
        return {
            "success": True,
            "agent": "financial_risk",
            "findings": findings,
            "summary": {
                "total": 1,
                "critical": 1,
                "high": 0,
                "medium": 0,
                "low": 0
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Financial risk check failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"财务风险检测失败：{str(e)}")


@router.get("/user-operation")
async def check_user_operation():
    """用户操作风险检测 - 测试版本"""
    try:
        # 测试数据：无异常
        return {
            "success": True,
            "agent": "user_operation",
            "findings": [],
            "summary": {
                "total": 0,
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"User operation check failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"用户操作检测失败：{str(e)}")


@router.get("/all")
async def check_all_risks():
    """全量风险检测"""
    try:
        business = await check_business_risk()
        financial = await check_financial_risk()
        user_op = await check_user_operation()
        
        return {
            "success": True,
            "business_risk": business.get("findings", []),
            "financial_risk": financial.get("findings", []),
            "user_operation": user_op.get("findings", []),
            "summary": {
                "business_total": len(business.get("findings", [])),
                "financial_total": len(financial.get("findings", [])),
                "user_operation_total": len(user_op.get("findings", [])),
                "grand_total": len(business.get("findings", [])) + len(financial.get("findings", [])) + len(user_op.get("findings", []))
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"All risks check failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"全量风险检测失败：{str(e)}")


@router.get("/summary")
async def get_risk_summary():
    """风险摘要统计"""
    try:
        business = await check_business_risk()
        financial = await check_financial_risk()
        user_op = await check_user_operation()
        
        return {
            "success": True,
            "summary": {
                "total_risks": business["summary"]["total"] + financial["summary"]["total"] + user_op["summary"]["total"],
                "critical": business["summary"]["critical"] + financial["summary"]["critical"] + user_op["summary"]["critical"],
                "high": business["summary"]["high"] + financial["summary"]["high"] + user_op["summary"]["high"],
                "medium": business["summary"]["medium"] + financial["summary"]["medium"] + user_op["summary"]["medium"],
                "low": business["summary"]["low"] + financial["summary"]["low"] + user_op["summary"]["low"]
            },
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Risk summary failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"风险摘要失败：{str(e)}")
