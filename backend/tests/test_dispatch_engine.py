"""派单规则引擎测试"""

import pytest
from app.services.dispatch_engine import (
    DispatchRuleEngine,
    AssignmentRule,
    AssigneeSkill,
    RuleType,
    AssignmentResult
)


class TestDispatchRuleEngine:
    """测试派单规则引擎"""
    
    def setup_method(self):
        """每个测试前的准备工作"""
        self.engine = DispatchRuleEngine()
        
        # 添加测试负责人
        self.engine.add_assignee(AssigneeSkill(
            id="assignee1",
            assignee_id="user1",
            assignee_name="张三",
            skill_tags=["bug_fix", "debugging", "java"],
            max_workload=10,
            current_workload=2
        ))
        
        self.engine.add_assignee(AssigneeSkill(
            id="assignee2",
            assignee_id="user2",
            assignee_name="李四",
            skill_tags=["feature_dev", "python", "api"],
            max_workload=10,
            current_workload=5
        ))
        
        self.engine.add_assignee(AssigneeSkill(
            id="assignee3",
            assignee_id="user3",
            assignee_name="王五",
            skill_tags=["bug_fix", "testing", "python"],
            max_workload=10,
            current_workload=8
        ))
    
    def test_add_rule(self):
        """测试添加规则"""
        rule = AssignmentRule(
            id="rule1",
            rule_name="测试规则",
            rule_type=RuleType.ROUND_ROBIN,
            priority=10
        )
        
        self.engine.add_rule(rule)
        assert len(self.engine.rules) == 1
    
    def test_match_rules_no_condition(self):
        """测试无条件匹配"""
        rule = AssignmentRule(
            id="rule_default",
            rule_name="默认规则",
            rule_type=RuleType.ROUND_ROBIN,
            priority=1,
            conditions={}
        )
        self.engine.add_rule(rule)
        
        ticket = {"title": "测试工单"}
        matched = self.engine.match_rules(ticket)
        
        assert len(matched) == 1
        assert matched[0].id == "rule_default"
    
    def test_match_rules_with_condition(self):
        """测试有条件匹配"""
        rule = AssignmentRule(
            id="rule_bug",
            rule_name="BUG 规则",
            rule_type=RuleType.SKILL_BASED,
            priority=10,
            conditions={"issue_type": "BUG"}
        )
        self.engine.add_rule(rule)
        
        # 条件匹配
        ticket_bug = {"issue_type": "BUG"}
        matched = self.engine.match_rules(ticket_bug)
        assert len(matched) == 1
        
        # 条件不匹配
        ticket_feature = {"issue_type": "FEATURE"}
        matched = self.engine.match_rules(ticket_feature)
        assert len(matched) == 0
    
    def test_round_robin_assign(self):
        """测试轮询分配"""
        rule = AssignmentRule(
            id="rule_rr",
            rule_name="轮询规则",
            rule_type=RuleType.ROUND_ROBIN,
            priority=1,
            config={"assignee_ids": ["user1", "user2", "user3"]}
        )
        self.engine.add_rule(rule)
        
        ticket = {"title": "测试工单"}
        
        # 第一次分配
        result1 = self.engine.assign(ticket)
        assert result1.success is True
        assert result1.assignee_id in ["user1", "user2", "user3"]
        
        # 第二次分配（应该轮到下一个人）
        result2 = self.engine.assign(ticket)
        assert result2.success is True
        assert result2.assignee_id != result1.assignee_id or result1.assignee_id == "user3"
    
    def test_skill_based_assign(self):
        """测试技能匹配分配"""
        rule = AssignmentRule(
            id="rule_skill",
            rule_name="技能匹配",
            rule_type=RuleType.SKILL_BASED,
            priority=10,
            conditions={"issue_type": "BUG"},
            config={"required_skills": ["bug_fix", "debugging"]}
        )
        self.engine.add_rule(rule)
        
        ticket = {"issue_type": "BUG"}
        result = self.engine.assign(ticket)
        
        assert result.success is True
        assert result.assignee_id == "user1"  # 张三技能最匹配
        assert result.confidence > 0.5
    
    def test_workload_based_assign(self):
        """测试负载均衡分配"""
        rule = AssignmentRule(
            id="rule_workload",
            rule_name="负载均衡",
            rule_type=RuleType.WORKLOAD_BASED,
            priority=1,
            config={"assignee_ids": []}
        )
        self.engine.add_rule(rule)
        
        ticket = {"title": "测试工单"}
        result = self.engine.assign(ticket)
        
        assert result.success is True
        # 应该分配给工单最少的人（张三：2 个）
        assert result.assignee_id == "user1"
    
    def test_assign_no_available_assignee(self):
        """测试没有可用负责人"""
        # 设置所有负责人都不可用
        for assignee in self.engine.assignees:
            assignee.current_workload = assignee.max_workload
        
        rule = AssignmentRule(
            id="rule1",
            rule_name="测试规则",
            rule_type=RuleType.WORKLOAD_BASED,
            priority=1
        )
        self.engine.add_rule(rule)
        
        ticket = {"title": "测试工单"}
        result = self.engine.assign(ticket)
        
        assert result.success is False
        assert "没有可用的负责人" in result.reason
    
    def test_assign_no_matching_rule(self):
        """测试没有匹配的规则"""
        # 添加一个有条件但不匹配的规则
        rule = AssignmentRule(
            id="rule_bug",
            rule_name="BUG 规则",
            rule_type=RuleType.SKILL_BASED,
            priority=10,
            conditions={"issue_type": "BUG"}
        )
        self.engine.add_rule(rule)
        
        # 发送一个非 BUG 工单
        ticket = {"issue_type": "FEATURE"}
        result = self.engine.assign(ticket)
        
        assert result.success is False
        assert "没有匹配的派单规则" in result.reason
    
    def test_priority_order(self):
        """测试规则优先级顺序"""
        # 添加多个规则
        self.engine.add_rule(AssignmentRule(
            id="rule_low",
            rule_name="低优先级",
            rule_type=RuleType.ROUND_ROBIN,
            priority=1,
            conditions={}
        ))
        
        self.engine.add_rule(AssignmentRule(
            id="rule_high",
            rule_name="高优先级",
            rule_type=RuleType.SKILL_BASED,
            priority=100,
            conditions={"priority": "URGENT"}
        ))
        
        # 紧急工单应该匹配高优先级规则
        ticket = {"priority": "URGENT", "issue_type": "BUG"}
        matched = self.engine.match_rules(ticket)
        
        assert len(matched) == 2
        assert matched[0].priority == 100  # 高优先级在前
    
    def test_get_statistics(self):
        """测试获取统计信息"""
        rule = AssignmentRule(
            id="rule1",
            rule_name="测试规则",
            rule_type=RuleType.ROUND_ROBIN,
            priority=1
        )
        self.engine.add_rule(rule)
        
        stats = self.engine.get_statistics()
        
        assert stats["total_rules"] == 1
        assert stats["total_assignees"] == 3
        assert stats["available_assignees"] == 3


class TestAssigneeSkill:
    """测试负责人技能模型"""
    
    def test_can_accept(self):
        """测试是否可以接受工单"""
        assignee = AssigneeSkill(
            id="a1",
            assignee_id="user1",
            assignee_name="张三",
            max_workload=10,
            current_workload=5
        )
        
        assert assignee.can_accept() is True
        
        # 达到最大负载
        assignee.current_workload = 10
        assert assignee.can_accept() is False
        
        # 超过最大负载
        assignee.current_workload = 11
        assert assignee.can_accept() is False
    
    def test_match_skills_perfect(self):
        """测试完美技能匹配"""
        assignee = AssigneeSkill(
            id="a1",
            assignee_id="user1",
            assignee_name="张三",
            skill_tags=["bug_fix", "debugging", "java"]
        )
        
        score = assignee.match_skills(["bug_fix", "debugging"])
        assert score == 1.0
    
    def test_match_skills_partial(self):
        """测试部分技能匹配"""
        assignee = AssigneeSkill(
            id="a1",
            assignee_id="user1",
            assignee_name="张三",
            skill_tags=["bug_fix", "debugging", "java"]
        )
        
        score = assignee.match_skills(["bug_fix", "python"])
        assert score == 0.5
    
    def test_match_skills_no_match(self):
        """测试无技能匹配"""
        assignee = AssigneeSkill(
            id="a1",
            assignee_id="user1",
            assignee_name="张三",
            skill_tags=["bug_fix", "debugging"]
        )
        
        score = assignee.match_skills(["python", "api"])
        assert score == 0.0
    
    def test_match_skills_empty_required(self):
        """测试空技能要求"""
        assignee = AssigneeSkill(
            id="a1",
            assignee_id="user1",
            assignee_name="张三",
            skill_tags=["bug_fix"]
        )
        
        score = assignee.match_skills([])
        assert score == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
