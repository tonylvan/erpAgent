"""
财务分析引擎测试

测试财务分析引擎的核心功能：
1. 财务健康度评分
2. 风险传播分析
3. 财务趋势分析
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, date

from app.services.financial_analysis import FinancialAnalysisEngine
from app.models.financial_risk import RiskSeverity


class TestFinancialHealthScore:
    """财务健康度评分测试"""
    
    @pytest.fixture
    def engine(self):
        """创建测试引擎"""
        with patch('app.services.financial_analysis.GraphDatabase'):
            engine = FinancialAnalysisEngine()
            yield engine
            engine.close()
    
    def test_calculate_liquidity_score_excellent(self, engine):
        """测试流动性评分 - 优秀"""
        # 流动比率 2.0, 速动比率 1.5
        score = engine._calculate_liquidity_score(2.0, 1.5)
        assert score >= 90
        assert score <= 100
    
    def test_calculate_liquidity_score_good(self, engine):
        """测试流动性评分 - 良好"""
        # 流动比率 1.5, 速动比率 1.0
        score = engine._calculate_liquidity_score(1.5, 1.0)
        assert score >= 75
        assert score <= 90
    
    def test_calculate_liquidity_score_warning(self, engine):
        """测试流动性评分 - 警告"""
        # 流动比率 1.0, 速动比率 0.7
        score = engine._calculate_liquidity_score(1.0, 0.7)
        assert score >= 50
        assert score < 70
    
    def test_calculate_liquidity_score_critical(self, engine):
        """测试流动性评分 - 危险"""
        # 流动比率 0.5, 速动比率 0.3
        score = engine._calculate_liquidity_score(0.5, 0.3)
        assert score < 40
    
    def test_calculate_leverage_score_low(self, engine):
        """测试杠杆评分 - 低负债"""
        # 负债权益比 0.8
        score = engine._calculate_leverage_score(0.8)
        assert score >= 90
    
    def test_calculate_leverage_score_moderate(self, engine):
        """测试杠杆评分 - 中等"""
        # 负债权益比 1.5
        score = engine._calculate_leverage_score(1.5)
        assert score >= 75
        assert score < 90
    
    def test_calculate_leverage_score_high(self, engine):
        """测试杠杆评分 - 高负债"""
        # 负债权益比 2.5
        score = engine._calculate_leverage_score(2.5)
        assert score >= 35
        assert score < 55
    
    def test_calculate_leverage_score_critical(self, engine):
        """测试杠杆评分 - 危险"""
        # 负债权益比 4.0
        score = engine._calculate_leverage_score(4.0)
        assert score < 30
    
    def test_calculate_profitability_score_excellent(self, engine):
        """测试盈利能力评分 - 优秀"""
        # ROE 20%
        score = engine._calculate_profitability_score(0.20)
        assert score >= 95
    
    def test_calculate_profitability_score_good(self, engine):
        """测试盈利能力评分 - 良好"""
        # ROE 12%
        score = engine._calculate_profitability_score(0.12)
        assert score >= 70
        assert score < 90
    
    def test_calculate_profitability_score_poor(self, engine):
        """测试盈利能力评分 - 差"""
        # ROE 2%
        score = engine._calculate_profitability_score(0.02)
        assert score < 50
    
    def test_calculate_cashflow_score_healthy(self, engine):
        """测试现金流评分 - 健康"""
        # 余额 200 万，安全线 100 万
        score = engine._calculate_cashflow_score(2000000, 1000000, 0)
        assert score >= 90
    
    def test_calculate_cashflow_score_warning(self, engine):
        """测试现金流评分 - 警告"""
        # 余额 80 万，安全线 100 万
        score = engine._calculate_cashflow_score(800000, 1000000, 0)
        assert score >= 45
        assert score < 65
    
    def test_calculate_cashflow_score_critical(self, engine):
        """测试现金流评分 - 危险"""
        # 余额 30 万，安全线 100 万
        score = engine._calculate_cashflow_score(300000, 1000000, 0)
        assert score < 40
    
    def test_calculate_cashflow_score_with_burn_rate(self, engine):
        """测试现金流评分 - 考虑消耗率"""
        # 余额 100 万，安全线 100 万，月消耗 50 万 (runway 2 个月)
        score = engine._calculate_cashflow_score(1000000, 1000000, 500000)
        # 有消耗率会降低评分
        assert score < engine._calculate_cashflow_score(1000000, 1000000, 0)
    
    @patch('app.services.financial_analysis.GraphDatabase')
    def test_calculate_health_score_mock_data(self, mock_db):
        """测试健康度评分计算 - 模拟数据"""
        # 模拟 Neo4j 返回数据
        mock_session = Mock()
        mock_result = Mock()
        
        # 第一次查询返回财务比率
        ratio_record = {
            "current_ratio": 1.2,
            "quick_ratio": 0.9,
            "debt_to_equity": 1.8,
            "roe": 0.08,
            "roi": 0.10,
            "gross_margin": 0.20
        }
        
        # 第二次查询返回现金流
        cashflow_record = {
            "balance": 800000,
            "threshold": 1000000,
            "burn_rate": 200000
        }
        
        mock_result.single.side_effect = [ratio_record, cashflow_record]
        mock_session.run.return_value = mock_result
        
        # 正确设置 context manager
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=False)
        mock_db.driver.return_value.session.return_value = mock_context
        
        engine = FinancialAnalysisEngine()
        result = engine.calculate_health_score("COMP-001")
        
        assert "overall_score" in result
        assert "dimension_scores" in result
        assert "level" in result
        assert "recommendations" in result
        
        # 验证评分范围
        assert result["overall_score"] >= 0
        assert result["overall_score"] <= 100
        
        # 验证维度
        assert "liquidity" in result["dimension_scores"]
        assert "leverage" in result["dimension_scores"]
        assert "profitability" in result["dimension_scores"]
        assert "cashflow" in result["dimension_scores"]
        
        engine.close()
    
    @patch('app.services.financial_analysis.GraphDatabase')
    def test_calculate_health_score_level_healthy(self, mock_db):
        """测试健康等级 - 健康"""
        mock_session = Mock()
        mock_result = Mock()
        
        # 优秀数据
        ratio_record = {
            "current_ratio": 2.0,
            "quick_ratio": 1.5,
            "debt_to_equity": 0.8,
            "roe": 0.20,
            "roi": 0.15,
            "gross_margin": 0.30
        }
        cashflow_record = {
            "balance": 3000000,
            "threshold": 1000000,
            "burn_rate": 100000
        }
        
        mock_result.single.side_effect = [ratio_record, cashflow_record]
        mock_session.run.return_value = mock_result
        
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=False)
        mock_db.driver.return_value.session.return_value = mock_context
        
        engine = FinancialAnalysisEngine()
        result = engine.calculate_health_score("COMP-001")
        
        assert result["level"] == "HEALTHY"
        assert result["overall_score"] >= 80
        
        engine.close()
    
    @patch('app.services.financial_analysis.GraphDatabase')
    def test_calculate_health_score_level_critical(self, mock_db):
        """测试健康等级 - 严重"""
        mock_session = Mock()
        mock_result = Mock()
        
        # 差数据
        ratio_record = {
            "current_ratio": 0.6,
            "quick_ratio": 0.4,
            "debt_to_equity": 3.5,
            "roe": 0.01,
            "roi": 0.02,
            "gross_margin": 0.05
        }
        cashflow_record = {
            "balance": 200000,
            "threshold": 1000000,
            "burn_rate": 300000
        }
        
        mock_result.single.side_effect = [ratio_record, cashflow_record]
        mock_session.run.return_value = mock_result
        
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=False)
        mock_db.driver.return_value.session.return_value = mock_context
        
        engine = FinancialAnalysisEngine()
        result = engine.calculate_health_score("COMP-001")
        
        assert result["level"] == "CRITICAL"
        assert result["overall_score"] < 40
        
        engine.close()


class TestRiskPropagation:
    """风险传播分析测试"""
    
    @pytest.fixture
    def engine(self):
        """创建测试引擎"""
        with patch('app.services.financial_analysis.GraphDatabase'):
            engine = FinancialAnalysisEngine()
            yield engine
            engine.close()
    
    @patch('app.services.financial_analysis.GraphDatabase')
    def test_analyze_cashflow_propagation(self, mock_db):
        """测试现金流风险传播分析"""
        mock_session = Mock()
        mock_result = Mock()
        
        mock_result.single.return_value = {
            "company_id": "COMP-001",
            "company_name": "某某公司",
            "departments": ["生产部", "销售部"],
            "projects": ["项目 A", "项目 B"],
            "pending_payments": 5,
            "pending_amount": 500000
        }
        
        mock_session.run.return_value = mock_result
        
        engine = FinancialAnalysisEngine()
        result = engine._analyze_cashflow_propagation(mock_session, "CFR-001")
        
        assert result["risk_id"] == "CFR-001"
        assert result["risk_type"] == "CASHFLOW"
        assert "direct_impacts" in result
        assert "indirect_impacts" in result
        assert "affected_entities" in result
        assert "propagation_paths" in result
        
        engine.close()
    
    @patch('app.services.financial_analysis.GraphDatabase')
    def test_analyze_ar_propagation(self, mock_db):
        """测试应收账款风险传播分析"""
        mock_session = Mock()
        mock_result = Mock()
        
        mock_result.single.return_value = {
            "customer_id": "CUST-001",
            "customer_name": "A 公司",
            "total_owed": 1200000,
            "tx_count": 5,
            "recent_sales": 2,
            "annual_revenue": 5000000
        }
        
        mock_session.run.return_value = mock_result
        
        engine = FinancialAnalysisEngine()
        result = engine._analyze_ar_propagation(mock_session, "ARR-001")
        
        assert result["risk_id"] == "ARR-001"
        assert result["risk_type"] == "AR"
        assert "direct_impacts" in result
        assert "indirect_impacts" in result
        
        engine.close()
    
    @patch('app.services.financial_analysis.GraphDatabase')
    def test_analyze_ap_propagation(self, mock_db):
        """测试应付账款风险传播分析"""
        mock_session = Mock()
        mock_result = Mock()
        
        mock_result.single.return_value = {
            "supplier_id": "SUP-001",
            "supplier_name": "供应商 A",
            "total_due": 800000,
            "tx_count": 4,
            "pending_orders": 3
        }
        
        mock_session.run.return_value = mock_result
        
        engine = FinancialAnalysisEngine()
        result = engine._analyze_ap_propagation(mock_session, "APR-001")
        
        assert result["risk_id"] == "APR-001"
        assert result["risk_type"] == "AP"
        assert "total_impact_score" in result
        
        engine.close()
    
    @patch('app.services.financial_analysis.GraphDatabase')
    def test_analyze_ratio_propagation(self, mock_db):
        """测试财务比率风险传播分析"""
        mock_session = Mock()
        mock_result = Mock()
        
        # 数据触发多个风险因素
        mock_result.single.return_value = {
            "company_id": "COMP-001",
            "company_name": "某某公司",
            "current_ratio": 0.8,  # < 1.0 触发风险
            "debt_to_equity": 2.5,  # > 2.0 触发风险
            "roe": 0.03,  # < 0.05 触发风险
            "gross_margin": 0.15
        }
        
        mock_session.run.return_value = mock_result
        
        engine = FinancialAnalysisEngine()
        result = engine._analyze_ratio_propagation(mock_session, "FRR-001")
        
        assert result["risk_id"] == "FRR-001"
        assert result["risk_type"] == "RATIO"
        # 验证返回结构
        assert "direct_impacts" in result
        assert "indirect_impacts" in result
        
        engine.close()
    
    @patch('app.services.financial_analysis.GraphDatabase')
    def test_analyze_budget_propagation(self, mock_db):
        """测试预算偏差风险传播分析"""
        mock_session = Mock()
        mock_result = Mock()
        
        mock_result.single.return_value = {
            "department_id": "DEPT-001",
            "department_name": "市场部",
            "budget": 1000000,
            "actual": 1300000,
            "variance": 0.3,
            "manager": "赵六"
        }
        
        mock_session.run.return_value = mock_result
        
        engine = FinancialAnalysisEngine()
        result = engine._analyze_budget_propagation(mock_session, "BVR-001")
        
        assert result["risk_id"] == "BVR-001"
        assert result["risk_type"] == "BUDGET"
        # 验证返回结构
        assert "direct_impacts" in result
        assert "indirect_impacts" in result
        
        engine.close()


class TestFinancialTrend:
    """财务趋势分析测试"""
    
    @patch('app.services.financial_analysis.GraphDatabase')
    def test_analyze_financial_trend(self, mock_db):
        """测试财务趋势分析"""
        mock_session = Mock()
        
        # 模拟 6 个周期的数据 - 需要可迭代
        records = [
            {"period": "2026-Q1", "roe": 0.08, "gross_margin": 0.20, "current_ratio": 1.2},
            {"period": "2025-Q4", "roe": 0.07, "gross_margin": 0.18, "current_ratio": 1.1},
            {"period": "2025-Q3", "roe": 0.06, "gross_margin": 0.17, "current_ratio": 1.0},
            {"period": "2025-Q2", "roe": 0.05, "gross_margin": 0.16, "current_ratio": 1.1},
            {"period": "2025-Q1", "roe": 0.06, "gross_margin": 0.18, "current_ratio": 1.2},
            {"period": "2024-Q4", "roe": 0.07, "gross_margin": 0.19, "current_ratio": 1.3},
        ]
        
        # session.run 返回的对象需要可以被 list() 转换
        mock_result = Mock()
        mock_result.__iter__ = Mock(return_value=iter(records))
        mock_session.run.return_value = mock_result
        
        # 设置 context manager
        mock_context = Mock()
        mock_context.__enter__ = Mock(return_value=mock_session)
        mock_context.__exit__ = Mock(return_value=False)
        mock_db.driver.return_value.session.return_value = mock_context
        
        engine = FinancialAnalysisEngine()
        result = engine.analyze_financial_trend("COMP-001", periods=6)
        
        assert "company_id" in result
        assert "periods" in result
        assert "metrics" in result
        assert "trends" in result
        
        assert len(result["periods"]) == 6
        assert "roe" in result["metrics"]
        assert "gross_margin" in result["metrics"]
        
        # 验证趋势判断
        assert "roe_trend" in result["trends"]
        assert result["trends"]["roe_trend"] in ["UP", "DOWN", "STABLE"]
        
        engine.close()
    
    @patch('app.services.financial_analysis.GraphDatabase')
    def test_analyze_financial_trend_no_data(self, mock_db):
        """测试财务趋势分析 - 无数据"""
        mock_session = Mock()
        
        # 模拟空结果
        mock_session.run.return_value = []
        
        engine = FinancialAnalysisEngine()
        result = engine.analyze_financial_trend("COMP-999", periods=6)
        
        assert "error" in result
        
        engine.close()


class TestFinancialAnalysisEngineLifecycle:
    """引擎生命周期测试"""
    
    @patch('app.services.financial_analysis.GraphDatabase')
    def test_engine_initialization(self, mock_db):
        """测试引擎初始化"""
        engine = FinancialAnalysisEngine(
            neo4j_uri="bolt://localhost:7687",
            neo4j_user="neo4j",
            neo4j_password="test"
        )
        
        assert engine.neo4j_uri == "bolt://localhost:7687"
        mock_db.driver.assert_called_once_with(
            "bolt://localhost:7687",
            auth=("neo4j", "test")
        )
        
        engine.close()
        mock_db.driver.return_value.close.assert_called_once()
    
    def test_engine_default_config(self):
        """测试默认配置"""
        with patch('app.services.financial_analysis.GraphDatabase') as mock_db:
            engine = FinancialAnalysisEngine()
            
            assert engine.neo4j_uri == "bolt://127.0.0.1:7687"
            
            engine.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
