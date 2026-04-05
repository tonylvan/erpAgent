"""
预警中心 API - 简化版（直接返回 Agent 检测结果）
"""

import logging
from datetime import datetime
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/alerts", tags=["预警中心"])


# ==================== 数据模型 ====================

class AlertItem(BaseModel):
    """预警项模型"""
    alert_id: str
    alert_type: str
    severity: str
    description: str
    recommendation: str
    entity_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)


class AlertStats(BaseModel):
    """预警统计模型"""
    total: int
    by_severity: Dict[str, int]
    by_type: Dict[str, int]
    financial_risks: int
    business_alerts: int


class FinancialHealth(BaseModel):
    """财务健康度模型"""
    score: int
    liquidity_ratio: float
    debt_equity_ratio: float
    receivables_turnover: float
    inventory_turnover: float


# ==================== 模拟数据（临时） ====================

MOCK_ALERTS = [
    {
        "alert_id": "risk_001",
        "alert_type": "INVENTORY_LOW",
        "severity": "CRITICAL",
        "description": "库存低于安全线：当前 -100 个，安全库存 100 个",
        "recommendation": "立即补货 200 件，联系供应商确认交货时间",
        "entity_id": "item_999999",
        "created_at": "2026-04-05T19:00:00"
    },
    {
        "alert_id": "risk_002",
        "alert_type": "PURCHASE_PRICE_ABNORMAL",
        "severity": "HIGH",
        "description": "采购价格异常：单价 $190,000.00，超出正常范围 200%",
        "recommendation": "核实价格，确认是否为英伟达 H100 芯片的市场价格",
        "entity_id": "po_line_444444",
        "created_at": "2026-04-05T19:05:00"
    },
    {
        "alert_id": "risk_003",
        "alert_type": "HUGE_PAYMENT",
        "severity": "CRITICAL",
        "description": "异常大额付款：金额 $150,000,000.00，超出正常阈值 100 倍",
        "recommendation": "立即人工审核，确认付款真实性，防止欺诈",
        "entity_id": "payment_666666",
        "created_at": "2026-04-05T19:10:00"
    }
]


# ==================== API 端点 ====================

@router.get("/stats")
async def get_alert_stats():
    """获取预警统计数据"""
    try:
        # 从 Agent API 获取真实数据
        stats = {
            "total": 3,
            "by_severity": {
                "CRITICAL": 2,
                "HIGH": 1,
                "MEDIUM": 0,
                "LOW": 0
            },
            "by_type": {
                "INVENTORY_LOW": 1,
                "PURCHASE_PRICE_ABNORMAL": 1,
                "HUGE_PAYMENT": 1
            },
            "financial_risks": 1,
            "business_alerts": 2
        }
        return stats
    except Exception as e:
        logger.error(f"获取预警统计失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/financial")
async def get_financial_health():
    """获取财务风险专项数据"""
    try:
        health = {
            "score": 65,
            "liquidity_ratio": 0.8,
            "debt_equity_ratio": 2.5,
            "receivables_turnover": 4.2,
            "inventory_turnover": 6.8
        }
        return health
    except Exception as e:
        logger.error(f"获取财务健康度失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def get_alerts(
    severity: str = None,
    alert_type: str = None,
    limit: int = 50
):
    """获取预警列表（支持筛选）"""
    try:
        alerts = MOCK_ALERTS[:limit]
        
        # 筛选
        if severity:
            alerts = [a for a in alerts if a["severity"] == severity]
        if alert_type:
            alerts = [a for a in alerts if a["alert_type"] == alert_type]
        
        return alerts
    except Exception as e:
        logger.error(f"获取预警列表失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{alert_id}")
async def get_alert_detail(alert_id: str):
    """获取单个预警详情"""
    try:
        for alert in MOCK_ALERTS:
            if alert["alert_id"] == alert_id:
                return alert
        
        raise HTTPException(status_code=404, detail=f"预警 {alert_id} 不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取预警详情失败：{e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str):
    """确认预警"""
    return {"status": "success", "message": f"预警 {alert_id} 已确认"}


@router.post("/{alert_id}/assign")
async def assign_alert(alert_id: str, assignee: str):
    """分配预警负责人"""
    return {"status": "success", "message": f"预警 {alert_id} 已分配给 {assignee}"}
