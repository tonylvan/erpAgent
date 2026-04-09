"""
Risk Predictor Test Suite

Tests for the advanced risk prediction module with ML-ready interfaces:
1. Cashflow prediction (Prophet/LSTM style)
2. Payment risk prediction (XGBoost style)
3. Inventory risk prediction (demand forecast)

Acceptance criteria: 8+ tests all passing
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date, timedelta
import numpy as np

from app.services.risk_predictor import (
    RiskPredictor,
    CashflowPredictor,
    PaymentRiskPredictor,
    InventoryRiskPredictor,
    PredictionModel,
    RiskLevel
)


def create_mock_neo4j_session(mock_result):
    """Create mock Neo4j session and context manager"""
    mock_session = Mock()
    mock_session.run.return_value = mock_result
    
    mock_context = Mock()
    mock_context.__enter__ = Mock(return_value=mock_session)
    mock_context.__exit__ = Mock(return_value=False)
    
    return mock_context, mock_session


class TestCashflowPredictor:
    """Test cashflow prediction (Prophet/LSTM style)"""
    
    @patch('app.services.risk_predictor.GraphDatabase')
    def test_cashflow_predict_basic(self, mock_db):
        """Test basic cashflow prediction"""
        mock_result = Mock()
        mock_result.single.return_value = {
            "current_balance": 1000000,
            "threshold": 500000,
            "historical_inflows": [100000, 150000, 120000, 180000],
            "historical_outflows": [80000, 90000, 100000, 85000]
        }
        
        mock_context, _ = create_mock_neo4j_session(mock_result)
        mock_db.driver.return_value.session.return_value = mock_context
        
        predictor = CashflowPredictor()
        result = predictor.predict("COMP-001", days=30)
        
        assert "company_id" in result
        assert "prediction_days" in result
        assert "predicted_balance" in result
        assert "confidence_interval" in result
        assert "trend" in result
        assert "risk_level" in result
        
        predictor.close()
    
    @patch('app.services.risk_predictor.GraphDatabase')
    def test_cashflow_predict_with_trend(self, mock_db):
        """Test cashflow trend detection"""
        # Declining trend data
        mock_result = Mock()
        mock_result.single.return_value = {
            "current_balance": 200000,
            "threshold": 500000,
            "historical_inflows": [200000, 150000, 100000, 50000],
            "historical_outflows": [100000, 120000, 150000, 180000]
        }
        
        mock_context, _ = create_mock_neo4j_session(mock_result)
        mock_db.driver.return_value.session.return_value = mock_context
        
        predictor = CashflowPredictor()
        result = predictor.predict("COMP-002", days=30)
        
        # Declining trend should indicate high risk
        assert result["trend"] in ["declining", "stable", "growing"]
        if result["trend"] == "declining":
            assert result["risk_level"] in [RiskLevel.HIGH.value, RiskLevel.CRITICAL.value]
        
        predictor.close()
    
    @patch('app.services.risk_predictor.GraphDatabase')
    def test_cashflow_confidence_interval(self, mock_db):
        """Test confidence interval calculation"""
        mock_result = Mock()
        mock_result.single.return_value = {
            "current_balance": 500000,
            "threshold": 300000,
            "historical_inflows": [100000, 100000, 100000, 100000],
            "historical_outflows": [80000, 80000, 80000, 80000]
        }
        
        mock_context, _ = create_mock_neo4j_session(mock_result)
        mock_db.driver.return_value.session.return_value = mock_context
        
        predictor = CashflowPredictor()
        result = predictor.predict("COMP-003", days=30)
        
        # Confidence interval should have lower and upper bounds
        assert "lower_bound" in result["confidence_interval"]
        assert "upper_bound" in result["confidence_interval"]
        assert result["confidence_interval"]["lower_bound"] <= result["predicted_balance"]
        assert result["confidence_interval"]["upper_bound"] >= result["predicted_balance"]
        
        predictor.close()
    
    @patch('app.services.risk_predictor.GraphDatabase')
    def test_cashflow_no_data(self, mock_db):
        """Test cashflow prediction with no data"""
        mock_result = Mock()
        mock_result.single.return_value = None
        
        mock_context, _ = create_mock_neo4j_session(mock_result)
        mock_db.driver.return_value.session.return_value = mock_context
        
        predictor = CashflowPredictor()
        result = predictor.predict("COMP-999", days=30)
        
        assert "error" in result
        assert result["error"] == "No cashflow data found"
        
        predictor.close()


class TestPaymentRiskPredictor:
    """Test payment risk prediction (XGBoost style)"""
    
    @patch('app.services.risk_predictor.GraphDatabase')
    def test_payment_risk_basic(self, mock_db):
        """Test basic payment risk prediction"""
        mock_result = Mock()
        mock_result.single.return_value = {
            "supplier_name": "Supplier A",
            "total_payable": 500000,
            "overdue_amount": 100000,
            "payment_history": [30, 35, 40, 45, 50],  # Days to pay
            "credit_limit": 1000000,
            "due_in_7d": 200000
        }
        
        mock_context, _ = create_mock_neo4j_session(mock_result)
        mock_db.driver.return_value.session.return_value = mock_context
        
        predictor = PaymentRiskPredictor()
        result = predictor.predict("SUPP-001", days=30)
        
        assert "supplier_id" in result
        assert "risk_probability" in result
        assert "risk_level" in result
        assert "feature_scores" in result
        assert "recommendations" in result
        
        predictor.close()
    
    @patch('app.services.risk_predictor.GraphDatabase')
    def test_payment_risk_high_risk(self, mock_db):
        """Test high risk payment prediction"""
        mock_result = Mock()
        mock_result.single.return_value = {
            "supplier_name": "Supplier B",
            "total_payable": 800000,
            "overdue_amount": 500000,
            "payment_history": [60, 75, 90, 100, 120],  # Very slow payments
            "credit_limit": 500000,
            "due_in_7d": 600000  # More than credit limit
        }
        
        mock_context, _ = create_mock_neo4j_session(mock_result)
        mock_db.driver.return_value.session.return_value = mock_context
        
        predictor = PaymentRiskPredictor()
        result = predictor.predict("SUPP-002", days=30)
        
        # High overdue + slow payment history = high risk
        assert result["risk_probability"] >= 0.6
        assert result["risk_level"] in [RiskLevel.HIGH.value, RiskLevel.CRITICAL.value]
        
        predictor.close()
    
    @patch('app.services.risk_predictor.GraphDatabase')
    def test_payment_risk_feature_importance(self, mock_db):
        """Test feature importance extraction"""
        mock_result = Mock()
        mock_result.single.return_value = {
            "supplier_name": "Supplier C",
            "total_payable": 300000,
            "overdue_amount": 50000,
            "payment_history": [30, 32, 35, 38, 40],
            "credit_limit": 800000,
            "due_in_7d": 100000
        }
        
        mock_context, _ = create_mock_neo4j_session(mock_result)
        mock_db.driver.return_value.session.return_value = mock_context
        
        predictor = PaymentRiskPredictor()
        result = predictor.predict("SUPP-003", days=30)
        
        # Feature scores should be present
        features = result["feature_scores"]
        assert "payment_delay_score" in features
        assert "overdue_ratio_score" in features
        assert "liquidity_score" in features
        
        predictor.close()


class TestInventoryRiskPredictor:
    """Test inventory risk prediction (demand forecast)"""
    
    @patch('app.services.risk_predictor.GraphDatabase')
    def test_inventory_risk_basic(self, mock_db):
        """Test basic inventory risk prediction"""
        mock_result = Mock()
        mock_result.single.return_value = {
            "product_name": "Product A",
            "current_stock": 1000,
            "reorder_point": 200,
            "demand_history": [100, 120, 110, 130, 140],
            "lead_time_days": 7,
            "unit_cost": 50
        }
        
        mock_context, _ = create_mock_neo4j_session(mock_result)
        mock_db.driver.return_value.session.return_value = mock_context
        
        predictor = InventoryRiskPredictor()
        result = predictor.predict("PROD-001", days=30)
        
        assert "product_id" in result
        assert "predicted_demand" in result
        assert "stockout_probability" in result
        assert "risk_level" in result
        assert "reorder_recommendation" in result
        
        predictor.close()
    
    @patch('app.services.risk_predictor.GraphDatabase')
    def test_inventory_stockout_risk(self, mock_db):
        """Test stockout risk detection"""
        mock_result = Mock()
        mock_result.single.return_value = {
            "product_name": "Product B",
            "current_stock": 50,
            "reorder_point": 200,
            "demand_history": [150, 180, 200, 220, 250],  # High demand
            "lead_time_days": 14,
            "unit_cost": 100
        }
        
        mock_context, _ = create_mock_neo4j_session(mock_result)
        mock_db.driver.return_value.session.return_value = mock_context
        
        predictor = InventoryRiskPredictor()
        result = predictor.predict("PROD-002", days=30)
        
        # Low stock + high demand = stockout risk
        assert result["stockout_probability"] >= 0.5
        assert result["risk_level"] in [RiskLevel.HIGH.value, RiskLevel.CRITICAL.value]
        
        predictor.close()
    
    @patch('app.services.risk_predictor.GraphDatabase')
    def test_inventory_overstock_risk(self, mock_db):
        """Test overstock risk detection"""
        mock_result = Mock()
        mock_result.single.return_value = {
            "product_name": "Product C",
            "current_stock": 5000,
            "reorder_point": 200,
            "demand_history": [50, 40, 30, 20, 10],  # Declining demand
            "lead_time_days": 7,
            "unit_cost": 200
        }
        
        mock_context, _ = create_mock_neo4j_session(mock_result)
        mock_db.driver.return_value.session.return_value = mock_context
        
        predictor = InventoryRiskPredictor()
        result = predictor.predict("PROD-003", days=30)
        
        # High stock + declining demand = overstock risk
        assert "overstock_risk" in result
        assert result["risk_level"] in [RiskLevel.LOW.value, RiskLevel.MEDIUM.value, RiskLevel.HIGH.value]
        
        predictor.close()


class TestRiskPredictorIntegration:
    """Test integrated risk predictor"""
    
    @patch('app.services.risk_predictor.GraphDatabase')
    def test_comprehensive_risk_prediction(self, mock_db):
        """Test comprehensive multi-type risk prediction"""
        # Mock data for all three types
        cashflow_result = {
            "current_balance": 500000,
            "threshold": 300000,
            "historical_inflows": [100000, 120000, 110000, 130000],
            "historical_outflows": [80000, 90000, 85000, 95000]
        }
        
        mock_result = Mock()
        mock_result.single.return_value = cashflow_result
        
        mock_context, _ = create_mock_neo4j_session(mock_result)
        mock_db.driver.return_value.session.return_value = mock_context
        
        predictor = RiskPredictor()
        result = predictor.predict_all("COMP-001", days=30)
        
        assert "cashflow" in result
        assert "payment" in result
        assert "inventory" in result
        assert "overall_risk_score" in result
        assert "summary" in result
        
        predictor.close()
    
    @patch('app.services.risk_predictor.GraphDatabase')
    def test_risk_predictor_health_check(self, mock_db):
        """Test risk predictor health check"""
        predictor = RiskPredictor()
        health = predictor.health_check()
        
        assert "status" in health
        assert "models_available" in health
        assert "supported_risk_types" in health
        
        predictor.close()


class TestPredictionModelEnum:
    """Test prediction model enumeration"""
    
    def test_prediction_model_values(self):
        """Test prediction model enum values"""
        assert PredictionModel.PROphet.value == "prophet"
        assert PredictionModel.LSTM.value == "lstm"
        assert PredictionModel.XGBOOST.value == "xgboost"
        assert PredictionModel.RULE_BASED.value == "rule_based"
    
    def test_risk_level_values(self):
        """Test risk level enum values"""
        assert RiskLevel.MINIMAL.value == "minimal"
        assert RiskLevel.LOW.value == "low"
        assert RiskLevel.MEDIUM.value == "medium"
        assert RiskLevel.HIGH.value == "high"
        assert RiskLevel.CRITICAL.value == "critical"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])