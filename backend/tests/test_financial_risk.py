"""
财务风险模型测试

测试 5 类财务风险模型：
1. 现金流风险 (CashFlowRisk)
2. 应收账款风险 (ARRisk)
3. 应付账款风险 (APRisk)
4. 财务比率风险 (FinancialRatioRisk)
5. 预算偏差风险 (BudgetVarianceRisk)
"""

import pytest
from datetime import datetime, date
from pydantic import ValidationError

from app.models.financial_risk import (
    CashFlowRisk, ARRisk, APRisk, FinancialRatioRisk,
    BudgetVarianceRisk, RiskSeverity, RiskType,
    ARTransactionRisk, APTransactionRisk,
    FinancialRiskSummary, FinancialRiskResponse
)


class TestCashFlowRisk:
    """现金流风险模型测试"""
    
    def test_create_valid_cashflow_risk(self):
        """测试创建有效的现金流风险"""
        risk = CashFlowRisk(
            id="CFR-001",
            company_id="COMP-001",
            company_name="某某公司",
            current_balance=500000,
            minimum_threshold=1000000,
            severity=RiskSeverity.CRITICAL,
            risk_score=85,
            deficit_amount=500000
        )
        
        assert risk.id == "CFR-001"
        assert risk.company_id == "COMP-001"
        assert risk.current_balance == 500000
        assert risk.severity == RiskSeverity.CRITICAL
        assert risk.risk_score == 85
        assert risk.status == "OPEN"
    
    def test_cashflow_risk_with_runway(self):
        """测试包含剩余天数的现金流风险"""
        risk = CashFlowRisk(
            id="CFR-002",
            company_id="COMP-001",
            company_name="某某公司",
            current_balance=800000,
            minimum_threshold=1000000,
            monthly_burn_rate=200000,
            severity=RiskSeverity.WARNING,
            risk_score=60,
            deficit_amount=200000,
            runway_days=120
        )
        
        assert risk.monthly_burn_rate == 200000
        assert risk.runway_days == 120
    
    def test_cashflow_risk_severity_levels(self):
        """测试不同严重程度的现金流风险"""
        # 高危
        critical = CashFlowRisk(
            id="CFR-C1", company_id="C1", company_name="Test",
            current_balance=100000, minimum_threshold=1000000,
            severity=RiskSeverity.CRITICAL, risk_score=90, deficit_amount=900000
        )
        assert critical.severity == RiskSeverity.CRITICAL
        
        # 警告
        warning = CashFlowRisk(
            id="CFR-W1", company_id="C1", company_name="Test",
            current_balance=600000, minimum_threshold=1000000,
            severity=RiskSeverity.WARNING, risk_score=60, deficit_amount=400000
        )
        assert warning.severity == RiskSeverity.WARNING
        
        # 提示
        info = CashFlowRisk(
            id="CFR-I1", company_id="C1", company_name="Test",
            current_balance=900000, minimum_threshold=1000000,
            severity=RiskSeverity.INFO, risk_score=40, deficit_amount=100000
        )
        assert info.severity == RiskSeverity.INFO
    
    def test_cashflow_risk_risk_score_range(self):
        """测试风险评分范围验证"""
        # 有效范围
        risk = CashFlowRisk(
            id="CFR-003", company_id="C1", company_name="Test",
            current_balance=500000, minimum_threshold=1000000,
            severity=RiskSeverity.WARNING, risk_score=0, deficit_amount=500000
        )
        assert risk.risk_score == 0
        
        risk = CashFlowRisk(
            id="CFR-004", company_id="C1", company_name="Test",
            current_balance=500000, minimum_threshold=1000000,
            severity=RiskSeverity.WARNING, risk_score=100, deficit_amount=500000
        )
        assert risk.risk_score == 100
        
        # 超出范围应该失败
        with pytest.raises(ValidationError):
            CashFlowRisk(
                id="CFR-005", company_id="C1", company_name="Test",
                current_balance=500000, minimum_threshold=1000000,
                severity=RiskSeverity.WARNING, risk_score=101, deficit_amount=500000
            )
    
    def test_cashflow_risk_status_transitions(self):
        """测试状态转换"""
        risk = CashFlowRisk(
            id="CFR-006", company_id="C1", company_name="Test",
            current_balance=500000, minimum_threshold=1000000,
            severity=RiskSeverity.WARNING, risk_score=60, deficit_amount=500000,
            status="OPEN"
        )
        assert risk.status == "OPEN"
        
        risk.status = "IN_PROGRESS"
        assert risk.status == "IN_PROGRESS"
        
        risk.status = "RESOLVED"
        assert risk.status == "RESOLVED"


class TestARRisk:
    """应收账款风险模型测试"""
    
    def test_create_valid_ar_risk(self):
        """测试创建有效的应收账款风险"""
        risk = ARRisk(
            id="ARR-001",
            customer_id="CUST-001",
            customer_name="A 公司",
            total_overdue_amount=1200000,
            overdue_count=5,
            max_overdue_days=90,
            avg_overdue_days=45,
            severity=RiskSeverity.WARNING,
            risk_score=70
        )
        
        assert risk.id == "ARR-001"
        assert risk.total_overdue_amount == 1200000
        assert risk.overdue_count == 5
        assert risk.severity == RiskSeverity.WARNING
    
    def test_ar_risk_with_transactions(self):
        """测试包含交易详情的应收账款风险"""
        transactions = [
            ARTransactionRisk(
                transaction_id="TXN-001",
                customer_id="CUST-001",
                customer_name="A 公司",
                amount=300000,
                due_date=date(2026, 2, 1),
                overdue_days=60,
                status="UNPAID"
            ),
            ARTransactionRisk(
                transaction_id="TXN-002",
                customer_id="CUST-001",
                customer_name="A 公司",
                amount=200000,
                due_date=date(2026, 3, 1),
                overdue_days=30,
                status="UNPAID"
            )
        ]
        
        risk = ARRisk(
            id="ARR-002",
            customer_id="CUST-001",
            customer_name="A 公司",
            total_overdue_amount=500000,
            overdue_count=2,
            max_overdue_days=60,
            avg_overdue_days=45,
            severity=RiskSeverity.WARNING,
            risk_score=65,
            transactions=transactions
        )
        
        assert len(risk.transactions) == 2
        assert risk.transactions[0].amount == 300000
        assert risk.transactions[1].overdue_days == 30
    
    def test_ar_risk_severity_calculation(self):
        """测试严重程度分级"""
        # 高危 - 大额逾期
        high_risk = ARRisk(
            id="ARR-H1", customer_id="C1", customer_name="Test",
            total_overdue_amount=1000000, overdue_count=10,
            max_overdue_days=120, avg_overdue_days=60,
            severity=RiskSeverity.CRITICAL, risk_score=90
        )
        assert high_risk.severity == RiskSeverity.CRITICAL
        
        # 警告 - 中等逾期
        medium_risk = ARRisk(
            id="ARR-M1", customer_id="C1", customer_name="Test",
            total_overdue_amount=200000, overdue_count=3,
            max_overdue_days=45, avg_overdue_days=30,
            severity=RiskSeverity.WARNING, risk_score=60
        )
        assert medium_risk.severity == RiskSeverity.WARNING


class TestAPRisk:
    """应付账款风险模型测试"""
    
    def test_create_valid_ap_risk(self):
        """测试创建有效的应付账款风险"""
        risk = APRisk(
            id="APR-001",
            supplier_id="SUP-001",
            supplier_name="某某供应商",
            total_due_amount=800000,
            due_in_week_amount=300000,
            due_in_month_amount=600000,
            transaction_count=5,
            severity=RiskSeverity.WARNING,
            risk_score=60
        )
        
        assert risk.id == "APR-001"
        assert risk.total_due_amount == 800000
        assert risk.due_in_week_amount == 300000
        assert risk.severity == RiskSeverity.WARNING
    
    def test_ap_risk_with_transactions(self):
        """测试包含交易详情的应付账款风险"""
        transactions = [
            APTransactionRisk(
                transaction_id="AP-001",
                supplier_id="SUP-001",
                supplier_name="供应商 A",
                amount=200000,
                due_date=date(2026, 4, 10),
                days_until_due=5,
                status="UNPAID"
            ),
            APTransactionRisk(
                transaction_id="AP-002",
                supplier_id="SUP-001",
                supplier_name="供应商 A",
                amount=150000,
                due_date=date(2026, 4, 20),
                days_until_due=15,
                status="UNPAID"
            )
        ]
        
        risk = APRisk(
            id="APR-002",
            supplier_id="SUP-001",
            supplier_name="供应商 A",
            total_due_amount=350000,
            due_in_week_amount=200000,
            due_in_month_amount=350000,
            transaction_count=2,
            severity=RiskSeverity.WARNING,
            risk_score=55,
            transactions=transactions
        )
        
        assert len(risk.transactions) == 2
        assert risk.transactions[0].days_until_due == 5


class TestFinancialRatioRisk:
    """财务比率风险模型测试"""
    
    def test_create_valid_ratio_risk(self):
        """测试创建有效的财务比率风险"""
        risk = FinancialRatioRisk(
            id="FRR-001",
            company_id="COMP-001",
            company_name="某某公司",
            current_ratio=0.8,
            quick_ratio=0.6,
            debt_to_equity=2.5,
            roe=0.03,
            roi=0.05,
            gross_margin=0.15,
            severity=RiskSeverity.WARNING,
            risk_score=65,
            period="2026-Q1"
        )
        
        assert risk.current_ratio == 0.8
        assert risk.debt_to_equity == 2.5
        assert risk.roe == 0.03
        assert risk.severity == RiskSeverity.WARNING
    
    def test_ratio_risk_factors(self):
        """测试风险因素列表"""
        risk = FinancialRatioRisk(
            id="FRR-002",
            company_id="COMP-001",
            company_name="某某公司",
            current_ratio=0.8,
            debt_to_equity=2.5,
            roe=0.03,
            severity=RiskSeverity.WARNING,
            risk_score=65,
            period="2026-Q1",
            risk_factors=[
                "流动比率低于 1.0",
                "负债权益比高于 2.0",
                "ROE 低于 5%"
            ]
        )
        
        assert len(risk.risk_factors) == 3
        assert "流动比率低于 1.0" in risk.risk_factors
    
    def test_ratio_risk_thresholds(self):
        """测试阈值配置"""
        risk = FinancialRatioRisk(
            id="FRR-003",
            company_id="COMP-001",
            company_name="某某公司",
            current_ratio=0.8,
            debt_to_equity=2.5,
            roe=0.03,
            severity=RiskSeverity.WARNING,
            risk_score=65,
            period="2026-Q1",
            thresholds={
                "current_ratio_min": 1.0,
                "debt_to_equity_max": 2.0,
                "roe_min": 0.05
            }
        )
        
        assert risk.thresholds["current_ratio_min"] == 1.0
        assert risk.thresholds["debt_to_equity_max"] == 2.0


class TestBudgetVarianceRisk:
    """预算偏差风险模型测试"""
    
    def test_create_valid_budget_risk(self):
        """测试创建有效的预算偏差风险"""
        risk = BudgetVarianceRisk(
            id="BVR-001",
            department_id="DEPT-001",
            department_name="市场部",
            budget_amount=1000000,
            actual_amount=1300000,
            variance_amount=300000,
            variance_percentage=0.3,
            severity=RiskSeverity.WARNING,
            risk_score=60,
            period="2026-Q1"
        )
        
        assert risk.budget_amount == 1000000
        assert risk.actual_amount == 1300000
        assert risk.variance_percentage == 0.3
        assert risk.severity == RiskSeverity.WARNING
    
    def test_budget_risk_variance_calculation(self):
        """测试偏差计算"""
        # 超支
        overrun = BudgetVarianceRisk(
            id="BVR-O1", department_id="D1", department_name="Test",
            budget_amount=1000000, actual_amount=1200000,
            variance_amount=200000, variance_percentage=0.2,
            severity=RiskSeverity.WARNING, risk_score=50,
            period="2026-Q1"
        )
        assert overrun.variance_percentage == 0.2
        assert overrun.variance_amount == 200000
        
        # 节约
        underrun = BudgetVarianceRisk(
            id="BVR-U1", department_id="D1", department_name="Test",
            budget_amount=1000000, actual_amount=800000,
            variance_amount=-200000, variance_percentage=-0.2,
            severity=RiskSeverity.INFO, risk_score=20,
            period="2026-Q1"
        )
        assert underrun.variance_percentage == -0.2


class TestFinancialRiskSummary:
    """财务风险汇总测试"""
    
    def test_create_risk_summary(self):
        """测试创建风险汇总"""
        summary = FinancialRiskSummary(
            total_risks=12,
            critical_count=2,
            warning_count=5,
            info_count=5,
            cashflow_risks=3,
            ar_risks=4,
            ap_risks=2,
            ratio_risks=2,
            budget_risks=1,
            overall_health_score=65
        )
        
        assert summary.total_risks == 12
        assert summary.critical_count == 2
        assert summary.overall_health_score == 65
    
    def test_risk_summary_validation(self):
        """测试汇总数据验证"""
        # 总数应该等于各分类之和
        summary = FinancialRiskSummary(
            total_risks=12,
            critical_count=2,
            warning_count=5,
            info_count=5,
            cashflow_risks=3,
            ar_risks=4,
            ap_risks=2,
            ratio_risks=2,
            budget_risks=1,
            overall_health_score=65
        )
        
        # 验证分类总和
        category_sum = (
            summary.cashflow_risks +
            summary.ar_risks +
            summary.ap_risks +
            summary.ratio_risks +
            summary.budget_risks
        )
        assert category_sum == 12
        assert category_sum == summary.total_risks


class TestRiskSeverityEnum:
    """风险严重程度枚举测试"""
    
    def test_severity_values(self):
        """测试枚举值"""
        assert RiskSeverity.CRITICAL.value == "CRITICAL"
        assert RiskSeverity.WARNING.value == "WARNING"
        assert RiskSeverity.INFO.value == "INFO"
    
    def test_severity_comparison(self):
        """测试枚举比较"""
        assert RiskSeverity.CRITICAL != RiskSeverity.WARNING
        assert RiskSeverity.WARNING == RiskSeverity.WARNING


class TestFinancialRiskResponse:
    """API 响应模型测试"""
    
    def test_create_success_response(self):
        """测试创建成功响应"""
        response = FinancialRiskResponse(
            success=True,
            data={"risk_id": "CFR-001"},
            message="获取成功"
        )
        
        assert response.success is True
        assert response.data["risk_id"] == "CFR-001"
        assert response.message == "获取成功"
    
    def test_create_error_response(self):
        """测试创建错误响应"""
        response = FinancialRiskResponse(
            success=False,
            data=None,
            message="数据不存在"
        )
        
        assert response.success is False
        assert response.data is None
        assert response.message == "数据不存在"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
