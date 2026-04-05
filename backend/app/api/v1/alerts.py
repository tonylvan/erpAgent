"""
预警中心 API - 提供预警 CRUD 接口和统计分析

API 端点:
- GET /api/v1/alerts - 获取预警列表
- GET /api/v1/alerts/stats - 获取预警统计
- GET /api/v1/alerts/{alert_id} - 获取单个预警详情
- POST /api/v1/alerts/{alert_id}/acknowledge - 确认预警
- POST /api/v1/alerts/{alert_id}/assign - 分配预警负责人
- GET /api/v1/alerts/financial - 获取财务风险专项
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.services.alert_rules import AlertRuleEngine, create_alert_engine
from app.services.alert_service import get_alert_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/alerts", tags=["预警中心"])


# ==================== 数据模型 ====================

class AlertItem(BaseModel):
    """预警项模型"""
    alert_type: str = Field(..., description="预警类型")
    severity: str = Field(..., description="预警等级 (RED/ORANGE/YELLOW)")
    description: str = Field(..., description="预警描述")
    recommendation: str = Field(..., description="处理建议")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    
    class Config:
        arbitrary_types_allowed = True


class AlertStats(BaseModel):
    """预警统计模型"""
    total: int = Field(..., description="预警总数")
    by_severity: Dict[str, int] = Field(..., description="按级别统计")
    by_type: Dict[str, int] = Field(..., description="按类型统计")
    financial_risks: int = Field(..., description="财务风险数量")
    business_alerts: int = Field(..., description="业务预警数量")


class AlertListResponse(BaseModel):
    """预警列表响应"""
    success: bool = True
    data: Dict[str, List[Dict[str, Any]]] = Field(..., description="预警数据")
    stats: AlertStats = Field(..., description="统计信息")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")


class FinancialRiskResponse(BaseModel):
    """财务风险专项响应"""
    success: bool = True
    risks: List[Dict[str, Any]] = Field(..., description="财务风险列表")
    health_score: Optional[float] = Field(None, description="财务健康度评分 (0-100)")
    timestamp: datetime = Field(default_factory=datetime.now, description="响应时间")


# ==================== 依赖注入 ====================

def get_alert_engine(driver=Depends(get_neo4j_driver)) -> AlertRuleEngine:
    """获取预警规则引擎实例"""
    return create_alert_engine(driver)


# ==================== API 端点 ====================

@router.get("", response_model=AlertListResponse)
async def get_alerts(
    rule: Optional[str] = Query(None, description="指定预警规则名称"),
    severity: Optional[str] = Query(None, description="按级别筛选 (RED/ORANGE/YELLOW)", pattern="^(RED|ORANGE|YELLOW)$"),
    engine: AlertRuleEngine = Depends(get_alert_engine),
):
    """
    获取预警列表
    
    - **rule**: 可选，指定运行单个预警规则
    - **severity**: 可选，按预警级别筛选
    
    返回所有预警规则的结果和统计信息
    """
    try:
        if rule:
            # 运行单个规则
            rule_method = getattr(engine, rule, None)
            if not rule_method:
                raise HTTPException(status_code=400, detail=f"未知的预警规则：{rule}")
            
            alerts_data = {rule: rule_method()}
        else:
            # 运行所有规则
            alerts_data = engine.run_all_alerts()
        
        # 按 severity 筛选
        if severity:
            filtered_data = {}
            for rule_name, alerts in alerts_data.items():
                filtered_alerts = [a for a in alerts if a.get('severity') == severity]
                if filtered_alerts:
                    filtered_data[rule_name] = filtered_alerts
            alerts_data = filtered_data
        
        # 获取统计
        stats_data = engine.get_alert_statistics()
        stats = AlertStats(**stats_data)
        
        return AlertListResponse(
            data=alerts_data,
            stats=stats,
            timestamp=datetime.now()
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alerts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取预警失败：{str(e)}")


@router.get("/stats", response_model=AlertStats)
async def get_alert_statistics(engine: AlertRuleEngine = Depends(get_alert_engine)):
    """
    获取预警统计数据
    
    返回各级别预警数量、类型分布等统计信息
    """
    try:
        stats = engine.get_alert_statistics()
        return AlertStats(**stats)
    except Exception as e:
        logger.error(f"Error getting alert stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取统计失败：{str(e)}")


@router.get("/financial", response_model=FinancialRiskResponse)
async def get_financial_risks(engine: AlertRuleEngine = Depends(get_alert_engine)):
    """
    获取财务风险专项
    
    返回所有财务风险预警和财务健康度评分
    """
    try:
        # 获取所有财务风险
        financial_rules = [
            'cashflow_risk',
            'ar_overdue_risk',
            'ap_risk',
            'financial_ratio_abnormal',
            'budget_variance',
        ]
        
        all_risks = []
        for rule_name in financial_rules:
            rule_method = getattr(engine, rule_name, None)
            if rule_method:
                risks = rule_method()
                all_risks.extend(risks)
        
        # 计算财务健康度评分 (简化版)
        health_score = calculate_financial_health_score(engine)
        
        return FinancialRiskResponse(
            risks=all_risks,
            health_score=health_score,
            timestamp=datetime.now()
        )
    
    except Exception as e:
        logger.error(f"Error getting financial risks: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取财务风险失败：{str(e)}")


@router.post("/{alert_type}/acknowledge")
async def acknowledge_alert(
    alert_type: str,
    alert_id: str = Query(..., description="预警 ID"),
    acknowledged_by: str = Query(..., description="确认人"),
    notes: Optional[str] = Query(None, description="备注"),
    engine: AlertRuleEngine = Depends(get_alert_engine),
):
    """
    确认预警
    
    - **alert_type**: 预警类型
    - **alert_id**: 预警 ID
    - **acknowledged_by**: 确认人
    - **notes**: 可选备注
    """
    try:
        # TODO: 实现预警确认逻辑 (保存到数据库)
        logger.info(f"Alert acknowledged: {alert_type}/{alert_id} by {acknowledged_by}")
        
        return {
            "success": True,
            "message": "预警已确认",
            "data": {
                "alert_type": alert_type,
                "alert_id": alert_id,
                "acknowledged_by": acknowledged_by,
                "acknowledged_at": datetime.now(),
                "notes": notes,
            }
        }
    
    except Exception as e:
        logger.error(f"Error acknowledging alert: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"确认预警失败：{str(e)}")


@router.post("/{alert_type}/assign")
async def assign_alert(
    alert_type: str,
    alert_id: str = Query(..., description="预警 ID"),
    assignee_id: str = Query(..., description="负责人 ID"),
    assignee_name: str = Query(..., description="负责人姓名"),
    due_hours: int = Query(24, description="处理时限 (小时)"),
    engine: AlertRuleEngine = Depends(get_alert_engine),
):
    """
    分配预警负责人
    
    - **alert_type**: 预警类型
    - **alert_id**: 预警 ID
    - **assignee_id**: 负责人 ID
    - **assignee_name**: 负责人姓名
    - **due_hours**: 处理时限 (小时)
    """
    try:
        # TODO: 实现预警分配逻辑 (创建工单)
        logger.info(f"Alert assigned: {alert_type}/{alert_id} to {assignee_name}")
        
        return {
            "success": True,
            "message": "预警已分配",
            "data": {
                "alert_type": alert_type,
                "alert_id": alert_id,
                "assignee_id": assignee_id,
                "assignee_name": assignee_name,
                "due_hours": due_hours,
                "assigned_at": datetime.now(),
            }
        }
    
    except Exception as e:
        logger.error(f"Error assigning alert: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"分配预警失败：{str(e)}")


@router.get("/rules")
async def get_alert_rules():
    """
    获取所有预警规则定义
    
    返回所有可用的预警规则及其说明
    """
    rules = {
        "business_alerts": {
            "inventory_low": {
                "name": "库存预警",
                "description": "库存低于安全线时触发",
                "severity": "YELLOW",
            },
            "inventory_zero": {
                "name": "库存为零预警",
                "description": "库存为 0 时触发高危预警",
                "severity": "RED",
            },
            "payment_overdue": {
                "name": "付款逾期预警",
                "description": "发票付款逾期时触发",
                "severity": "RED/ORANGE/YELLOW",
            },
            "customer_churn": {
                "name": "客户流失预警",
                "description": "客户 90 天未下单时触发",
                "severity": "RED/ORANGE/YELLOW",
            },
            "delivery_delay": {
                "name": "供应商交货逾期预警",
                "description": "采购订单交货逾期时触发",
                "severity": "RED/ORANGE/YELLOW",
            },
            "sales_anomaly": {
                "name": "销售订单异常预警",
                "description": "订单金额异常波动时触发",
                "severity": "ORANGE/YELLOW",
            },
        },
        "financial_risks": {
            "cashflow_risk": {
                "name": "现金流预警",
                "description": "现金流低于安全线时触发",
                "severity": "RED",
            },
            "ar_overdue_risk": {
                "name": "应收账款逾期预警",
                "description": "客户应收账款逾期时触发",
                "severity": "RED/ORANGE/YELLOW",
            },
            "ap_risk": {
                "name": "应付账款风险预警",
                "description": "7 天内到期应付预警",
                "severity": "ORANGE",
            },
            "financial_ratio_abnormal": {
                "name": "财务比率异常预警",
                "description": "关键财务指标异常时触发",
                "severity": "RED/ORANGE/YELLOW",
            },
            "budget_variance": {
                "name": "预算偏差预警",
                "description": "部门预算偏差超过 20% 时触发",
                "severity": "RED/ORANGE/YELLOW",
            },
        }
    }
    
    return {
        "success": True,
        "data": rules,
        "total_rules": 11,
    }


# ==================== 辅助函数 ====================

def calculate_financial_health_score(engine: AlertRuleEngine) -> Optional[float]:
    """
    计算财务健康度评分 (0-100 分)
    
    基于以下指标:
    - 流动比率 (权重 30%)
    - 负债权益比 (权重 25%)
    - ROE (权重 25%)
    - 现金流 (权重 20%)
    """
    try:
        # 获取财务比率数据
        ratios = engine.check_financial_ratio_abnormal()
        cashflow_risks = engine.check_cashflow_risk()
        
        if not ratios and not cashflow_risks:
            return None
        
        score = 100.0
        
        # 根据财务比率异常扣分
        if ratios:
            for ratio in ratios:
                abnormal_count = ratio.get('abnormal_count', 0)
                score -= abnormal_count * 10  # 每个异常扣 10 分
        
        # 根据现金流风险扣分
        if cashflow_risks:
            score -= len(cashflow_risks) * 20  # 每个现金流风险扣 20 分
        
        # 确保分数在 0-100 范围内
        return max(0.0, min(100.0, score))
    
    except Exception as e:
        logger.error(f"Error calculating health score: {e}")
        return None
