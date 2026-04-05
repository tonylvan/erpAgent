"""
财务分析引擎

包含：
1. 财务健康度评分
2. 风险传播分析
3. 财务趋势分析
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date
from neo4j import GraphDatabase
from neo4j.graph import Node, Relationship, Path
import asyncio

from app.models.financial_risk import (
    CashFlowRisk, ARRisk, APRisk, FinancialRatioRisk, 
    BudgetVarianceRisk, RiskSeverity, FinancialRiskSummary
)


class FinancialAnalysisEngine:
    """财务分析引擎"""
    
    def __init__(self, neo4j_uri: str = "bolt://127.0.0.1:7687", 
                 neo4j_user: str = "neo4j", 
                 neo4j_password: str = "neo4j"):
        self.neo4j_uri = neo4j_uri
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
        
    def close(self):
        """关闭数据库连接"""
        if self.driver:
            self.driver.close()
    
    # ==================== 财务健康度评分 ====================
    
    def calculate_health_score(self, company_id: str) -> Dict[str, Any]:
        """
        计算公司财务健康度评分 (0-100 分)
        
        评分维度：
        - 流动比率 (权重 30%)
        - 负债权益比 (权重 25%)
        - ROE (权重 25%)
        - 现金流 (权重 20%)
        
        Returns:
            {
                "overall_score": 65,
                "dimension_scores": {
                    "liquidity": 40,
                    "leverage": 35,
                    "profitability": 50,
                    "cashflow": 60
                },
                "level": "NEEDS_ATTENTION",
                "recommendations": [...]
            }
        """
        with self.driver.session() as session:
            # 获取财务比率数据
            ratio_result = session.run("""
                MATCH (c:Company {id: $company_id})-[:HAS_FINANCIAL_RATIO]->(r:FinancialRatio)
                RETURN r.current_ratio as current_ratio,
                       r.quick_ratio as quick_ratio,
                       r.debt_to_equity as debt_to_equity,
                       r.roe as roe,
                       r.roi as roi,
                       r.gross_margin as gross_margin
            """, company_id=company_id)
            
            ratio_data = ratio_result.single()
            
            # 获取现金流数据
            cashflow_result = session.run("""
                MATCH (c:Company {id: $company_id})-[:HAS_CASHFLOW]->(cf:CashFlow)
                RETURN cf.balance as balance,
                       cf.minimum_threshold as threshold,
                       cf.monthly_burn_rate as burn_rate
            """, company_id=company_id)
            
            cashflow_data = cashflow_result.single()
            
            # 计算各维度评分
            dimension_scores = {}
            recommendations = []
            
            # 1. 流动性评分 (流动比率，权重 30%)
            liquidity_score = self._calculate_liquidity_score(
                ratio_data["current_ratio"] if ratio_data and ratio_data["current_ratio"] else 1.0,
                ratio_data["quick_ratio"] if ratio_data and ratio_data["quick_ratio"] else 0.8
            )
            dimension_scores["liquidity"] = liquidity_score
            
            if liquidity_score < 50:
                recommendations.append("⚠️ 流动比率偏低，建议优化短期资产结构")
            if liquidity_score < 30:
                recommendations.append("🔴 流动性严重不足，需立即补充营运资金")
            
            # 2. 杠杆评分 (负债权益比，权重 25%)
            leverage_score = self._calculate_leverage_score(
                ratio_data["debt_to_equity"] if ratio_data and ratio_data["debt_to_equity"] else 1.5
            )
            dimension_scores["leverage"] = leverage_score
            
            if leverage_score < 50:
                recommendations.append("⚠️ 负债水平偏高，建议降低财务杠杆")
            
            # 3. 盈利能力评分 (ROE，权重 25%)
            profitability_score = self._calculate_profitability_score(
                ratio_data["roe"] if ratio_data and ratio_data["roe"] else 0.05
            )
            dimension_scores["profitability"] = profitability_score
            
            if profitability_score < 50:
                recommendations.append("⚠️ 盈利能力不足，需提升经营效率")
            
            # 4. 现金流评分 (权重 20%)
            cashflow_score = self._calculate_cashflow_score(
                cashflow_data["balance"] if cashflow_data and cashflow_data["balance"] else 0,
                cashflow_data["threshold"] if cashflow_data and cashflow_data["threshold"] else 1000000,
                cashflow_data["burn_rate"] if cashflow_data and cashflow_data["burn_rate"] else 0
            )
            dimension_scores["cashflow"] = cashflow_score
            
            if cashflow_score < 50:
                recommendations.append("🔴 现金流紧张，建议加快回款或融资")
            
            # 计算综合评分
            overall_score = (
                liquidity_score * 0.30 +
                leverage_score * 0.25 +
                profitability_score * 0.25 +
                cashflow_score * 0.20
            )
            
            # 确定健康等级
            if overall_score >= 80:
                level = "HEALTHY"
            elif overall_score >= 60:
                level = "NEEDS_ATTENTION"
            elif overall_score >= 40:
                level = "AT_RISK"
            else:
                level = "CRITICAL"
            
            return {
                "company_id": company_id,
                "overall_score": round(overall_score, 2),
                "dimension_scores": {k: round(v, 2) for k, v in dimension_scores.items()},
                "level": level,
                "recommendations": recommendations,
                "calculated_at": datetime.now().isoformat()
            }
    
    def _calculate_liquidity_score(self, current_ratio: float, quick_ratio: float) -> float:
        """计算流动性评分 (0-100)"""
        # 流动比率理想值：1.5-2.0
        if current_ratio >= 2.0:
            cr_score = 100
        elif current_ratio >= 1.5:
            cr_score = 90
        elif current_ratio >= 1.2:
            cr_score = 75
        elif current_ratio >= 1.0:
            cr_score = 60
        elif current_ratio >= 0.8:
            cr_score = 40
        else:
            cr_score = max(0, current_ratio * 50)
        
        # 速动比率理想值：1.0-1.2
        if quick_ratio >= 1.2:
            qr_score = 100
        elif quick_ratio >= 1.0:
            qr_score = 90
        elif quick_ratio >= 0.8:
            qr_score = 70
        else:
            qr_score = max(0, quick_ratio * 70)
        
        # 综合评分 (流动比率 70%, 速动比率 30%)
        return cr_score * 0.7 + qr_score * 0.3
    
    def _calculate_leverage_score(self, debt_to_equity: float) -> float:
        """计算杠杆评分 (0-100)"""
        # 负债权益比理想值：<1.5
        if debt_to_equity <= 1.0:
            return 100
        elif debt_to_equity <= 1.5:
            return 85
        elif debt_to_equity <= 2.0:
            return 65
        elif debt_to_equity <= 2.5:
            return 45
        elif debt_to_equity <= 3.0:
            return 25
        else:
            return max(0, 100 - (debt_to_equity - 1.0) * 40)
    
    def _calculate_profitability_score(self, roe: float) -> float:
        """计算盈利能力评分 (0-100)"""
        # ROE 理想值：>15%
        if roe >= 0.20:
            return 100
        elif roe >= 0.15:
            return 90
        elif roe >= 0.10:
            return 75
        elif roe >= 0.05:
            return 60
        elif roe >= 0.02:
            return 40
        else:
            return max(0, roe * 1000)
    
    def _calculate_cashflow_score(self, balance: float, threshold: float, burn_rate: float) -> float:
        """计算现金流评分 (0-100)"""
        if threshold == 0:
            return 50
        
        # 基于现金余额与安全线的比例
        ratio = balance / threshold
        
        if ratio >= 2.0:
            base_score = 100
        elif ratio >= 1.5:
            base_score = 90
        elif ratio >= 1.0:
            base_score = 75
        elif ratio >= 0.8:
            base_score = 50
        elif ratio >= 0.5:
            base_score = 30
        else:
            base_score = max(0, ratio * 60)
        
        # 考虑消耗率 (runway)
        if burn_rate and burn_rate > 0:
            runway_months = balance / burn_rate
            if runway_months >= 12:
                runway_factor = 1.0
            elif runway_months >= 6:
                runway_factor = 0.9
            elif runway_months >= 3:
                runway_factor = 0.75
            elif runway_months >= 1:
                runway_factor = 0.5
            else:
                runway_factor = 0.3
            
            base_score *= runway_factor
        
        return min(100, base_score)
    
    # ==================== 风险传播分析 ====================
    
    def analyze_risk_propagation(self, risk_id: str, risk_type: str) -> Dict[str, Any]:
        """
        分析风险传播路径和影响范围
        
        Args:
            risk_id: 风险 ID
            risk_type: 风险类型 (CASHFLOW/AR/AP/RATIO/BUDGET)
        
        Returns:
            {
                "risk_id": "...",
                "direct_impacts": [...],
                "indirect_impacts": [...],
                "affected_entities": {
                    "departments": [...],
                    "products": [...],
                    "customers": [...]
                },
                "total_impact_score": 75,
                "propagation_paths": [...]
            }
        """
        with self.driver.session() as session:
            # 根据风险类型查询传播路径
            if risk_type == "CASHFLOW":
                result = self._analyze_cashflow_propagation(session, risk_id)
            elif risk_type == "AR":
                result = self._analyze_ar_propagation(session, risk_id)
            elif risk_type == "AP":
                result = self._analyze_ap_propagation(session, risk_id)
            elif risk_type == "RATIO":
                result = self._analyze_ratio_propagation(session, risk_id)
            elif risk_type == "BUDGET":
                result = self._analyze_budget_propagation(session, risk_id)
            else:
                result = {"error": f"Unknown risk type: {risk_type}"}
            
            return result
    
    def _analyze_cashflow_propagation(self, session, risk_id: str) -> Dict[str, Any]:
        """分析现金流风险传播"""
        # 查询受影响的部门、项目等
        query = """
            MATCH (cf:CashFlow {id: $risk_id})<-[:HAS_CASHFLOW]-(c:Company)
            OPTIONAL MATCH (c)-[:HAS_DEPARTMENT]->(d:Department)
            OPTIONAL MATCH (c)-[:HAS_PROJECT]->(p:Project)
            OPTIONAL MATCH (c)-[:SUPPLIES]->(po:PurchaseOrder)
            WHERE po.payment_status = 'PENDING'
            
            RETURN 
                c.id as company_id,
                c.name as company_name,
                collect(DISTINCT d.name) as departments,
                collect(DISTINCT p.name) as projects,
                count(po) as pending_payments,
                sum(po.amount) as pending_amount
        """
        
        result = session.run(query, risk_id=risk_id)
        record = result.single()
        
        if not record:
            return {"error": "Risk not found"}
        
        return {
            "risk_id": risk_id,
            "risk_type": "CASHFLOW",
            "company_id": record["company_id"],
            "company_name": record["company_name"],
            "direct_impacts": [
                {
                    "type": "department",
                    "entities": record["departments"] or [],
                    "impact_level": "HIGH"
                },
                {
                    "type": "project",
                    "entities": record["projects"] or [],
                    "impact_level": "MEDIUM"
                }
            ],
            "indirect_impacts": [
                {
                    "type": "supplier_payments",
                    "count": record["pending_payments"],
                    "amount": record["pending_amount"] or 0,
                    "impact_level": "HIGH"
                }
            ],
            "affected_entities": {
                "departments": record["departments"] or [],
                "projects": record["projects"] or [],
                "customers": []
            },
            "total_impact_score": min(100, 50 + record["pending_payments"] * 5),
            "propagation_paths": [
                "现金流不足 → 无法支付供应商 → 供应链中断风险",
                "现金流不足 → 项目资金短缺 → 项目延期风险"
            ]
        }
    
    def _analyze_ar_propagation(self, session, risk_id: str) -> Dict[str, Any]:
        """分析应收账款风险传播"""
        query = """
            MATCH (c:Customer)-[:OWES]->(ar:ARTransaction)
            WHERE ar.customer_id = $risk_id OR c.id = $risk_id
            WITH c, sum(ar.amount) as total_owed, count(ar) as tx_count
            
            OPTIONAL MATCH (c)-[:GENERATES]->(s:Sale)
            WHERE s.timestamp >= date() - duration({days: 365})
            
            RETURN 
                c.id as customer_id,
                c.name as customer_name,
                total_owed,
                tx_count,
                count(s) as recent_sales,
                sum(s.amount) as annual_revenue
        """
        
        result = session.run(query, risk_id=risk_id)
        record = result.single()
        
        if not record:
            return {"error": "Risk not found"}
        
        return {
            "risk_id": risk_id,
            "risk_type": "AR",
            "customer_id": record["customer_id"],
            "customer_name": record["customer_name"],
            "direct_impacts": [
                {
                    "type": "cashflow",
                    "description": f"影响现金流 ¥{record['total_owed']:,.0f}",
                    "impact_level": "HIGH"
                }
            ],
            "indirect_impacts": [
                {
                    "type": "revenue_loss",
                    "annual_revenue": record["annual_revenue"] or 0,
                    "risk_level": "MEDIUM" if record["recent_sales"] > 0 else "HIGH"
                }
            ],
            "affected_entities": {
                "departments": ["销售部", "财务部"],
                "products": [],
                "customers": [record["customer_name"]]
            },
            "total_impact_score": min(100, 40 + (record["total_owed"] / 100000)),
            "propagation_paths": [
                "客户逾期 → 现金流减少 → 运营资金紧张",
                "客户逾期 → 坏账风险 → 利润下降"
            ]
        }
    
    def _analyze_ap_propagation(self, session, risk_id: str) -> Dict[str, Any]:
        """分析应付账款风险传播"""
        query = """
            MATCH (s:Supplier)<-[:OWED_BY]-(ap:APTransaction)
            WHERE ap.supplier_id = $risk_id OR s.id = $risk_id
            WITH s, sum(ap.amount) as total_due, count(ap) as tx_count
            WHERE ap.status = 'UNPAID'
            
            OPTIONAL MATCH (s)-[:SUPPLIES]->(po:PurchaseOrder)
            WHERE po.status = 'PENDING'
            
            RETURN 
                s.id as supplier_id,
                s.name as supplier_name,
                total_due,
                tx_count,
                count(po) as pending_orders
        """
        
        result = session.run(query, risk_id=risk_id)
        record = result.single()
        
        if not record:
            return {"error": "Risk not found"}
        
        return {
            "risk_id": risk_id,
            "risk_type": "AP",
            "supplier_id": record["supplier_id"],
            "supplier_name": record["supplier_name"],
            "direct_impacts": [
                {
                    "type": "payment_obligation",
                    "amount": record["total_due"],
                    "impact_level": "HIGH"
                }
            ],
            "indirect_impacts": [
                {
                    "type": "supply_chain",
                    "pending_orders": record["pending_orders"],
                    "risk_level": "MEDIUM" if record["pending_orders"] > 0 else "LOW"
                }
            ],
            "affected_entities": {
                "departments": ["采购部", "财务部"],
                "products": [],
                "suppliers": [record["supplier_name"]]
            },
            "total_impact_score": min(100, 30 + (record["total_due"] / 100000) + record["pending_orders"] * 10),
            "propagation_paths": [
                "应付账款到期 → 现金流压力 → 资金周转困难",
                "无法及时付款 → 供应商关系恶化 → 供应链风险"
            ]
        }
    
    def _analyze_ratio_propagation(self, session, risk_id: str) -> Dict[str, Any]:
        """分析财务比率风险传播"""
        query = """
            MATCH (c:Company)-[:HAS_FINANCIAL_RATIO]->(r:FinancialRatio)
            WHERE r.id = $risk_id OR c.id = $risk_id
            
            RETURN 
                c.id as company_id,
                c.name as company_name,
                r.current_ratio,
                r.debt_to_equity,
                r.roe,
                r.gross_margin
        """
        
        result = session.run(query, risk_id=risk_id)
        record = result.single()
        
        if not record:
            return {"error": "Risk not found"}
        
        risk_factors = []
        if record["current_ratio"] and record["current_ratio"] < 1.0:
            risk_factors.append("流动比率过低")
        if record["debt_to_equity"] and record["debt_to_equity"] > 2.0:
            risk_factors.append("负债权益比过高")
        if record["roe"] and record["roe"] < 0.05:
            risk_factors.append("ROE 过低")
        if record["gross_margin"] and record["gross_margin"] < 0.1:
            risk_factors.append("毛利率过低")
        
        return {
            "risk_id": risk_id,
            "risk_type": "RATIO",
            "company_id": record["company_id"],
            "company_name": record["company_name"],
            "direct_impacts": [
                {
                    "type": "financial_health",
                    "factors": risk_factors,
                    "impact_level": "HIGH" if len(risk_factors) > 2 else "MEDIUM"
                }
            ],
            "indirect_impacts": [
                {
                    "type": "investor_confidence",
                    "risk_level": "MEDIUM"
                },
                {
                    "type": "credit_rating",
                    "risk_level": "MEDIUM" if record["debt_to_equity"] and record["debt_to_equity"] > 2.0 else "LOW"
                }
            ],
            "affected_entities": {
                "departments": ["财务部", "管理层"],
                "products": [],
                "stakeholders": ["股东", "债权人"]
            },
            "total_impact_score": min(100, len(risk_factors) * 25),
            "propagation_paths": [
                "财务比率恶化 → 投资者信心下降 → 融资难度增加",
                "负债过高 → 信用评级下降 → 融资成本上升"
            ]
        }
    
    def _analyze_budget_propagation(self, session, risk_id: str) -> Dict[str, Any]:
        """分析预算偏差风险传播"""
        query = """
            MATCH (d:Department)-[:HAS_BUDGET]->(b:Budget)
            MATCH (d)-[:HAS_ACTUAL]->(a:Actual)
            WHERE b.id = $risk_id OR d.id = $risk_id
            WITH d, b, a, 
                 b.amount as budget, 
                 a.amount as actual,
                 (a.amount - b.amount) / b.amount as variance
            
            RETURN 
                d.id as department_id,
                d.name as department_name,
                budget,
                actual,
                variance,
                d.manager as manager
        """
        
        result = session.run(query, risk_id=risk_id)
        record = result.single()
        
        if not record:
            return {"error": "Risk not found"}
        
        variance_pct = record["variance"] * 100 if record["variance"] else 0
        
        return {
            "risk_id": risk_id,
            "risk_type": "BUDGET",
            "department_id": record["department_id"],
            "department_name": record["department_name"],
            "direct_impacts": [
                {
                    "type": "budget_overrun",
                    "budget": record["budget"],
                    "actual": record["actual"],
                    "variance_pct": round(variance_pct, 2),
                    "impact_level": "HIGH" if abs(variance_pct) > 30 else "MEDIUM"
                }
            ],
            "indirect_impacts": [
                {
                    "type": "profit_margin",
                    "description": "影响公司整体利润率",
                    "impact_level": "MEDIUM"
                }
            ],
            "affected_entities": {
                "departments": [record["department_name"]],
                "projects": [],
                "managers": [record["manager"]] if record["manager"] else []
            },
            "total_impact_score": min(100, abs(variance_pct) * 2),
            "propagation_paths": [
                "预算超支 → 部门费用增加 → 利润率下降",
                "预算偏差 → 需要调整资源分配 → 其他项目受影响"
            ]
        }
    
    # ==================== 财务趋势分析 ====================
    
    def analyze_financial_trend(self, company_id: str, periods: int = 6) -> Dict[str, Any]:
        """
        分析财务趋势 (最近 N 个周期)
        
        Returns:
            {
                "company_id": "...",
                "periods": [...],
                "metrics": {
                    "revenue": [...],
                    "profit": [...],
                    "cashflow": [...]
                },
                "trends": {
                    "revenue_trend": "UP",
                    "profit_trend": "DOWN",
                    "cashflow_trend": "STABLE"
                }
            }
        """
        with self.driver.session() as session:
            # 获取历史财务数据
            query = """
                MATCH (c:Company {id: $company_id})-[:HAS_FINANCIAL_RATIO]->(r:FinancialRatio)
                RETURN r.period as period,
                       r.roe as roe,
                       r.gross_margin as gross_margin,
                       r.current_ratio as current_ratio
                ORDER BY period DESC
                LIMIT $periods
            """
            
            result = session.run(query, company_id=company_id, periods=periods)
            records = list(result)
            
            if not records:
                return {"error": "No historical data found"}
            
            periods = []
            roe_trend = []
            margin_trend = []
            liquidity_trend = []
            
            for record in records:
                periods.append(record["period"])
                roe_trend.append(record["roe"] if record["roe"] else 0)
                margin_trend.append(record["gross_margin"] if record["gross_margin"] else 0)
                liquidity_trend.append(record["current_ratio"] if record["current_ratio"] else 1)
            
            # 判断趋势
            def get_trend(values):
                if len(values) < 2:
                    return "STABLE"
                recent_avg = sum(values[-3:]) / min(3, len(values))
                older_avg = sum(values[:3]) / min(3, len(values))
                
                if recent_avg > older_avg * 1.1:
                    return "UP"
                elif recent_avg < older_avg * 0.9:
                    return "DOWN"
                else:
                    return "STABLE"
            
            return {
                "company_id": company_id,
                "periods": list(reversed(periods)),
                "metrics": {
                    "roe": list(reversed(roe_trend)),
                    "gross_margin": list(reversed(margin_trend)),
                    "current_ratio": list(reversed(liquidity_trend))
                },
                "trends": {
                    "roe_trend": get_trend(roe_trend),
                    "margin_trend": get_trend(margin_trend),
                    "liquidity_trend": get_trend(liquidity_trend)
                },
                "analyzed_at": datetime.now().isoformat()
            }


# 便捷函数
def get_financial_analysis_engine() -> FinancialAnalysisEngine:
    """获取财务分析引擎实例"""
    return FinancialAnalysisEngine()
