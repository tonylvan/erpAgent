"""
智能决策支持模块 - 决策场景测试

测试 5 大决策场景的定义和完整性
验收标准：5 大场景测试通过
"""

import pytest
from app.models.decision import (
    DecisionType,
    DecisionStatus,
    DecisionPriority,
    DecisionScenario,
    ALL_DECISION_SCENARIOS,
    INVENTORY_DECISION_SCENARIOS,
    PROCUREMENT_DECISION_SCENARIOS,
    SALES_DECISION_SCENARIOS,
    FINANCIAL_DECISION_SCENARIOS,
    CUSTOMER_DECISION_SCENARIOS
)


class TestDecisionType:
    """测试决策类型枚举"""
    
    def test_decision_type_values(self):
        """测试决策类型值"""
        assert DecisionType.INVENTORY.value == "inventory"
        assert DecisionType.PROCUREMENT.value == "procurement"
        assert DecisionType.SALES.value == "sales"
        assert DecisionType.FINANCIAL.value == "financial"
        assert DecisionType.CUSTOMER.value == "customer"
    
    def test_decision_type_count(self):
        """测试决策类型数量"""
        assert len(list(DecisionType)) == 5


class TestDecisionStatus:
    """测试决策状态枚举"""
    
    def test_decision_status_values(self):
        """测试决策状态值"""
        assert DecisionStatus.PROPOSED.value == "proposed"
        assert DecisionStatus.ANALYZING.value == "analyzing"
        assert DecisionStatus.PENDING_APPROVAL.value == "pending_approval"
        assert DecisionStatus.APPROVED.value == "approved"
        assert DecisionStatus.REJECTED.value == "rejected"
        assert DecisionStatus.EXECUTED.value == "executed"
        assert DecisionStatus.ARCHIVED.value == "archived"


class TestDecisionPriority:
    """测试决策优先级枚举"""
    
    def test_decision_priority_values(self):
        """测试决策优先级值"""
        assert DecisionPriority.LOW.value == "low"
        assert DecisionPriority.MEDIUM.value == "medium"
        assert DecisionPriority.HIGH.value == "high"
        assert DecisionPriority.URGENT.value == "urgent"


class TestInventoryDecisionScenarios:
    """测试库存决策场景"""
    
    def test_scenario_count(self):
        """测试库存场景数量"""
        assert len(INVENTORY_DECISION_SCENARIOS) == 3
    
    def test_scenario_ids_unique(self):
        """测试场景 ID 唯一性"""
        ids = [s.id for s in INVENTORY_DECISION_SCENARIOS]
        assert len(ids) == len(set(ids))
    
    def test_scenario_completeness(self):
        """测试场景完整性"""
        for scenario in INVENTORY_DECISION_SCENARIOS:
            assert scenario.id is not None
            assert scenario.name is not None
            assert scenario.description is not None
            assert scenario.decision_type == DecisionType.INVENTORY
            assert len(scenario.trigger_conditions) > 0
            assert len(scenario.analysis_dimensions) > 0
            assert len(scenario.decision_options) > 0
            assert len(scenario.evaluation_metrics) > 0
    
    def test_replenishment_scenario(self):
        """测试补货场景"""
        scenario = next(s for s in INVENTORY_DECISION_SCENARIOS if s.id == "INV-001")
        assert "库存低于安全库存" in scenario.trigger_conditions
        assert "立即补货" in scenario.decision_options
    
    def test_slow_moving_scenario(self):
        """测试呆滞库存场景"""
        scenario = next(s for s in INVENTORY_DECISION_SCENARIOS if s.id == "INV-002")
        assert "库龄超过 90 天" in scenario.trigger_conditions
        assert "打折促销" in scenario.decision_options
    
    def test_distribution_scenario(self):
        """测试库存调拨场景"""
        scenario = next(s for s in INVENTORY_DECISION_SCENARIOS if s.id == "INV-003")
        assert scenario.decision_type == DecisionType.INVENTORY
        assert "调拨成本" in scenario.evaluation_metrics


class TestProcurementDecisionScenarios:
    """测试采购决策场景"""
    
    def test_scenario_count(self):
        """测试采购场景数量"""
        assert len(PROCUREMENT_DECISION_SCENARIOS) == 3
    
    def test_scenario_completeness(self):
        """测试场景完整性"""
        for scenario in PROCUREMENT_DECISION_SCENARIOS:
            assert scenario.decision_type == DecisionType.PROCUREMENT
            assert len(scenario.trigger_conditions) > 0
    
    def test_supplier_selection_scenario(self):
        """测试供应商选择场景"""
        scenario = next(s for s in PROCUREMENT_DECISION_SCENARIOS if s.id == "PROC-001")
        assert "供应商交货及时率" in scenario.analysis_dimensions
        assert "综合成本" in scenario.evaluation_metrics
    
    def test_timing_scenario(self):
        """测试采购时机场景"""
        scenario = next(s for s in PROCUREMENT_DECISION_SCENARIOS if s.id == "PROC-002")
        assert "历史价格趋势" in scenario.analysis_dimensions
    
    def test_batch_scenario(self):
        """测试采购批量场景"""
        scenario = next(s for s in PROCUREMENT_DECISION_SCENARIOS if s.id == "PROC-003")
        assert any("经济批量" in opt for opt in scenario.decision_options)


class TestSalesDecisionScenarios:
    """测试销售决策场景"""
    
    def test_scenario_count(self):
        """测试销售场景数量"""
        assert len(SALES_DECISION_SCENARIOS) == 3
    
    def test_scenario_completeness(self):
        """测试场景完整性"""
        for scenario in SALES_DECISION_SCENARIOS:
            assert scenario.decision_type == DecisionType.SALES
    
    def test_pricing_scenario(self):
        """测试定价场景"""
        scenario = next(s for s in SALES_DECISION_SCENARIOS if s.id == "SALE-001")
        assert "价格弹性" in scenario.analysis_dimensions
        assert scenario.icon == "💰"
    
    def test_promotion_scenario(self):
        """测试促销场景"""
        scenario = next(s for s in SALES_DECISION_SCENARIOS if s.id == "SALE-002")
        assert "历史促销效果" in scenario.analysis_dimensions
        assert "ROI" in scenario.evaluation_metrics
    
    def test_discount_scenario(self):
        """测试折扣场景"""
        scenario = next(s for s in SALES_DECISION_SCENARIOS if s.id == "SALE-003")
        assert "客户价值" in scenario.analysis_dimensions


class TestFinancialDecisionScenarios:
    """测试财务决策场景"""
    
    def test_scenario_count(self):
        """测试财务场景数量"""
        assert len(FINANCIAL_DECISION_SCENARIOS) == 3
    
    def test_scenario_completeness(self):
        """测试场景完整性"""
        for scenario in FINANCIAL_DECISION_SCENARIOS:
            assert scenario.decision_type == DecisionType.FINANCIAL
    
    def test_payment_priority_scenario(self):
        """测试付款优先级场景"""
        scenario = next(s for s in FINANCIAL_DECISION_SCENARIOS if s.id == "FIN-001")
        assert "现金流紧张" in scenario.trigger_conditions
        assert "优先支付关键供应商" in scenario.decision_options
    
    def test_ar_collection_scenario(self):
        """测试应收账款催收场景"""
        scenario = next(s for s in FINANCIAL_DECISION_SCENARIOS if s.id == "FIN-002")
        assert "账款逾期" in scenario.trigger_conditions
        assert scenario.icon == "📋"
    
    def test_capital_allocation_scenario(self):
        """测试资金调配场景"""
        scenario = next(s for s in FINANCIAL_DECISION_SCENARIOS if s.id == "FIN-003")
        assert "各业务 ROI" in scenario.analysis_dimensions


class TestCustomerDecisionScenarios:
    """测试客户决策场景"""
    
    def test_scenario_count(self):
        """测试客户场景数量"""
        assert len(CUSTOMER_DECISION_SCENARIOS) == 3
    
    def test_scenario_completeness(self):
        """测试场景完整性"""
        for scenario in CUSTOMER_DECISION_SCENARIOS:
            assert scenario.decision_type == DecisionType.CUSTOMER
    
    def test_retention_scenario(self):
        """测试客户维护场景"""
        scenario = next(s for s in CUSTOMER_DECISION_SCENARIOS if s.id == "CUST-001")
        assert "客户价值评分" in scenario.analysis_dimensions
        assert scenario.icon == "🤝"
    
    def test_churn_scenario(self):
        """测试客户挽回场景"""
        scenario = next(s for s in CUSTOMER_DECISION_SCENARIOS if s.id == "CUST-002")
        assert "流失原因分析" in scenario.analysis_dimensions
        assert "挽回成功率" in scenario.evaluation_metrics
    
    def test_segmentation_scenario(self):
        """测试客户分级场景"""
        scenario = next(s for s in CUSTOMER_DECISION_SCENARIOS if s.id == "CUST-003")
        assert "客户贡献度" in scenario.analysis_dimensions


class TestAllDecisionScenarios:
    """测试所有决策场景"""
    
    def test_total_count(self):
        """测试总场景数量"""
        assert len(ALL_DECISION_SCENARIOS) == 15
    
    def test_all_types_covered(self):
        """测试所有决策类型都被覆盖"""
        types = set(s.decision_type for s in ALL_DECISION_SCENARIOS)
        assert types == {
            DecisionType.INVENTORY,
            DecisionType.PROCUREMENT,
            DecisionType.SALES,
            DecisionType.FINANCIAL,
            DecisionType.CUSTOMER
        }
    
    def test_all_scenarios_have_icons(self):
        """测试所有场景都有图标"""
        for scenario in ALL_DECISION_SCENARIOS:
            assert scenario.icon is not None
            assert len(scenario.icon) > 0
    
    def test_scenario_id_format(self):
        """测试场景 ID 格式"""
        for scenario in ALL_DECISION_SCENARIOS:
            assert '-' in scenario.id
            prefix = scenario.id.split('-')[0]
            assert prefix in ['INV', 'PROC', 'SALE', 'FIN', 'CUST']
    
    def test_no_duplicate_ids(self):
        """测试无重复 ID"""
        ids = [s.id for s in ALL_DECISION_SCENARIOS]
        assert len(ids) == len(set(ids)), "发现重复的场景 ID"


class TestDecisionScenarioModel:
    """测试决策场景模型"""
    
    def test_create_scenario(self):
        """测试创建场景"""
        scenario = DecisionScenario(
            id="TEST-001",
            name="测试场景",
            description="这是一个测试场景",
            decision_type=DecisionType.INVENTORY
        )
        assert scenario.id == "TEST-001"
        assert scenario.name == "测试场景"
        assert scenario.decision_type == DecisionType.INVENTORY
    
    def test_scenario_default_values(self):
        """测试场景默认值"""
        scenario = DecisionScenario(
            id="TEST-002",
            name="测试",
            description="测试",
            decision_type=DecisionType.SALES
        )
        assert scenario.icon == "📊"
        assert scenario.trigger_conditions == []
        assert scenario.decision_options == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
