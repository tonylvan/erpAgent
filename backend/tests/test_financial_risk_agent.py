# -*- coding: utf-8 -*-
"""
财务风险检测 Agent 单元测试
测试用例：25+
"""

import unittest
from unittest.mock import Mock, MagicMock
from datetime import datetime
import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agents.financial_risk_agent import (
    FinancialRiskAgent,
    DatabaseConnection,
    FinancialRiskReport,
    RiskSeverity,
    RiskType,
    run_financial_risk_detection,
    get_financial_risk_agent
)


class TestDataFactory:
    """测试数据工厂"""
    
    @staticmethod
    def create_cashflow_data(total_cash=1000000, monthly_expenses=300000,
                             monthly_budget=280000, ocf_m1=50000, ocf_m2=50000, ocf_m3=50000):
        return [{
            "company_id": "COMP-001", "company_name": "测试公司",
            "total_cash": total_cash, "monthly_operating_expenses": monthly_expenses,
            "monthly_budget": monthly_budget,
            "operating_cashflow_m1": ocf_m1, "operating_cashflow_m2": ocf_m2,
            "operating_cashflow_m3": ocf_m3
        }]
    
    @staticmethod
    def create_ar_data(total_ar=2000000, overdue_ar=500000, dso=65, max_overdue_days=120):
        return [{
            "company_id": "COMP-001", "company_name": "测试公司",
            "total_ar": total_ar, "overdue_ar": overdue_ar,
            "dso": dso, "max_overdue_days": max_overdue_days
        }]
    
    @staticmethod
    def create_customer_ar_data(overdue_amount=1500000, max_overdue_days=95, ar_90plus_amount=600000):
        return [{
            "customer_id": "CUST-001", "customer_name": "测试客户",
            "overdue_amount": overdue_amount, "max_overdue_days": max_overdue_days,
            "ar_90plus_amount": ar_90plus_amount
        }]
    
    @staticmethod
    def create_ap_data(ap_due_7days=400000, cash_reserve=600000, dpo=70):
        return [{
            "company_id": "COMP-001", "company_name": "测试公司",
            "total_ap": 1500000, "ap_due_in_7days": ap_due_7days,
            "cash_reserve": cash_reserve, "dpo": dpo
        }]
    
    @staticmethod
    def create_supplier_data():
        return [
            {"supplier_id": "SUP-001", "supplier_name": "供应商 A", "total_purchase": 500000,
             "purchase_rank": 1, "overdue_payment_amount": 100000, "overdue_days": 45},
            {"supplier_id": "SUP-002", "supplier_name": "供应商 B", "total_purchase": 400000,
             "purchase_rank": 2, "overdue_payment_amount": 0, "overdue_days": 0},
            {"supplier_id": "SUP-003", "supplier_name": "供应商 C", "total_purchase": 300000,
             "purchase_rank": 3, "overdue_payment_amount": 50000, "overdue_days": 15},
            {"supplier_id": "SUP-004", "supplier_name": "供应商 D", "total_purchase": 200000,
             "purchase_rank": 4, "overdue_payment_amount": 0, "overdue_days": 0},
            {"supplier_id": "SUP-005", "supplier_name": "供应商 E", "total_purchase": 100000,
             "purchase_rank": 5, "overdue_payment_amount": 0, "overdue_days": 0}
        ]
    
    @staticmethod
    def create_ratio_data(current_ratio=0.9, quick_ratio=0.7, debt_to_equity=2.5,
                          roe=0.03, roi=0.05):
        return [{
            "company_id": "COMP-001", "company_name": "测试公司",
            "current_ratio": current_ratio, "quick_ratio": quick_ratio,
            "debt_to_equity": debt_to_equity, "roe": roe, "roi": roi,
            "total_liabilities": 7000000, "equity": 3000000
        }]
    
    @staticmethod
    def create_dept_budget_data(budget=1000000, actual=1300000, prev_actual=800000):
        return [{
            "company_id": "COMP-001", "company_name": "测试公司",
            "department_id": "DEPT-001", "department_name": "市场部",
            "budget_amount": budget, "actual_amount": actual,
            "prev_month_actual": prev_actual
        }]
    
    @staticmethod
    def create_project_budget_data(budget_cost=500000, actual_cost=700000):
        return [{
            "company_id": "COMP-001", "company_name": "测试公司",
            "project_id": "PROJ-001", "project_name": "新产品开发",
            "budget_cost": budget_cost, "actual_cost": actual_cost
        }]
    
    @staticmethod
    def create_revenue_budget_data(budget_revenue=2000000, actual_revenue=1500000):
        return [{
            "company_id": "COMP-001", "company_name": "测试公司",
            "budget_revenue": budget_revenue, "actual_revenue": actual_revenue
        }]


class TestFinancialRiskReport(unittest.TestCase):
    """测试 FinancialRiskReport 类"""
    
    def test_create_report(self):
        report = FinancialRiskReport(
            risk_type="cashflow_critical", severity="CRITICAL",
            description="现金余额低于安全线", data={"current_cash": 500000},
            recommendation="加速收款", impact="资金链风险"
        )
        self.assertEqual(report.agent, "financial_risk")
        self.assertEqual(report.risk_type, "cashflow_critical")
        self.assertEqual(report.severity, "CRITICAL")
        self.assertIsNotNone(report.created_at)
    
    def test_report_to_dict(self):
        report = FinancialRiskReport(
            risk_type="ar_overdue_rate", severity="HIGH",
            description="应收账款逾期率过高", data={"overdue_rate": 0.25},
            recommendation="加强催收", impact="回款能力问题"
        )
        result = report.to_dict()
        self.assertIn("agent", result)
        self.assertIn("risk_type", result)
        self.assertEqual(result["risk_type"], "ar_overdue_rate")
    
    def test_report_to_json(self):
        report = FinancialRiskReport(
            risk_type="ratio_current", severity="WARNING",
            description="流动比率过低", data={"current_ratio": 1.2},
            recommendation="优化资产结构", impact="偿债能力不足"
        )
        json_str = report.to_json()
        parsed = json.loads(json_str)
        self.assertEqual(parsed["risk_type"], "ratio_current")


class TestCashFlowRiskDetection(unittest.TestCase):
    """测试现金流风险检测 (4 条规则)"""
    
    def setUp(self):
        self.agent = FinancialRiskAgent()
        self.agent.db = Mock()
    
    def test_rule_1_1_critical(self):
        """规则 1.1: CRITICAL (< 1 个月)"""
        self.agent.db.execute_pg_query = Mock(return_value=TestDataFactory.create_cashflow_data(
            total_cash=200000, monthly_expenses=300000))
        self.agent._detect_cashflow_risks()
        risk = next((r for r in self.agent.risks if r.risk_type == "cashflow_critical"), None)
        self.assertIsNotNone(risk)
        self.assertEqual(risk.severity, RiskSeverity.CRITICAL.value)
    
    def test_rule_1_1_high(self):
        """规则 1.1: HIGH (< 2 个月)"""
        self.agent.db.execute_pg_query = Mock(return_value=TestDataFactory.create_cashflow_data(
            total_cash=500000, monthly_expenses=300000))
        self.agent._detect_cashflow_risks()
        risk = next((r for r in self.agent.risks if r.risk_type == "cashflow_critical"), None)
        self.assertIsNotNone(risk)
        self.assertEqual(risk.severity, RiskSeverity.HIGH.value)
    
    def test_rule_1_1_medium(self):
        """规则 1.1: MEDIUM (< 3 个月)"""
        self.agent.db.execute_pg_query = Mock(return_value=TestDataFactory.create_cashflow_data(
            total_cash=700000, monthly_expenses=300000))
        self.agent._detect_cashflow_risks()
        risk = next((r for r in self.agent.risks if r.risk_type == "cashflow_critical"), None)
        self.assertIsNotNone(risk)
        self.assertEqual(risk.severity, RiskSeverity.MEDIUM.value)
    
    def test_rule_1_2_burn_rate(self):
        """规则 1.2: 现金消耗率超标"""
        self.agent.db.execute_pg_query = Mock(return_value=TestDataFactory.create_cashflow_data(
            total_cash=2000000, monthly_expenses=360000, monthly_budget=280000))
        self.agent._detect_cashflow_risks()
        risk = next((r for r in self.agent.risks if r.risk_type == "cashflow_burn_rate"), None)
        self.assertIsNotNone(risk)
        self.assertEqual(risk.severity, RiskSeverity.HIGH.value)
    
    def test_rule_1_3_runway_critical(self):
        """规则 1.3: Runway CRITICAL (< 3 个月)"""
        self.agent.db.execute_pg_query = Mock(return_value=TestDataFactory.create_cashflow_data(
            total_cash=600000, monthly_expenses=300000))
        self.agent._detect_cashflow_risks()
        risk = next((r for r in self.agent.risks if r.risk_type == "cashflow_runway"), None)
        self.assertIsNotNone(risk)
        self.assertEqual(risk.severity, RiskSeverity.CRITICAL.value)
    
    def test_rule_1_3_runway_high(self):
        """规则 1.3: Runway HIGH (< 6 个月)"""
        self.agent.db.execute_pg_query = Mock(return_value=TestDataFactory.create_cashflow_data(
            total_cash=1200000, monthly_expenses=300000))
        self.agent._detect_cashflow_risks()
        risk = next((r for r in self.agent.risks if r.risk_type == "cashflow_runway"), None)
        self.assertIsNotNone(risk)
        self.assertEqual(risk.severity, RiskSeverity.HIGH.value)
    
    def test_rule_1_4_negative_cashflow(self):
        """规则 1.4: 经营性现金流为负"""
        self.agent.db.execute_pg_query = Mock(return_value=TestDataFactory.create_cashflow_data(
            total_cash=2000000, monthly_expenses=300000,
            ocf_m1=-50000, ocf_m2=-60000, ocf_m3=-70000))
        self.agent._detect_cashflow_risks()
        risk = next((r for r in self.agent.risks if r.risk_type == "cashflow_negative"), None)
        self.assertIsNotNone(risk)
        self.assertEqual(risk.severity, RiskSeverity.HIGH.value)


class TestARRiskDetection(unittest.TestCase):
    """测试应收账款风险检测 (4 条规则)"""
    
    def setUp(self):
        self.agent = FinancialRiskAgent()
        self.agent.db = Mock()
    
    def test_rule_2_1_overdue_rate(self):
        """规则 2.1: 逾期率过高"""
        self.agent.db.execute_pg_query = Mock(side_effect=[
            TestDataFactory.create_ar_data(total_ar=2000000, overdue_ar=500000), []
        ])
        self.agent._detect_ar_risks()
        risk = next((r for r in self.agent.risks if r.risk_type == "ar_overdue_rate"), None)
        self.assertIsNotNone(risk)
        self.assertEqual(risk.severity, RiskSeverity.HIGH.value)
    
    def test_rule_2_2_concentration(self):
        """规则 2.2: 单一客户逾期过大"""
        self.agent.db.execute_pg_query = Mock(side_effect=[
            [], TestDataFactory.create_customer_ar_data(overdue_amount=1500000)
        ])
        self.agent._detect_ar_risks()
        risk = next((r for r in self.agent.risks if r.risk_type == "ar_concentration"), None)
        self.assertIsNotNone(risk)
        self.assertEqual(risk.severity, RiskSeverity.HIGH.value)
    
    def test_rule_2_3_dso(self):
        """规则 2.3: DSO 过长"""
        self.agent.db.execute_pg_query = Mock(side_effect=[
            TestDataFactory.create_ar_data(dso=75), []
        ])
        self.agent._detect_ar_risks()
        risk = next((r for r in self.agent.risks if r.risk_type == "ar_dso"), None)
        self.assertIsNotNone(risk)
        self.assertEqual(risk.severity, RiskSeverity.MEDIUM.value)
    
    def test_rule_2_4_bad_debt(self):
        """规则 2.4: 坏账风险"""
        self.agent.db.execute_pg_query = Mock(side_effect=[
            [], TestDataFactory.create_customer_ar_data(max_overdue_days=95, ar_90plus_amount=600000)
        ])
        self.agent._detect_ar_risks()
        risk = next((r for r in self.agent.risks if r.risk_type == "ar_bad_debt"), None)
        self.assertIsNotNone(risk)
        self.assertEqual(risk.severity, RiskSeverity.CRITICAL.value)


class TestAPRiskDetection(unittest.TestCase):
    """测试应付账款风险检测 (4 条规则)"""
    
    def setUp(self):
        self.agent = FinancialRiskAgent()
        self.agent.db = Mock()
    
    def test_rule_3_1_payment_pressure(self):
        """规则 3.1: 付款压力"""
        self.agent.db.execute_pg_query = Mock(side_effect=[
            TestDataFactory.create_ap_data(ap_due_7days=400000, cash_reserve=600000), []
        ])
        self.agent._detect_ap_risks()
        risk = next((r for r in self.agent.risks if r.risk_type == "ap_payment_pressure"), None)
        self.assertIsNotNone(risk)
        self.assertEqual(risk.severity, RiskSeverity.HIGH.value)
    
    def test_rule_3_2_supplier_concentration(self):
        """规则 3.2: 供应商集中度"""
        self.agent.db.execute_pg_query = Mock(side_effect=[[], TestDataFactory.create_supplier_data()])
        self.agent._detect_ap_risks()
        risk = next((r for r in self.agent.risks if r.risk_type == "ap_supplier_concentration"), None)
        self.assertIsNotNone(risk)
        self.assertEqual(risk.severity, RiskSeverity.MEDIUM.value)
    
    def test_rule_3_3_overdue_payment(self):
        """规则 3.3: 逾期付款"""
        self.agent.db.execute_pg_query = Mock(side_effect=[[], TestDataFactory.create_supplier_data()])
        self.agent._detect_ap_risks()
        risks = [r for r in self.agent.risks if r.risk_type == "ap_overdue_payment"]
        self.assertEqual(len(risks), 2)
    
    def test_rule_3_4_dpo_abnormal(self):
        """规则 3.4: DPO 异常"""
        self.agent.db.execute_pg_query = Mock(side_effect=[
            TestDataFactory.create_ap_data(dpo=70), []
        ])
        self.agent._detect_ap_risks()
        risk = next((r for r in self.agent.risks if r.risk_type == "ap_dpo_abnormal"), None)
        self.assertIsNotNone(risk)
        self.assertEqual(risk.severity, RiskSeverity.MEDIUM.value)


class TestRatioRiskDetection(unittest.TestCase):
    """测试财务比率异常检测 (4 条规则)"""
    
    def setUp(self):
        self.agent = FinancialRiskAgent()
        self.agent.db = Mock()
    
    def test_rule_4_1_current_critical(self):
        """规则 4.1: 流动比率 CRITICAL (< 1.0)"""
        self.agent.db.execute_pg_query = Mock(return_value=TestDataFactory.create_ratio_data(current_ratio=0.8))
        self.agent._detect_ratio_risks()
        risk = next((r for r in self.agent.risks if r.risk_type == "ratio_current"), None)
        self.assertIsNotNone(risk)
        self.assertEqual(risk.severity, RiskSeverity.CRITICAL.value)
    
    def test_rule_4_1_current_warning(self):
        """规则 4.1: 流动比率 WARNING (< 1.5)"""
        self.agent.db.execute_pg_query = Mock(return_value=TestDataFactory.create_ratio_data(current_ratio=1.2))
        self.agent._detect_ratio_risks()
        risk = next((r for r in self.agent.risks if r.risk_type == "ratio_current"), None)
        self.assertIsNotNone(risk)
        self.assertEqual(risk.severity, RiskSeverity.WARNING.value)
    
    def test_rule_4_2_debt_equity_critical(self):
        """规则 4.2: 负债权益比 CRITICAL (> 3.0)"""
        self.agent.db.execute_pg_query = Mock(return_value=TestDataFactory.create_ratio_data(debt_to_equity=3.5))
        self.agent._detect_ratio_risks()
        risk = next((r for r in self.agent.risks if r.risk_type == "ratio_debt_equity"), None)
        self.assertIsNotNone(risk)
        self.assertEqual(risk.severity, RiskSeverity.CRITICAL.value)
    
    def test_rule_4_2_debt_equity_high(self):
        """规则 4.2: 负债权益比 HIGH (> 2.0)"""
        self.agent.db.execute_pg_query = Mock(return_value=TestDataFactory.create_ratio_data(debt_to_equity=2.5))
        self.agent._detect_ratio_risks()
        risk = next((r for r in self.agent.risks if r.risk_type == "ratio_debt_equity"), None)
        self.assertIsNotNone(risk)
        self.assertEqual(risk.severity, RiskSeverity.HIGH.value)
    
    def test_rule_4_3_roe(self):
        """规则 4.3: ROE 过低"""
        self.agent.db.execute_pg_query = Mock(return_value=TestDataFactory.create_ratio_data(roe=0.03))
        self.agent._detect_ratio_risks()
        risk = next((r for r in self.agent.risks if r.risk_type == "ratio_roe"), None)
        self.assertIsNotNone(risk)
        self.assertEqual(risk.severity, RiskSeverity.WARNING.value)
    
    def test_rule_4_4_roi(self):
        """规则 4.4: ROI 过低"""
        self.agent.db.execute_pg_query = Mock(return_value=TestDataFactory.create_ratio_data(roi=0.05))
        self.agent._detect_ratio_risks()
        risk = next((r for r in self.agent.risks if r.risk_type == "ratio_roi"), None)
        self.assertIsNotNone(risk)
        self.assertEqual(risk.severity, RiskSeverity.MEDIUM.value)


class TestBudgetRiskDetection(unittest.TestCase):
    """测试预算偏差风险检测 (4 条规则)"""
    
    def setUp(self):
        self.agent = FinancialRiskAgent()
        self.agent.db = Mock()
    
    def test_rule_5_1_department_over_budget(self):
        """规则 5.1: 部门超预算"""
        self.agent.db.execute_pg_query = Mock(side_effect=[
            TestDataFactory.create_dept_budget_data(budget=1000000, actual=1300000), [], []
        ])
        self.agent._detect_budget_risks()
        risk = next((r for r in self.agent.risks if r.risk_type == "budget_department"), None)
        self.assertIsNotNone(risk)
    
    def test_rule_5_2_project_overrun(self):
        """规则 5.2: 项目超支"""
        self.agent.db.execute_pg_query = Mock(side_effect=[
            [], TestDataFactory.create_project_budget_data(budget_cost=500000, actual_cost=700000), []
        ])
        self.agent._detect_budget_risks()
        risk = next((r for r in self.agent.risks if r.risk_type == "budget_project"), None)
        self.assertIsNotNone(risk)
        self.assertEqual(risk.severity, RiskSeverity.HIGH.value)
    
    def test_rule_5_3_expense_growth(self):
        """规则 5.3: 费用异常增长"""
        self.agent.db.execute_pg_query = Mock(side_effect=[
            TestDataFactory.create_dept_budget_data(budget=1000000, actual=1300000, prev_actual=800000),
            [], []
        ])
        self.agent._detect_budget_risks()
        risk = next((r for r in self.agent.risks if r.risk_type == "budget_growth"), None)
        self.assertIsNotNone(risk)
    
    def test_rule_5_4_revenue_below_budget(self):
        """规则 5.4: 收入未达预算"""
        self.agent.db.execute_pg_query = Mock(side_effect=[
            [], [], TestDataFactory.create_revenue_budget_data(budget_revenue=2000000, actual_revenue=1500000)
        ])
        self.agent._detect_budget_risks()
        risk = next((r for r in self.agent.risks if r.risk_type == "budget_revenue"), None)
        self.assertIsNotNone(risk)
        self.assertEqual(risk.severity, RiskSeverity.HIGH.value)


class TestBoundaryConditions(unittest.TestCase):
    """测试边界条件"""
    
    def setUp(self):
        self.agent = FinancialRiskAgent()
        self.agent.db = Mock()
    
    def test_zero_values_no_error(self):
        """测试零值 - 不抛出异常"""
        self.agent.db.execute_pg_query = Mock(return_value=TestDataFactory.create_cashflow_data(
            total_cash=0, monthly_expenses=0))
        try:
            self.agent._detect_cashflow_risks()
            success = True
        except Exception:
            success = False
        self.assertTrue(success)
    
    def test_null_data_handling(self):
        """测试 None 数据处理"""
        self.agent.db.execute_pg_query = Mock(return_value=[{
            "company_id": "COMP-001", "company_name": "测试公司",
            "total_cash": None, "monthly_operating_expenses": None,
            "monthly_budget": None, "operating_cashflow_m1": None,
            "operating_cashflow_m2": None, "operating_cashflow_m3": None
        }])
        try:
            self.agent._detect_cashflow_risks()
            success = True
        except TypeError:
            success = False
        self.assertTrue(success)
    
    def test_empty_result(self):
        """测试空结果"""
        self.agent.db.execute_pg_query = Mock(return_value=[])
        self.agent._detect_cashflow_risks()
        self.assertEqual(len(self.agent.risks), 0)
    
    def test_boundary_current_ratio_1_0(self):
        """边界：流动比率 = 1.0 (触发 WARNING，因为 1.0 < 1.5)"""
        self.agent.db.execute_pg_query = Mock(return_value=TestDataFactory.create_ratio_data(current_ratio=1.0))
        self.agent._detect_ratio_risks()
        risk = next((r for r in self.agent.risks if r.risk_type == "ratio_current"), None)
        self.assertIsNotNone(risk)
        self.assertEqual(risk.severity, RiskSeverity.WARNING.value)
    
    def test_boundary_current_ratio_0_99(self):
        """边界：流动比率 = 0.99 (触发 CRITICAL)"""
        self.agent.db.execute_pg_query = Mock(return_value=TestDataFactory.create_ratio_data(current_ratio=0.99))
        self.agent._detect_ratio_risks()
        risk = next((r for r in self.agent.risks if r.risk_type == "ratio_current"), None)
        self.assertIsNotNone(risk)
        self.assertEqual(risk.severity, RiskSeverity.CRITICAL.value)
    
    def test_boundary_overdue_rate_20_percent(self):
        """边界：逾期率 = 20% (不触发)"""
        self.agent.db.execute_pg_query = Mock(side_effect=[
            TestDataFactory.create_ar_data(total_ar=1000000, overdue_ar=200000), []
        ])
        self.agent._detect_ar_risks()
        risk = next((r for r in self.agent.risks if r.risk_type == "ar_overdue_rate"), None)
        self.assertIsNone(risk)


class TestRiskSummary(unittest.TestCase):
    """测试风险汇总"""
    
    def setUp(self):
        self.agent = FinancialRiskAgent()
    
    def test_summary_empty(self):
        summary = self.agent.get_risk_summary()
        self.assertEqual(summary["total"], 0)
    
    def test_summary_with_risks(self):
        self.agent.risks = [
            FinancialRiskReport("cashflow_critical", "CRITICAL", "测试", {}, "建议", "影响"),
            FinancialRiskReport("cashflow_critical", "CRITICAL", "测试", {}, "建议", "影响"),
            FinancialRiskReport("ar_overdue_rate", "HIGH", "测试", {}, "建议", "影响"),
            FinancialRiskReport("ratio_current", "WARNING", "测试", {}, "建议", "影响"),
        ]
        summary = self.agent.get_risk_summary()
        self.assertEqual(summary["total"], 4)
        self.assertEqual(summary["critical_count"], 2)
        self.assertEqual(summary["high_count"], 1)
        self.assertEqual(summary["warning_count"], 1)


class TestConvenienceFunctions(unittest.TestCase):
    """测试便捷函数"""
    
    def test_get_agent(self):
        agent = get_financial_risk_agent()
        self.assertIsInstance(agent, FinancialRiskAgent)


if __name__ == "__main__":
    unittest.main(verbosity=2)
