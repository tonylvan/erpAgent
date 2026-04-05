# -*- coding: utf-8 -*-
"""业务风险检测 Agent 单元测试"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date, timedelta

from app.agents.business_risk_agent import (
    BusinessRiskAgent, BusinessRiskAlert, RiskSeverity, RiskType,
    BusinessRiskCategory, RISK_TYPE_CATEGORY_MAP,
    get_business_risk_agent, detect_business_risks
)


def create_mock_cursor(rows):
    mock_cursor = Mock()
    mock_cursor.fetchall.return_value = rows
    mock_cursor.execute = Mock()
    mock_cursor.close = Mock()
    return mock_cursor


def create_mock_connection(rows):
    mock_conn = Mock()
    mock_conn.cursor.return_value = create_mock_cursor(rows)
    return mock_conn


def create_mock_pool(conn):
    mock_pool = Mock()
    mock_pool.getconn.return_value = conn
    mock_pool.putconn = Mock()
    mock_pool.closeall = Mock()
    return mock_pool


class TestBusinessRiskAlert:
    def test_alert_creation(self):
        alert = BusinessRiskAlert(risk_type=RiskType.INVENTORY_LOW.value, severity=RiskSeverity.HIGH.value,
            description="测试", data={"key": "value"})
        assert alert.agent == "business_risk"
        assert alert.risk_type == RiskType.INVENTORY_LOW.value
        assert alert.severity == RiskSeverity.HIGH.value
        assert alert.category == BusinessRiskCategory.INVENTORY.value
        assert alert.data == {"key": "value"}
        assert alert.created_at is not None
    
    def test_alert_to_dict(self):
        alert = BusinessRiskAlert(risk_type=RiskType.PURCHASE_DELIVERY_DELAY.value, severity=RiskSeverity.CRITICAL.value)
        result = alert.to_dict()
        assert result["agent"] == "business_risk"
        assert result["risk_type"] == RiskType.PURCHASE_DELIVERY_DELAY.value
    
    def test_alert_to_json(self):
        import json
        alert = BusinessRiskAlert(risk_type=RiskType.SALES_RETURN_HIGH.value, severity=RiskSeverity.MEDIUM.value)
        json_str = alert.to_json()
        parsed = json.loads(json_str)
        assert parsed["risk_type"] == RiskType.SALES_RETURN_HIGH.value


class TestInventoryRiskDetection:
    @patch('app.agents.business_risk_agent.pool.SimpleConnectionPool')
    def test_check_inventory_low_critical(self, mock_pool_cls):
        rows = [(123, "iPhone 15", "IP15", 30, 100, 1, "主仓库")]
        mock_pool = create_mock_pool(create_mock_connection(rows))
        mock_pool_cls.return_value = mock_pool
        
        agent = BusinessRiskAgent()
        alerts = agent._check_inventory_low()
        
        assert len(alerts) == 1
        assert alerts[0].risk_type == RiskType.INVENTORY_LOW.value
        assert alerts[0].severity == RiskSeverity.CRITICAL.value
        assert alerts[0].data["current_stock"] == 30
        assert alerts[0].data["safety_stock"] == 100
        agent.close()
    
    @patch('app.agents.business_risk_agent.pool.SimpleConnectionPool')
    def test_check_inventory_low_high(self, mock_pool_cls):
        rows = [(124, "iPhone 15", "IP15", 60, 100, 1, "主仓库")]
        mock_pool = create_mock_pool(create_mock_connection(rows))
        mock_pool_cls.return_value = mock_pool
        
        agent = BusinessRiskAgent()
        alerts = agent._check_inventory_low()
        
        assert len(alerts) == 1
        assert alerts[0].severity == RiskSeverity.HIGH.value
        agent.close()
    
    @patch('app.agents.business_risk_agent.pool.SimpleConnectionPool')
    def test_check_inventory_low_multiple(self, mock_pool_cls):
        rows = [(123, "A", "A001", 20, 100, 1, "W1"), (124, "B", "B001", 50, 100, 1, "W1"), (125, "C", "C001", 85, 100, 1, "W1")]
        mock_pool = create_mock_pool(create_mock_connection(rows))
        mock_pool_cls.return_value = mock_pool
        
        agent = BusinessRiskAgent()
        alerts = agent._check_inventory_low()
        
        assert len(alerts) == 3
        assert alerts[0].severity == RiskSeverity.CRITICAL.value
        agent.close()
    
    @patch('app.agents.business_risk_agent.pool.SimpleConnectionPool')
    def test_check_inventory_turnover_low(self, mock_pool_cls):
        rows = [(123, "商品 A", "A001", 50000, 100000, 0.5)]
        mock_pool = create_mock_pool(create_mock_connection(rows))
        mock_pool_cls.return_value = mock_pool
        
        agent = BusinessRiskAgent()
        alerts = agent._check_inventory_turnover_low()
        
        assert len(alerts) == 1
        assert alerts[0].risk_type == RiskType.INVENTORY_TURNOVER_LOW.value
        agent.close()
    
    @patch('app.agents.business_risk_agent.pool.SimpleConnectionPool')
    def test_check_inventory_slow_moving(self, mock_pool_cls):
        rows = [(123, "滞销品", "SLOW001", 100, 500, 50000)]
        mock_pool = create_mock_pool(create_mock_connection(rows))
        mock_pool_cls.return_value = mock_pool
        
        agent = BusinessRiskAgent()
        alerts = agent._check_inventory_slow_moving()
        
        assert len(alerts) == 1
        assert alerts[0].risk_type == RiskType.INVENTORY_SLOW_MOVING.value
        agent.close()
    
    @patch('app.agents.business_risk_agent.pool.SimpleConnectionPool')
    def test_check_inventory_overstock(self, mock_pool_cls):
        rows = [(123, "积压品", "OVER001", 1000, 300)]
        mock_pool = create_mock_pool(create_mock_connection(rows))
        mock_pool_cls.return_value = mock_pool
        
        agent = BusinessRiskAgent()
        alerts = agent._check_inventory_overstock()
        
        assert len(alerts) == 1
        assert alerts[0].risk_type == RiskType.INVENTORY_OVERSTOCK.value
        agent.close()


class TestPurchaseRiskDetection:
    @patch('app.agents.business_risk_agent.pool.SimpleConnectionPool')
    def test_check_purchase_delivery_delay_critical(self, mock_pool_cls):
        rows = [(1, "PO-001", date(2026, 3, 1), 100000, 101, "供应商 A", 35)]
        mock_pool = create_mock_pool(create_mock_connection(rows))
        mock_pool_cls.return_value = mock_pool
        
        agent = BusinessRiskAgent()
        alerts = agent._check_purchase_delivery_delay()
        
        assert len(alerts) == 1
        assert alerts[0].severity == RiskSeverity.CRITICAL.value
        assert alerts[0].data["delay_days"] == 35
        agent.close()
    
    @patch('app.agents.business_risk_agent.pool.SimpleConnectionPool')
    def test_check_purchase_delivery_delay_high(self, mock_pool_cls):
        rows = [(1, "PO-001", date(2026, 3, 20), 50000, 101, "供应商 A", 10)]
        mock_pool = create_mock_pool(create_mock_connection(rows))
        mock_pool_cls.return_value = mock_pool
        
        agent = BusinessRiskAgent()
        alerts = agent._check_purchase_delivery_delay()
        
        assert len(alerts) == 1
        assert alerts[0].severity == RiskSeverity.HIGH.value
        agent.close()
    
    @patch('app.agents.business_risk_agent.pool.SimpleConnectionPool')
    def test_check_purchase_price_fluctuation(self, mock_pool_cls):
        rows = [(123, "商品 A", 135.0, 100.0, 35.0)]
        mock_pool = create_mock_pool(create_mock_connection(rows))
        mock_pool_cls.return_value = mock_pool
        
        agent = BusinessRiskAgent()
        alerts = agent._check_purchase_price_fluctuation()
        
        assert len(alerts) == 1
        assert alerts[0].risk_type == RiskType.PURCHASE_PRICE_FLUCTUATION.value
        agent.close()
    
    @patch('app.agents.business_risk_agent.pool.SimpleConnectionPool')
    def test_check_purchase_single_supplier(self, mock_pool_cls):
        rows = [(101, "供应商 A", 850000, 1000000, 85.0)]
        mock_pool = create_mock_pool(create_mock_connection(rows))
        mock_pool_cls.return_value = mock_pool
        
        agent = BusinessRiskAgent()
        alerts = agent._check_purchase_single_supplier()
        
        assert len(alerts) == 1
        assert alerts[0].severity == RiskSeverity.HIGH.value
        agent.close()
    
    @patch('app.agents.business_risk_agent.pool.SimpleConnectionPool')
    def test_check_purchase_order_cancel(self, mock_pool_cls):
        rows = [(101, "供应商 A", 20, 5, 25.0)]
        mock_pool = create_mock_pool(create_mock_connection(rows))
        mock_pool_cls.return_value = mock_pool
        
        agent = BusinessRiskAgent()
        alerts = agent._check_purchase_order_cancel()
        
        assert len(alerts) == 1
        assert alerts[0].risk_type == RiskType.PURCHASE_ORDER_CANCEL.value
        agent.close()


class TestSalesRiskDetection:
    @patch('app.agents.business_risk_agent.pool.SimpleConnectionPool')
    def test_check_sales_order_cancel(self, mock_pool_cls):
        rows = [(201, "客户 A", 50, 10, 20.0)]
        mock_pool = create_mock_pool(create_mock_connection(rows))
        mock_pool_cls.return_value = mock_pool
        
        agent = BusinessRiskAgent()
        alerts = agent._check_sales_order_cancel()
        
        assert len(alerts) == 1
        assert alerts[0].risk_type == RiskType.SALES_ORDER_CANCEL.value
        agent.close()
    
    @patch('app.agents.business_risk_agent.pool.SimpleConnectionPool')
    def test_check_sales_return_high_critical(self, mock_pool_cls):
        rows = [(201, "客户 A", 100000, 35000, 35.0)]
        mock_pool = create_mock_pool(create_mock_connection(rows))
        mock_pool_cls.return_value = mock_pool
        
        agent = BusinessRiskAgent()
        alerts = agent._check_sales_return_high()
        
        assert len(alerts) == 1
        assert alerts[0].severity == RiskSeverity.CRITICAL.value
        agent.close()
    
    @patch('app.agents.business_risk_agent.pool.SimpleConnectionPool')
    def test_check_sales_decline(self, mock_pool_cls):
        rows = [(201, "客户 A", 100000, 40000, -60.0)]
        mock_pool = create_mock_pool(create_mock_connection(rows))
        mock_pool_cls.return_value = mock_pool
        
        agent = BusinessRiskAgent()
        alerts = agent._check_sales_decline()
        
        assert len(alerts) == 1
        assert alerts[0].risk_type == RiskType.SALES_DECLINE.value
        agent.close()
    
    @patch('app.agents.business_risk_agent.pool.SimpleConnectionPool')
    def test_check_sales_customer_lost(self, mock_pool_cls):
        rows = [(201, "大客户 A", 600000)]
        mock_pool = create_mock_pool(create_mock_connection(rows))
        mock_pool_cls.return_value = mock_pool
        
        agent = BusinessRiskAgent()
        alerts = agent._check_sales_customer_lost()
        
        assert len(alerts) == 1
        assert alerts[0].severity == RiskSeverity.CRITICAL.value
        agent.close()


class TestPaymentRiskDetection:
    @patch('app.agents.business_risk_agent.pool.SimpleConnectionPool')
    def test_check_payment_duplicate_critical(self, mock_pool_cls):
        rows = [(101, "供应商 A", 50000, 5, [1,2,3,4,5], date(2026,4,1), date(2026,4,5))]
        mock_pool = create_mock_pool(create_mock_connection(rows))
        mock_pool_cls.return_value = mock_pool
        
        agent = BusinessRiskAgent()
        alerts = agent._check_payment_duplicate()
        
        assert len(alerts) == 1
        assert alerts[0].severity == RiskSeverity.CRITICAL.value
        assert alerts[0].data["payment_count"] == 5
        agent.close()
    
    @patch('app.agents.business_risk_agent.pool.SimpleConnectionPool')
    def test_check_payment_invoice_mismatch(self, mock_pool_cls):
        rows = [(1, "PAY-001", 101, "供应商 A", 11500, 10000, "INV-001", 1500, 15.0)]
        mock_pool = create_mock_pool(create_mock_connection(rows))
        mock_pool_cls.return_value = mock_pool
        
        agent = BusinessRiskAgent()
        alerts = agent._check_payment_invoice_mismatch()
        
        assert len(alerts) == 1
        assert alerts[0].risk_type == RiskType.PAYMENT_INVOICE_MISMATCH.value
        agent.close()
    
    @patch('app.agents.business_risk_agent.pool.SimpleConnectionPool')
    def test_check_payment_abnormal_large(self, mock_pool_cls):
        rows = [(1, "PAY-001", 101, "供应商 A", 250000, date(2026,4,1), 10000, 25.0)]
        mock_pool = create_mock_pool(create_mock_connection(rows))
        mock_pool_cls.return_value = mock_pool
        
        agent = BusinessRiskAgent()
        alerts = agent._check_payment_abnormal_large()
        
        assert len(alerts) == 1
        assert alerts[0].risk_type == RiskType.PAYMENT_ABNORMAL_LARGE.value
        agent.close()


class TestNeo4jAnalysis:
    @patch('app.agents.business_risk_agent.GraphDatabase')
    def test_analyze_supplier_risk_graph_high_risk(self, mock_db):
        mock_result = Mock()
        mock_result.single.return_value = {"s.id": "SUP-001", "s.name": "供应商 A", "s.status": "active",
            "total_orders": 100, "delayed": 40, "cancelled": 25, "total_payable": 1000000, "overdue": 600000}
        mock_session = Mock()
        mock_session.run.return_value = mock_result
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=False)
        mock_driver = Mock()
        mock_driver.session.return_value = mock_session
        mock_db.driver.return_value = mock_driver
        
        agent = BusinessRiskAgent()
        result = agent.analyze_supplier_risk_graph("SUP-001")
        
        assert result["supplier_id"] == "SUP-001"
        assert result["risk_score"] > 70
        assert result["risk_level"] == "HIGH"
        agent.close()
    
    @patch('app.agents.business_risk_agent.GraphDatabase')
    def test_analyze_supplier_risk_graph_not_found(self, mock_db):
        mock_result = Mock()
        mock_result.single.return_value = None
        mock_session = Mock()
        mock_session.run.return_value = mock_result
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=False)
        mock_driver = Mock()
        mock_driver.session.return_value = mock_session
        mock_db.driver.return_value = mock_driver
        
        agent = BusinessRiskAgent()
        result = agent.analyze_supplier_risk_graph("SUP-999")
        
        assert "error" in result
        agent.close()


class TestRiskSummary:
    @patch('app.agents.business_risk_agent.pool.SimpleConnectionPool')
    def test_get_risk_summary(self, mock_pool_cls):
        mock_pool = create_mock_pool(create_mock_connection([]))
        mock_pool_cls.return_value = mock_pool
        
        agent = BusinessRiskAgent()
        with patch.object(agent, 'detect_inventory_risks') as m1, \
             patch.object(agent, 'detect_purchase_risks') as m2, \
             patch.object(agent, 'detect_sales_risks') as m3, \
             patch.object(agent, 'detect_payment_risks') as m4:
            m1.return_value = [BusinessRiskAlert(risk_type=RiskType.INVENTORY_LOW.value, severity=RiskSeverity.HIGH.value)]
            m2.return_value = [BusinessRiskAlert(risk_type=RiskType.PURCHASE_DELIVERY_DELAY.value, severity=RiskSeverity.MEDIUM.value)]
            m3.return_value = []
            m4.return_value = [BusinessRiskAlert(risk_type=RiskType.PAYMENT_DUPLICATE.value, severity=RiskSeverity.CRITICAL.value)]
            
            summary = agent.get_risk_summary()
            
            assert summary["total_risks"] == 3
            assert BusinessRiskCategory.INVENTORY.value in summary["by_category"]
            assert summary["by_severity"][RiskSeverity.CRITICAL.value] == 1
        agent.close()


class TestConvenienceFunctions:
    @patch('app.agents.business_risk_agent.BusinessRiskAgent')
    def test_get_business_risk_agent(self, mock_cls):
        agent = get_business_risk_agent()
        assert agent is not None
        mock_cls.assert_called_once()
    
    @patch('app.agents.business_risk_agent.BusinessRiskAgent')
    def test_detect_business_risks(self, mock_cls):
        mock_agent = Mock()
        mock_agent.detect_all_risks.return_value = [BusinessRiskAlert(risk_type=RiskType.INVENTORY_LOW.value)]
        mock_cls.return_value = mock_agent
        
        result = detect_business_risks()
        
        assert isinstance(result, list)
        assert len(result) == 1
        mock_agent.close.assert_called_once()


class TestEdgeCases:
    @patch('app.agents.business_risk_agent.pool.SimpleConnectionPool')
    def test_empty_database(self, mock_pool_cls):
        mock_pool = create_mock_pool(create_mock_connection([]))
        mock_pool_cls.return_value = mock_pool
        
        agent = BusinessRiskAgent()
        alerts = agent._check_inventory_low()
        
        assert len(alerts) == 0
        agent.close()
    
    @patch('app.agents.business_risk_agent.pool.SimpleConnectionPool')
    def test_database_error_handling(self, mock_pool_cls):
        mock_conn = Mock()
        mock_conn.cursor.side_effect = Exception("DB error")
        mock_pool = create_mock_pool(mock_conn)
        mock_pool_cls.return_value = mock_pool
        
        agent = BusinessRiskAgent()
        alerts = agent._check_inventory_low()
        
        assert len(alerts) == 0
        agent.close()
    
    @patch('app.agents.business_risk_agent.GraphDatabase')
    def test_neo4j_error_handling(self, mock_db):
        mock_db.driver.side_effect = Exception("Neo4j error")
        
        agent = BusinessRiskAgent()
        result = agent.analyze_supplier_risk_graph("SUP-001")
        
        assert "error" in result
        agent.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
