"""
风险预测模型测试

测试风险预测引擎的核心功能：
1. 现金流预测
2. 应收账款逾期预测
3. 财务风险综合预测
4. 批量预测

验收标准：预测准确率 >75%
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, date, timedelta

from app.services.risk_prediction import RiskPredictionEngine, PredictionConfidence


def create_mock_session(mock_result):
    """创建模拟会话和上下文管理器"""
    mock_session = Mock()
    mock_session.run.return_value = mock_result
    
    mock_context = Mock()
    mock_context.__enter__ = Mock(return_value=mock_session)
    mock_context.__exit__ = Mock(return_value=False)
    
    return mock_context, mock_session


class TestCashflowPrediction:
    """现金流预测测试"""
    
    @patch('app.services.risk_prediction.GraphDatabase')
    def test_predict_cashflow_risk_healthy(self, mock_db):
        """测试现金流预测 - 健康"""
        mock_result = Mock()
        mock_result.single.return_value = {
            "current_balance": 2000000,
            "threshold": 1000000,
            "burn_rate": 100000,
            "inflow_30d": 1500000,
            "outflow_30d": 1400000
        }
        
        mock_context, _ = create_mock_session(mock_result)
        mock_db.driver.return_value.session.return_value = mock_context
        
        engine = RiskPredictionEngine()
        result = engine.predict_cashflow_risk("COMP-001", days=30)
        
        assert "company_id" in result
        assert "prediction_days" in result
        assert "current_balance" in result
        assert "predicted_balance" in result
        assert "risk_probability" in result
        assert "confidence" in result
        
        # 健康状态风险概率应该较低
        assert result["risk_probability"] < 0.4
        assert result["confidence"] == PredictionConfidence.HIGH.value
        
        engine.close()
    
    @patch('app.services.risk_prediction.GraphDatabase')
    def test_predict_cashflow_risk_critical(self, mock_db):
        """测试现金流预测 - 危险"""
        mock_result = Mock()
        mock_result.single.return_value = {
            "current_balance": 300000,
            "threshold": 1000000,
            "burn_rate": 400000,
            "inflow_30d": 500000,
            "outflow_30d": 900000
        }
        
        mock_context, _ = create_mock_session(mock_result)
        mock_db.driver.return_value.session.return_value = mock_context
        
        engine = RiskPredictionEngine()
        result = engine.predict_cashflow_risk("COMP-001", days=30)
        
        # 危险状态风险概率应该很高
        assert result["risk_probability"] >= 0.7
        assert result["current_balance"] == 300000
        assert result["predicted_balance"] < result["current_balance"]
        
        engine.close()
    
    @patch('app.services.risk_prediction.GraphDatabase')
    def test_predict_cashflow_risk_warning(self, mock_db):
        """测试现金流预测 - 警告"""
        mock_result = Mock()
        mock_result.single.return_value = {
            "current_balance": 800000,
            "threshold": 1000000,
            "burn_rate": 200000,
            "inflow_30d": 1000000,
            "outflow_30d": 1100000
        }
        
        mock_context, _ = create_mock_session(mock_result)
        mock_db.driver.return_value.session.return_value = mock_context
        
        engine = RiskPredictionEngine()
        result = engine.predict_cashflow_risk("COMP-001", days=30)
        
        # 警告状态风险概率中等
        assert result["risk_probability"] >= 0.5
        assert result["risk_probability"] < 0.8
        
        engine.close()
    
    @patch('app.services.risk_prediction.GraphDatabase')
    def test_predict_cashflow_risk_with_runway(self, mock_db):
        """测试现金流预测 - 包含剩余天数"""
        mock_result = Mock()
        mock_result.single.return_value = {
            "current_balance": 600000,
            "threshold": 1000000,
            "burn_rate": 150000,
            "inflow_30d": 800000,
            "outflow_30d": 900000
        }
        
        mock_context, _ = create_mock_session(mock_result)
        mock_db.driver.return_value.session.return_value = mock_context
        
        engine = RiskPredictionEngine()
        result = engine.predict_cashflow_risk("COMP-001", days=30)
        
        assert "runway_days" in result["metrics"]
        assert result["metrics"]["runway_days"] > 0
        
        engine.close()
    
    @patch('app.services.risk_prediction.GraphDatabase')
    def test_predict_cashflow_risk_no_data(self, mock_db):
        """测试现金流预测 - 无数据"""
        mock_result = Mock()
        mock_result.single.return_value = None
        
        mock_context, _ = create_mock_session(mock_result)
        mock_db.driver.return_value.session.return_value = mock_context
        
        engine = RiskPredictionEngine()
        result = engine.predict_cashflow_risk("COMP-999", days=30)
        
        assert "error" in result
        
        engine.close()


class TestARPrediction:
    """应收账款预测测试"""
    
    @patch('app.services.risk_prediction.GraphDatabase')
    def test_predict_ar_risk_high_risk(self, mock_db):
        """测试应收账款预测 - 高风险"""
        mock_result = Mock()
        mock_result.single.return_value = {
            "customer_name": "A 公司",
            "current_overdue": 800000,
            "total_receivable": 1000000,
            "overdue_count": 8,
            "avg_payment_days": 75
        }
        
        mock_context, _ = create_mock_session(mock_result)
        mock_db.driver.return_value.session.return_value = mock_context
        
        engine = RiskPredictionEngine()
        result = engine.predict_ar_risk("CUST-001", days=30)
        
        assert result["risk_probability"] >= 0.7
        assert result["current_overdue"] == 800000
        assert result["confidence"] == PredictionConfidence.HIGH.value
        
        engine.close()
    
    @patch('app.services.risk_prediction.GraphDatabase')
    def test_predict_ar_risk_low_risk(self, mock_db):
        """测试应收账款预测 - 低风险"""
        mock_result = Mock()
        mock_result.single.return_value = {
            "customer_name": "B 公司",
            "current_overdue": 20000,
            "total_receivable": 500000,
            "overdue_count": 1,
            "avg_payment_days": 25
        }
        
        mock_context, _ = create_mock_session(mock_result)
        mock_db.driver.return_value.session.return_value = mock_context
        
        engine = RiskPredictionEngine()
        result = engine.predict_ar_risk("CUST-002", days=30)
        
        # 低风险应该 <= 0.4
        assert result["risk_probability"] <= 0.4
        
        engine.close()


class TestComprehensivePrediction:
    """综合财务风险预测测试"""
    
    @patch('app.services.risk_prediction.GraphDatabase')
    def test_predict_financial_risk_critical(self, mock_db):
        """测试综合预测 - 严重风险"""
        mock_result = Mock()
        mock_result.single.return_value = {
            "cash_balance": 200000,
            "cash_threshold": 1000000,
            "current_ratio": 0.7,
            "debt_to_equity": 3.0,
            "roe": 0.02,
            "overdue_ar": 600000,
            "total_ap": 1500000,
            "ap_due_soon": 400000
        }
        
        mock_context, _ = create_mock_session(mock_result)
        mock_db.driver.return_value.session.return_value = mock_context
        
        engine = RiskPredictionEngine()
        result = engine.predict_financial_risk("COMP-001", days=30)
        
        assert result["overall_risk_score"] >= 70
        assert result["risk_level"] in ["CRITICAL", "HIGH"]
        assert len(result["recommendations"]) > 0
        
        engine.close()
    
    @patch('app.services.risk_prediction.GraphDatabase')
    def test_predict_financial_risk_healthy(self, mock_db):
        """测试综合预测 - 健康"""
        mock_result = Mock()
        mock_result.single.return_value = {
            "cash_balance": 3000000,
            "cash_threshold": 1000000,
            "current_ratio": 2.0,
            "debt_to_equity": 0.8,
            "roe": 0.18,
            "overdue_ar": 50000,
            "total_ap": 800000,
            "ap_due_soon": 200000
        }
        
        mock_context, _ = create_mock_session(mock_result)
        mock_db.driver.return_value.session.return_value = mock_context
        
        engine = RiskPredictionEngine()
        result = engine.predict_financial_risk("COMP-002", days=30)
        
        assert result["overall_risk_score"] < 40
        assert result["risk_level"] in ["LOW", "MINIMAL"]
        
        engine.close()
    
    @patch('app.services.risk_prediction.GraphDatabase')
    def test_predict_financial_risk_category_scores(self, mock_db):
        """测试综合预测 - 分类评分"""
        mock_result = Mock()
        mock_result.single.return_value = {
            "cash_balance": 800000,
            "cash_threshold": 1000000,
            "current_ratio": 1.2,
            "debt_to_equity": 1.8,
            "roe": 0.08,
            "overdue_ar": 200000,
            "total_ap": 600000,
            "ap_due_soon": 150000
        }
        
        mock_context, _ = create_mock_session(mock_result)
        mock_db.driver.return_value.session.return_value = mock_context
        
        engine = RiskPredictionEngine()
        result = engine.predict_financial_risk("COMP-003", days=30)
        
        assert "category_scores" in result
        assert "cashflow" in result["category_scores"]
        assert "ar" in result["category_scores"]
        assert "ap" in result["category_scores"]
        assert "ratio" in result["category_scores"]
        
        for category, score in result["category_scores"].items():
            assert 0 <= score <= 100
        
        engine.close()


class TestBatchPrediction:
    """批量预测测试"""
    
    @patch('app.services.risk_prediction.GraphDatabase')
    def test_batch_predict_risks(self, mock_db):
        """测试批量预测"""
        mock_result = Mock()
        mock_result.single.return_value = {
            "cash_balance": 1000000,
            "cash_threshold": 1000000,
            "current_ratio": 1.5,
            "debt_to_equity": 1.5,
            "roe": 0.10,
            "overdue_ar": 100000,
            "total_ap": 500000,
            "ap_due_soon": 100000
        }
        
        mock_context, _ = create_mock_session(mock_result)
        mock_db.driver.return_value.session.return_value = mock_context
        
        engine = RiskPredictionEngine()
        company_ids = ["COMP-001", "COMP-002", "COMP-003"]
        result = engine.batch_predict_risks(company_ids, days=30)
        
        assert "predictions" in result
        assert "summary" in result
        assert len(result["predictions"]) == 3
        
        summary = result["summary"]
        assert summary["total_companies"] == 3
        assert "avg_risk_score" in summary
        
        engine.close()


class TestPredictionConfidence:
    """预测置信度测试"""
    
    def test_confidence_enum_values(self):
        """测试置信度枚举值"""
        assert PredictionConfidence.HIGH.value == "HIGH"
        assert PredictionConfidence.MEDIUM.value == "MEDIUM"
        assert PredictionConfidence.LOW.value == "LOW"


class TestPredictionAccuracy:
    """预测准确率测试（模拟）"""
    
    @patch('app.services.risk_prediction.GraphDatabase')
    def test_prediction_accuracy_threshold(self, mock_db):
        """
        测试预测准确率阈值
        
        验收标准：预测准确率 >75%
        
        注意：这是简化测试，实际准确率需要历史数据验证
        """
        # 测试不同风险等级的识别
        test_scenarios = [
            # 场景 1: 高风险数据
            {
                "data": {
                    "cash_balance": 200000,
                    "cash_threshold": 1000000,
                    "current_ratio": 0.6,
                    "debt_to_equity": 3.0,
                    "roe": 0.02
                },
                "expected_high_risk": True  # 期望高风险评分
            },
            # 场景 2: 低风险数据
            {
                "data": {
                    "cash_balance": 3000000,
                    "cash_threshold": 1000000,
                    "current_ratio": 2.0,
                    "debt_to_equity": 0.8,
                    "roe": 0.18
                },
                "expected_high_risk": False  # 期望低风险评分
            }
        ]
        
        correct_predictions = 0
        
        for scenario in test_scenarios:
            mock_result = Mock()
            mock_result.single.return_value = {
                **scenario["data"],
                "overdue_ar": 50000,
                "total_ap": 400000,
                "ap_due_soon": 100000
            }
            
            mock_context = Mock()
            mock_context.__enter__ = Mock(return_value=Mock(run=Mock(return_value=mock_result)))
            mock_context.__exit__ = Mock(return_value=False)
            mock_db.driver.return_value.session.return_value = mock_context
            
            engine = RiskPredictionEngine()
            result = engine.predict_financial_risk("COMP-TEST", days=30)
            
            is_high_risk = result["overall_risk_score"] >= 60
            
            if is_high_risk == scenario["expected_high_risk"]:
                correct_predictions += 1
            
            engine.close()
        
        # 简单测试：至少能正确区分高/低风险
        accuracy = correct_predictions / len(test_scenarios)
        assert accuracy >= 0.75, f"预测准确率 {accuracy:.2%} 低于 75%"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
