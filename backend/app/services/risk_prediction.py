"""
风险预测模型

基于 Neo4j 图谱和历史数据进行财务风险预测

功能：
1. 现金流预测
2. 应收账款逾期预测
3. 财务风险综合预测
"""

from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, date, timedelta
from neo4j import GraphDatabase
import asyncio
from enum import Enum


class PredictionConfidence(str, Enum):
    """预测置信度"""
    HIGH = "HIGH"      # >80%
    MEDIUM = "MEDIUM"  # 60-80%
    LOW = "LOW"        # <60%


class RiskPredictionEngine:
    """风险预测引擎"""
    
    def __init__(self, neo4j_uri: str = "bolt://127.0.0.1:7687",
                 neo4j_user: str = "neo4j",
                 neo4j_password: str = "neo4j"):
        self.neo4j_uri = neo4j_uri
        self.driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
    
    def close(self):
        """关闭数据库连接"""
        if self.driver:
            self.driver.close()
    
    # ==================== 现金流预测 ====================
    
    def predict_cashflow_risk(self, company_id: str, days: int = 30) -> Dict[str, Any]:
        """
        预测未来 N 天的现金流风险
        
        Returns:
            {
                "company_id": "...",
                "prediction_days": 30,
                "current_balance": 500000,
                "predicted_balance": 200000,
                "risk_probability": 0.75,
                "confidence": "HIGH",
                "risk_factors": [...],
                "recommendations": [...]
            }
        """
        with self.driver.session() as session:
            # 获取当前现金流数据
            cashflow_query = """
                MATCH (c:Company {id: $company_id})-[:HAS_CASHFLOW]->(cf:CashFlow)
                RETURN cf.balance as current_balance,
                       cf.minimum_threshold as threshold,
                       cf.monthly_burn_rate as burn_rate,
                       cf.inflow_30d as inflow_30d,
                       cf.outflow_30d as outflow_30d
            """
            
            result = session.run(cashflow_query, company_id=company_id)
            record = result.single()
            
            if not record:
                return {
                    "error": "No cashflow data found",
                    "company_id": company_id
                }
            
            current_balance = record["current_balance"] or 0
            threshold = record["threshold"] or 1000000
            burn_rate = record["burn_rate"] or 0
            inflow_30d = record["inflow_30d"] or 0
            outflow_30d = record["outflow_30d"] or 0
            
            # 计算日均流入流出
            daily_inflow = inflow_30d / 30 if inflow_30d else 0
            daily_outflow = outflow_30d / 30 if outflow_30d else 0
            
            # 如果没有 burn_rate，使用 outflow - inflow 估算
            if burn_rate == 0:
                burn_rate = max(0, daily_outflow - daily_inflow) * 30
            
            # 预测未来现金流
            predicted_days = days
            predicted_balance = current_balance - (burn_rate * (days / 30))
            
            # 计算风险概率
            if predicted_balance <= 0:
                risk_probability = 1.0
            elif predicted_balance < threshold * 0.5:
                risk_probability = 0.85
            elif predicted_balance < threshold:
                risk_probability = 0.65
            elif predicted_balance < threshold * 1.5:
                risk_probability = 0.35
            else:
                risk_probability = 0.15
            
            # 确定置信度
            if inflow_30d and outflow_30d:
                confidence = PredictionConfidence.HIGH
            elif current_balance:
                confidence = PredictionConfidence.MEDIUM
            else:
                confidence = PredictionConfidence.LOW
            
            # 识别风险因素
            risk_factors = []
            if burn_rate > 0:
                risk_factors.append(f"月消耗率：¥{burn_rate:,.0f}")
            if predicted_balance < threshold:
                risk_factors.append(f"预测余额低于安全线 ¥{threshold:,.0f}")
            if daily_outflow > daily_inflow * 1.2:
                risk_factors.append("流出显著大于流入")
            
            # 生成建议
            recommendations = []
            if risk_probability > 0.7:
                recommendations.append("🔴 立即启动融资或加快回款")
                recommendations.append("🔴 审查并削减非必要支出")
            elif risk_probability > 0.5:
                recommendations.append("⚠️ 优化应收账款管理")
                recommendations.append("⚠️ 与供应商协商延长账期")
            else:
                recommendations.append("✅ 维持当前现金流管理策略")
            
            # 计算安全天数
            if burn_rate > 0:
                runway_days = int(current_balance / (burn_rate / 30))
            else:
                runway_days = 999
            
            return {
                "company_id": company_id,
                "prediction_days": days,
                "current_balance": current_balance,
                "predicted_balance": max(0, predicted_balance),
                "minimum_threshold": threshold,
                "risk_probability": round(risk_probability, 2),
                "confidence": confidence.value,
                "risk_factors": risk_factors,
                "recommendations": recommendations,
                "metrics": {
                    "daily_inflow": round(daily_inflow, 2),
                    "daily_outflow": round(daily_outflow, 2),
                    "monthly_burn_rate": round(burn_rate, 2),
                    "runway_days": runway_days
                },
                "predicted_at": datetime.now().isoformat()
            }
    
    # ==================== 应收账款逾期预测 ====================
    
    def predict_ar_risk(self, customer_id: str, days: int = 30) -> Dict[str, Any]:
        """
        预测客户应收账款逾期风险
        
        Returns:
            {
                "customer_id": "...",
                "current_overdue": 120000,
                "predicted_overdue": 200000,
                "risk_probability": 0.70,
                "confidence": "MEDIUM",
                "risk_factors": [...],
                "recommendations": [...]
            }
        """
        with self.driver.session() as session:
            # 获取客户历史和当前应收账款数据
            ar_query = """
                MATCH (c:Customer {id: $customer_id})-[:OWES]->(ar:ARTransaction)
                WITH c, 
                     sum(CASE WHEN ar.status = 'UNPAID' AND ar.due_date < date() THEN ar.amount ELSE 0 END) as current_overdue,
                     sum(CASE WHEN ar.status = 'UNPAID' THEN ar.amount ELSE 0 END) as total_receivable,
                     count(CASE WHEN ar.due_date < date() AND ar.status = 'UNPAID' THEN 1 END) as overdue_count,
                     avg(CASE WHEN ar.status = 'PAID' THEN ar.days_to_pay ELSE null END) as avg_payment_days
                RETURN c.name as customer_name,
                       current_overdue,
                       total_receivable,
                       overdue_count,
                       avg_payment_days
            """
            
            result = session.run(ar_query, customer_id=customer_id)
            record = result.single()
            
            if not record:
                return {
                    "error": "No AR data found",
                    "customer_id": customer_id
                }
            
            current_overdue = record["current_overdue"] or 0
            total_receivable = record["total_receivable"] or 0
            overdue_count = record["overdue_count"] or 0
            avg_payment_days = record["avg_payment_days"] or 30
            
            # 预测未来逾期
            # 基于历史逾期率和平均付款天数
            if total_receivable > 0:
                overdue_rate = current_overdue / total_receivable
            else:
                overdue_rate = 0
            
            # 预测未来 30 天新增逾期
            predicted_new_overdue = (total_receivable - current_overdue) * min(overdue_rate * 2, 0.5)
            predicted_total_overdue = current_overdue + predicted_new_overdue
            
            # 计算风险概率
            if overdue_count > 10 or current_overdue > 500000:
                risk_probability = 0.90
            elif overdue_count > 5 or current_overdue > 200000:
                risk_probability = 0.75
            elif overdue_count > 2 or current_overdue > 100000:
                risk_probability = 0.60
            elif overdue_count > 0 or current_overdue > 50000:
                risk_probability = 0.40
            else:
                risk_probability = 0.20
            
            # 调整基于付款行为
            if avg_payment_days > 60:
                risk_probability = min(1.0, risk_probability + 0.15)
            elif avg_payment_days > 45:
                risk_probability = min(1.0, risk_probability + 0.08)
            
            # 确定置信度
            if overdue_count > 5 and total_receivable > 100000:
                confidence = PredictionConfidence.HIGH
            elif overdue_count > 0 or total_receivable > 50000:
                confidence = PredictionConfidence.MEDIUM
            else:
                confidence = PredictionConfidence.LOW
            
            # 风险因素
            risk_factors = []
            if current_overdue > 0:
                risk_factors.append(f"当前逾期：¥{current_overdue:,.0f}")
            if overdue_count > 0:
                risk_factors.append(f"逾期笔数：{overdue_count}")
            if avg_payment_days > 45:
                risk_factors.append(f"平均付款天数：{avg_payment_days:.0f}天 (偏长)")
            
            # 建议
            recommendations = []
            if risk_probability > 0.7:
                recommendations.append("🔴 立即联系客户催收")
                recommendations.append("🔴 考虑暂停赊销或要求预付款")
            elif risk_probability > 0.5:
                recommendations.append("⚠️ 加强跟进频率")
                recommendations.append("⚠️ 重新评估信用额度")
            else:
                recommendations.append("✅ 维持正常对账流程")
            
            return {
                "customer_id": customer_id,
                "customer_name": record["customer_name"],
                "prediction_days": days,
                "current_overdue": current_overdue,
                "predicted_overdue": round(predicted_total_overdue, 2),
                "total_receivable": total_receivable,
                "risk_probability": round(risk_probability, 2),
                "confidence": confidence.value,
                "risk_factors": risk_factors,
                "recommendations": recommendations,
                "metrics": {
                    "overdue_count": overdue_count,
                    "avg_payment_days": round(avg_payment_days, 1),
                    "overdue_rate": round(overdue_rate, 3)
                },
                "predicted_at": datetime.now().isoformat()
            }
    
    # ==================== 财务风险综合预测 ====================
    
    def predict_financial_risk(self, company_id: str, days: int = 30) -> Dict[str, Any]:
        """
        综合财务风险预测
        
        Returns:
            {
                "company_id": "...",
                "overall_risk_score": 65,
                "risk_level": "MEDIUM",
                "category_scores": {
                    "cashflow": 70,
                    "ar": 60,
                    "ap": 50,
                    "ratio": 55
                },
                "predictions": [...],
                "recommendations": [...]
            }
        """
        with self.driver.session() as session:
            # 获取公司综合财务数据
            query = """
                MATCH (c:Company {id: $company_id})
                OPTIONAL MATCH (c)-[:HAS_CASHFLOW]->(cf:CashFlow)
                OPTIONAL MATCH (c)-[:HAS_FINANCIAL_RATIO]->(r:FinancialRatio)
                
                // 应收账款
                OPTIONAL MATCH (c)-[:HAS_CUSTOMER]->(cust:Customer)
                OPTIONAL MATCH (cust)-[:OWES]->(ar:ARTransaction)
                WHERE ar.status = 'UNPAID'
                
                // 应付账款
                OPTIONAL MATCH (c)-[:HAS_SUPPLIER]->(sup:Supplier)
                OPTIONAL MATCH (sup)<-[:OWED_BY]-(ap:APTransaction)
                WHERE ap.status = 'UNPAID'
                
                RETURN 
                    cf.balance as cash_balance,
                    cf.minimum_threshold as cash_threshold,
                    r.current_ratio as current_ratio,
                    r.debt_to_equity as debt_to_equity,
                    r.roe as roe,
                    sum(CASE WHEN ar.due_date < date() THEN ar.amount ELSE 0 END) as overdue_ar,
                    sum(ap.amount) as total_ap,
                    sum(CASE WHEN ap.due_date < date() + duration({days: 7}) THEN ap.amount ELSE 0 END) as ap_due_soon
            """
            
            result = session.run(query, company_id=company_id)
            record = result.single()
            
            if not record:
                return {
                    "error": "No financial data found",
                    "company_id": company_id
                }
            
            # 计算各类别风险评分 (0-100, 越高越危险)
            category_scores = {}
            
            # 1. 现金流风险评分
            cash_balance = record["cash_balance"] or 0
            cash_threshold = record["cash_threshold"] or 1000000
            
            if cash_balance <= 0:
                category_scores["cashflow"] = 100
            elif cash_balance < cash_threshold * 0.5:
                category_scores["cashflow"] = 85
            elif cash_balance < cash_threshold:
                category_scores["cashflow"] = 65
            elif cash_balance < cash_threshold * 1.5:
                category_scores["cashflow"] = 40
            else:
                category_scores["cashflow"] = 20
            
            # 2. 应收账款风险评分
            overdue_ar = record["overdue_ar"] or 0
            if overdue_ar > 500000:
                category_scores["ar"] = 80
            elif overdue_ar > 200000:
                category_scores["ar"] = 65
            elif overdue_ar > 100000:
                category_scores["ar"] = 50
            elif overdue_ar > 50000:
                category_scores["ar"] = 35
            else:
                category_scores["ar"] = 20
            
            # 3. 应付账款风险评分
            total_ap = record["total_ap"] or 0
            ap_due_soon = record["ap_due_soon"] or 0
            
            if ap_due_soon > cash_balance and cash_balance > 0:
                category_scores["ap"] = 85
            elif ap_due_soon > cash_balance * 0.8:
                category_scores["ap"] = 70
            elif total_ap > cash_balance * 2:
                category_scores["ap"] = 55
            else:
                category_scores["ap"] = 30
            
            # 4. 财务比率风险评分
            current_ratio = record["current_ratio"] or 1.5
            debt_to_equity = record["debt_to_equity"] or 1.5
            roe = record["roe"] or 0.05
            
            ratio_score = 0
            if current_ratio < 1.0:
                ratio_score += 35
            elif current_ratio < 1.2:
                ratio_score += 20
            
            if debt_to_equity > 2.5:
                ratio_score += 35
            elif debt_to_equity > 2.0:
                ratio_score += 20
            
            if roe < 0.03:
                ratio_score += 30
            elif roe < 0.05:
                ratio_score += 15
            
            category_scores["ratio"] = min(100, ratio_score)
            
            # 计算综合风险评分
            overall_risk_score = (
                category_scores["cashflow"] * 0.35 +
                category_scores["ar"] * 0.25 +
                category_scores["ap"] * 0.20 +
                category_scores["ratio"] * 0.20
            )
            
            # 确定风险等级
            if overall_risk_score >= 80:
                risk_level = "CRITICAL"
            elif overall_risk_score >= 60:
                risk_level = "HIGH"
            elif overall_risk_score >= 40:
                risk_level = "MEDIUM"
            elif overall_risk_score >= 20:
                risk_level = "LOW"
            else:
                risk_level = "MINIMAL"
            
            # 生成预测详情
            predictions = []
            
            if category_scores["cashflow"] > 50:
                predictions.append({
                    "category": "现金流",
                    "risk_score": category_scores["cashflow"],
                    "trend": "需要关注",
                    "description": f"当前余额 ¥{cash_balance:,.0f}, 安全线 ¥{cash_threshold:,.0f}"
                })
            
            if category_scores["ar"] > 50:
                predictions.append({
                    "category": "应收账款",
                    "risk_score": category_scores["ar"],
                    "trend": "风险较高",
                    "description": f"逾期金额 ¥{overdue_ar:,.0f}"
                })
            
            if category_scores["ap"] > 50:
                predictions.append({
                    "category": "应付账款",
                    "risk_score": category_scores["ap"],
                    "trend": "支付压力大",
                    "description": f"7 天内到期 ¥{ap_due_soon:,.0f}"
                })
            
            if category_scores["ratio"] > 50:
                predictions.append({
                    "category": "财务比率",
                    "risk_score": category_scores["ratio"],
                    "trend": "指标不佳",
                    "description": f"流动比率 {current_ratio:.2f}, 负债权益比 {debt_to_equity:.2f}"
                })
            
            # 生成建议
            recommendations = []
            if category_scores["cashflow"] > 60:
                recommendations.append("🔴 优先保障现金流：加快回款、控制支出")
            if category_scores["ar"] > 60:
                recommendations.append("🔴 加强应收账款管理：催收逾期款项")
            if category_scores["ap"] > 60:
                recommendations.append("⚠️ 合理安排付款计划：避免集中支付")
            if category_scores["ratio"] > 60:
                recommendations.append("⚠️ 优化财务结构：降低负债比例")
            
            if not recommendations:
                recommendations.append("✅ 财务状况良好，维持当前策略")
            
            return {
                "company_id": company_id,
                "prediction_days": days,
                "overall_risk_score": round(overall_risk_score, 2),
                "risk_level": risk_level,
                "category_scores": {k: round(v, 2) for k, v in category_scores.items()},
                "predictions": predictions,
                "recommendations": recommendations,
                "metrics": {
                    "cash_balance": cash_balance,
                    "cash_threshold": cash_threshold,
                    "current_ratio": current_ratio,
                    "debt_to_equity": debt_to_equity,
                    "roe": roe,
                    "overdue_ar": overdue_ar,
                    "total_ap": total_ap,
                    "ap_due_soon": ap_due_soon
                },
                "predicted_at": datetime.now().isoformat()
            }
    
    # ==================== 批量预测 ====================
    
    def batch_predict_risks(self, company_ids: List[str], days: int = 30) -> Dict[str, Any]:
        """
        批量预测多个公司的财务风险
        
        Returns:
            {
                "predictions": [...],
                "summary": {
                    "total_companies": 10,
                    "high_risk_count": 2,
                    "medium_risk_count": 5,
                    "low_risk_count": 3,
                    "avg_risk_score": 52.5
                }
            }
        """
        predictions = []
        risk_scores = []
        
        for company_id in company_ids:
            try:
                pred = self.predict_financial_risk(company_id, days)
                if "error" not in pred:
                    predictions.append(pred)
                    risk_scores.append(pred["overall_risk_score"])
            except Exception as e:
                predictions.append({
                    "company_id": company_id,
                    "error": str(e)
                })
        
        # 汇总统计
        high_risk = sum(1 for p in predictions if p.get("risk_level") in ["CRITICAL", "HIGH"])
        medium_risk = sum(1 for p in predictions if p.get("risk_level") == "MEDIUM")
        low_risk = sum(1 for p in predictions if p.get("risk_level") in ["LOW", "MINIMAL"])
        
        avg_score = sum(risk_scores) / len(risk_scores) if risk_scores else 0
        
        return {
            "predictions": predictions,
            "summary": {
                "total_companies": len(predictions),
                "high_risk_count": high_risk,
                "medium_risk_count": medium_risk,
                "low_risk_count": low_risk,
                "avg_risk_score": round(avg_score, 2)
            },
            "predicted_at": datetime.now().isoformat()
        }


# 便捷函数
def get_risk_prediction_engine() -> RiskPredictionEngine:
    """获取风险预测引擎实例"""
    return RiskPredictionEngine()
