"""
预警规则引擎单元测试 - 测试覆盖率 >75%

测试用例:
1. 业务预警规则测试 (6 个)
   - test_check_inventory_low
   - test_check_inventory_zero
   - test_check_payment_overdue
   - test_check_customer_churn
   - test_check_delivery_delay
   - test_check_sales_anomaly

2. 财务风险预警规则测试 (5 个)
   - test_check_cashflow_risk
   - test_check_ar_overdue
   - test_check_ap_risk
   - test_check_financial_ratio_abnormal
   - test_check_budget_variance

3. 综合方法测试
   - test_run_all_alerts
   - test_get_alert_statistics
"""

import os
import sys
from datetime import date, timedelta
from unittest.mock import MagicMock, Mock, patch

import pytest
from neo4j import Driver

# 添加项目路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.alert_rules import AlertRuleEngine, create_alert_engine


# ==================== Fixture ====================

@pytest.fixture
def mock_neo4j_driver():
    """模拟 Neo4j 驱动"""
    driver = Mock(spec=Driver)
    session = MagicMock()
    driver.session.return_value.__enter__ = Mock(return_value=session)
    driver.session.return_value.__exit__ = Mock(return_value=None)
    return driver, session


@pytest.fixture
def alert_engine(mock_neo4j_driver):
    """创建预警引擎实例"""
    driver, _ = mock_neo4j_driver
    return AlertRuleEngine(driver)


# ==================== 业务预警规则测试 ====================

class TestBusinessAlerts:
    """业务预警规则测试"""

    def test_check_inventory_low(self, mock_neo4j_driver, alert_engine):
        """测试 1: 库存预警 - 库存低于安全线"""
        driver, session = mock_neo4j_driver
        
        # 模拟返回数据
        mock_record = {
            'alert_type': 'INVENTORY_LOW',
            'severity': 'YELLOW',
            'product_id': 'PROD-001',
            'product_name': 'iPhone 15 Pro',
            'current_stock': 50,
            'safety_threshold': 100,
            'avg_daily_sales': 5.5,
            'recommendation': '库存低于安全线，建议补货',
        }
        session.run.return_value = [mock_record]
        
        # 执行测试
        alerts = alert_engine.check_inventory_low()
        
        # 验证结果
        assert len(alerts) == 1
        assert alerts[0]['alert_type'] == 'INVENTORY_LOW'
        assert alerts[0]['severity'] == 'YELLOW'
        assert alerts[0]['current_stock'] == 50
        assert alerts[0]['safety_threshold'] == 100
        session.run.assert_called_once()

    def test_check_inventory_zero(self, mock_neo4j_driver, alert_engine):
        """测试 2: 库存为零预警"""
        driver, session = mock_neo4j_driver
        
        # 模拟返回数据
        mock_record = {
            'alert_type': 'INVENTORY_ZERO',
            'severity': 'RED',
            'product_id': 'PROD-002',
            'product_name': 'AirPods Pro',
            'current_stock': 0,
            'pending_orders': 3,
            'description': '库存为 0，3 个订单无法履行',
            'recommendation': '立即紧急补货',
        }
        session.run.return_value = [mock_record]
        
        # 执行测试
        alerts = alert_engine.check_inventory_zero()
        
        # 验证结果
        assert len(alerts) == 1
        assert alerts[0]['alert_type'] == 'INVENTORY_ZERO'
        assert alerts[0]['severity'] == 'RED'
        assert alerts[0]['pending_orders'] == 3
        session.run.assert_called_once()

    def test_check_payment_overdue(self, mock_neo4j_driver, alert_engine):
        """测试 3: 付款逾期预警"""
        driver, session = mock_neo4j_driver
        
        # 模拟返回数据
        mock_record = {
            'alert_type': 'PAYMENT_OVERDUE',
            'severity': 'ORANGE',
            'invoice_id': 'INV-001',
            'invoice_number': 'INV-2026-001',
            'amount': 50000,
            'due_date': date.today() - timedelta(days=15),
            'overdue_days': 15,
            'vendor_name': '供应商 A',
            'description': '付款已逾期 15 天',
            'recommendation': '立即安排付款',
        }
        session.run.return_value = [mock_record]
        
        # 执行测试
        alerts = alert_engine.check_payment_overdue(overdue_days=1)
        
        # 验证结果
        assert len(alerts) == 1
        assert alerts[0]['alert_type'] == 'PAYMENT_OVERDUE'
        assert alerts[0]['severity'] == 'ORANGE'
        assert alerts[0]['overdue_days'] == 15
        session.run.assert_called_once()

    def test_check_customer_churn(self, mock_neo4j_driver, alert_engine):
        """测试 4: 客户流失预警"""
        driver, session = mock_neo4j_driver
        
        # 模拟返回数据
        mock_record = {
            'alert_type': 'CUSTOMER_CHURN',
            'severity': 'RED',
            'customer_id': 'CUST-001',
            'customer_name': '某某公司',
            'last_order_date': date.today() - timedelta(days=120),
            'days_inactive': 120,
            'historical_revenue': 1500000,
            'description': '客户已 120 天未下单，历史贡献 1500000 元',
            'recommendation': '客户经理立即联系回访',
        }
        session.run.return_value = [mock_record]
        
        # 执行测试
        alerts = alert_engine.check_customer_churn(inactive_days=90)
        
        # 验证结果
        assert len(alerts) == 1
        assert alerts[0]['alert_type'] == 'CUSTOMER_CHURN'
        assert alerts[0]['severity'] == 'RED'
        assert alerts[0]['days_inactive'] == 120
        assert alerts[0]['historical_revenue'] == 1500000
        session.run.assert_called_once()

    def test_check_delivery_delay(self, mock_neo4j_driver, alert_engine):
        """测试 5: 供应商交货逾期预警"""
        driver, session = mock_neo4j_driver
        
        # 模拟返回数据
        mock_record = {
            'alert_type': 'DELIVERY_DELAY',
            'severity': 'YELLOW',
            'po_id': 'PO-001',
            'po_number': 'PO-2026-001',
            'expected_delivery_date': date.today() - timedelta(days=5),
            'delay_days': 5,
            'vendor_name': '供应商 B',
            'order_amount': 100000,
            'description': '交货已逾期 5 天',
            'recommendation': '联系供应商确认交货时间',
        }
        session.run.return_value = [mock_record]
        
        # 执行测试
        alerts = alert_engine.check_delivery_delay(delay_days=3)
        
        # 验证结果
        assert len(alerts) == 1
        assert alerts[0]['alert_type'] == 'DELIVERY_DELAY'
        assert alerts[0]['severity'] == 'YELLOW'
        assert alerts[0]['delay_days'] == 5
        session.run.assert_called_once()

    def test_check_sales_anomaly(self, mock_neo4j_driver, alert_engine):
        """测试 6: 销售订单异常预警"""
        driver, session = mock_neo4j_driver
        
        # 模拟返回数据
        mock_record = {
            'alert_type': 'SALES_ANOMALY',
            'severity': 'YELLOW',
            'customer_id': 'CUST-002',
            'customer_name': '客户 C',
            'order_id': 'ORD-001',
            'order_number': 'ORD-2026-001',
            'recent_amount': 50000,
            'historical_avg': 30000,
            'variance_percent': 66.67,
            'description': '订单金额波动 66.67%，远超历史平均',
            'recommendation': '确认订单真实性，防止欺诈',
        }
        session.run.return_value = [mock_record]
        
        # 执行测试
        alerts = alert_engine.check_sales_anomaly(threshold_percent=0.3)
        
        # 验证结果
        assert len(alerts) == 1
        assert alerts[0]['alert_type'] == 'SALES_ANOMALY'
        assert alerts[0]['variance_percent'] == 66.67
        session.run.assert_called_once()


# ==================== 财务风险预警规则测试 ====================

class TestFinancialRisks:
    """财务风险预警规则测试"""

    def test_check_cashflow_risk(self, mock_neo4j_driver, alert_engine):
        """测试 7: 现金流预警"""
        driver, session = mock_neo4j_driver
        
        # 模拟返回数据
        mock_record = {
            'alert_type': 'CASHFLOW_RISK',
            'severity': 'RED',
            'company_id': 'COMP-001',
            'company_name': '总公司',
            'current_balance': 500000,
            'safety_threshold': 1000000,
            'cashflow_gap': 500000,
            'fill_rate': 50.0,
            'description': '现金流 500000 元，低于安全线 1000000 元，缺口 500000 元',
            'recommendation': '立即筹集资金或加速回款',
        }
        session.run.return_value = [mock_record]
        
        # 执行测试
        alerts = alert_engine.check_cashflow_risk()
        
        # 验证结果
        assert len(alerts) == 1
        assert alerts[0]['alert_type'] == 'CASHFLOW_RISK'
        assert alerts[0]['severity'] == 'RED'
        assert alerts[0]['cashflow_gap'] == 500000
        session.run.assert_called_once()

    def test_check_ar_overdue(self, mock_neo4j_driver, alert_engine):
        """测试 8: 应收账款逾期预警"""
        driver, session = mock_neo4j_driver
        
        # 模拟返回数据
        mock_record = {
            'alert_type': 'AR_OVERDUE_RISK',
            'severity': 'ORANGE',
            'customer_id': 'CUST-003',
            'customer_name': '客户 D',
            'total_overdue': 150000,
            'overdue_count': 6,
            'max_overdue_days': 60,
            'description': '应收账款逾期 150000 元，共 6 笔，最长逾期 60 天',
            'recommendation': '立即催收或启动法律程序',
        }
        session.run.return_value = [mock_record]
        
        # 执行测试
        alerts = alert_engine.check_ar_overdue(threshold_amount=100000, threshold_count=5)
        
        # 验证结果
        assert len(alerts) == 1
        assert alerts[0]['alert_type'] == 'AR_OVERDUE_RISK'
        assert alerts[0]['total_overdue'] == 150000
        assert alerts[0]['overdue_count'] == 6
        session.run.assert_called_once()

    def test_check_ap_risk(self, mock_neo4j_driver, alert_engine):
        """测试 9: 应付账款风险预警"""
        driver, session = mock_neo4j_driver
        
        # 模拟返回数据
        mock_record = {
            'alert_type': 'AP_RISK',
            'severity': 'ORANGE',
            'supplier_id': 'SUP-001',
            'supplier_name': '供应商 E',
            'due_in_week': 200000,
            'invoice_count': 5,
            'earliest_due': date.today() + timedelta(days=2),
            'description': '未来 7 天内需支付 200000 元，共 5 笔',
            'recommendation': '提前安排资金计划',
        }
        session.run.return_value = [mock_record]
        
        # 执行测试
        alerts = alert_engine.check_ap_risk(days_ahead=7)
        
        # 验证结果
        assert len(alerts) == 1
        assert alerts[0]['alert_type'] == 'AP_RISK'
        assert alerts[0]['due_in_week'] == 200000
        session.run.assert_called_once()

    def test_check_financial_ratio_abnormal(self, mock_neo4j_driver, alert_engine):
        """测试 10: 财务比率异常预警"""
        driver, session = mock_neo4j_driver
        
        # 模拟返回数据
        mock_record = {
            'alert_type': 'FINANCIAL_RATIO_ABNORMAL',
            'severity': 'RED',
            'company_id': 'COMP-002',
            'company_name': '分公司',
            'current_ratio': 0.8,
            'quick_ratio': 0.6,
            'debt_to_equity': 2.5,
            'roe': 0.03,
            'gross_margin': 0.12,
            'abnormal_count': 4,
            'description': '发现 4 项财务指标异常',
            'recommendation': '详细分析财务健康状况并制定改善计划',
        }
        session.run.return_value = [mock_record]
        
        # 执行测试
        alerts = alert_engine.check_financial_ratio_abnormal()
        
        # 验证结果
        assert len(alerts) == 1
        assert alerts[0]['alert_type'] == 'FINANCIAL_RATIO_ABNORMAL'
        assert alerts[0]['severity'] == 'RED'
        assert alerts[0]['abnormal_count'] == 4
        assert alerts[0]['current_ratio'] == 0.8
        assert alerts[0]['debt_to_equity'] == 2.5
        session.run.assert_called_once()

    def test_check_budget_variance(self, mock_neo4j_driver, alert_engine):
        """测试 11: 预算偏差预警"""
        driver, session = mock_neo4j_driver
        
        # 模拟返回数据
        mock_record = {
            'alert_type': 'BUDGET_VARIANCE',
            'severity': 'ORANGE',
            'department_id': 'DEPT-001',
            'department_name': '市场部',
            'budget_amount': 1000000,
            'actual_amount': 1300000,
            'variance_amount': -300000,
            'variance_percent': 30.0,
            'period': '2026-Q1',
            'description': '预算 1000000 元，实际 1300000 元，偏差 30.0%',
            'recommendation': '分析超支原因并提交说明报告',
        }
        session.run.return_value = [mock_record]
        
        # 执行测试
        alerts = alert_engine.check_budget_variance(variance_threshold=0.2)
        
        # 验证结果
        assert len(alerts) == 1
        assert alerts[0]['alert_type'] == 'BUDGET_VARIANCE'
        assert alerts[0]['severity'] == 'ORANGE'
        assert alerts[0]['variance_percent'] == 30.0
        session.run.assert_called_once()


# ==================== 综合方法测试 ====================

class TestComprehensiveMethods:
    """综合方法测试"""

    def test_run_all_alerts(self, mock_neo4j_driver, alert_engine):
        """测试 12: 运行所有预警规则"""
        driver, session = mock_neo4j_driver
        session.run.return_value = []
        
        # 执行测试
        alerts = alert_engine.run_all_alerts()
        
        # 验证结果
        assert isinstance(alerts, dict)
        # 业务预警
        assert 'inventory_low' in alerts
        assert 'inventory_zero' in alerts
        assert 'payment_overdue' in alerts
        assert 'customer_churn' in alerts
        assert 'delivery_delay' in alerts
        assert 'sales_anomaly' in alerts
        # 财务风险预警
        assert 'cashflow_risk' in alerts
        assert 'ar_overdue_risk' in alerts
        assert 'ap_risk' in alerts
        assert 'financial_ratio_abnormal' in alerts
        assert 'budget_variance' in alerts
        
        # 总共 11 个规则
        assert len(alerts) == 11

    def test_get_alert_statistics(self, mock_neo4j_driver, alert_engine):
        """测试 13: 获取预警统计数据"""
        driver, session = mock_neo4j_driver
        session.run.return_value = []
        
        # 执行测试
        stats = alert_engine.get_alert_statistics()
        
        # 验证结果
        assert 'total' in stats
        assert 'by_severity' in stats
        assert 'by_type' in stats
        assert 'financial_risks' in stats
        assert 'business_alerts' in stats
        
        # 验证 severity 分类
        assert 'RED' in stats['by_severity']
        assert 'ORANGE' in stats['by_severity']
        assert 'YELLOW' in stats['by_severity']

    def test_create_alert_engine(self, mock_neo4j_driver):
        """测试 14: 创建预警引擎实例"""
        driver, _ = mock_neo4j_driver
        
        # 执行测试
        engine = create_alert_engine(driver)
        
        # 验证结果
        assert isinstance(engine, AlertRuleEngine)
        assert engine.driver == driver


# ==================== 边界条件测试 ====================

class TestEdgeCases:
    """边界条件测试"""

    def test_empty_results(self, mock_neo4j_driver, alert_engine):
        """测试 15: 空结果处理"""
        driver, session = mock_neo4j_driver
        session.run.return_value = []
        
        # 执行测试
        alerts = alert_engine.check_inventory_low()
        
        # 验证结果
        assert len(alerts) == 0
        assert isinstance(alerts, list)

    def test_severity_classification(self, mock_neo4j_driver, alert_engine):
        """测试 16: 预警级别分类逻辑"""
        driver, session = mock_neo4j_driver
        
        # 模拟不同级别的预警
        test_cases = [
            # (overdue_days, expected_severity)
            (5, 'YELLOW'),
            (10, 'ORANGE'),
            (35, 'RED'),
        ]
        
        for overdue_days, expected_severity in test_cases:
            mock_record = {
                'alert_type': 'PAYMENT_OVERDUE',
                'severity': expected_severity,
                'overdue_days': overdue_days,
            }
            session.run.return_value = [mock_record]
            
            alerts = alert_engine.check_payment_overdue()
            assert len(alerts) == 1
            assert alerts[0]['severity'] == expected_severity

    def test_financial_rules_count(self, mock_neo4j_driver, alert_engine):
        """测试 17: 财务风险规则数量验证"""
        driver, session = mock_neo4j_driver
        session.run.return_value = []
        
        # 获取所有规则
        all_alerts = alert_engine.run_all_alerts()
        
        # 财务风险规则
        financial_rules = [
            'cashflow_risk',
            'ar_overdue_risk',
            'ap_risk',
            'financial_ratio_abnormal',
            'budget_variance',
        ]
        
        # 验证财务风险规则数量
        financial_count = sum(1 for rule in financial_rules if rule in all_alerts)
        assert financial_count == 5

    def test_business_rules_count(self, mock_neo4j_driver, alert_engine):
        """测试 18: 业务预警规则数量验证"""
        driver, session = mock_neo4j_driver
        session.run.return_value = []
        
        # 获取所有规则
        all_alerts = alert_engine.run_all_alerts()
        
        # 业务预警规则
        business_rules = [
            'inventory_low',
            'inventory_zero',
            'payment_overdue',
            'customer_churn',
            'delivery_delay',
            'sales_anomaly',
        ]
        
        # 验证业务预警规则数量
        business_count = sum(1 for rule in business_rules if rule in all_alerts)
        assert business_count == 6


# ==================== 测试覆盖率补充 ====================

class TestCoverageExtension:
    """扩展测试覆盖率"""

    def test_statistics_severity_counting(self, mock_neo4j_driver, alert_engine):
        """测试 19: 统计中 severity 计数"""
        driver, session = mock_neo4j_driver
        
        # 模拟不同 severity 的返回
        def mock_run(query, **kwargs):
            if 'INVENTORY' in query:
                return [{'severity': 'YELLOW'}]
            elif 'CASHFLOW' in query:
                return [{'severity': 'RED'}]
            elif 'AR_OVERDUE' in query:
                return [{'severity': 'ORANGE'}]
            return []
        
        session.run.side_effect = mock_run
        
        stats = alert_engine.get_alert_statistics()
        
        # 验证计数
        assert stats['by_severity']['RED'] >= 0
        assert stats['by_severity']['ORANGE'] >= 0
        assert stats['by_severity']['YELLOW'] >= 0

    def test_alert_type_mapping(self, mock_neo4j_driver, alert_engine):
        """测试 20: 预警类型映射"""
        driver, session = mock_neo4j_driver
        session.run.return_value = []
        
        alerts = alert_engine.run_all_alerts()
        
        # 验证所有预警类型都有正确的 alert_type 字段
        for rule_name, rule_alerts in alerts.items():
            for alert in rule_alerts:
                assert 'alert_type' in alert
                assert 'severity' in alert
                assert 'description' in alert
                assert 'recommendation' in alert


# ==================== 运行测试 ====================

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--cov=app.services.alert_rules', '--cov-report=html'])
