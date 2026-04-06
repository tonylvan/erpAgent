"""派单规则引擎 - 实现智能分配策略"""

from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import logging
import random

logger = logging.getLogger(__name__)


class RuleType(str, Enum):
    """派单规则类型"""
    ROUND_ROBIN = "ROUND_ROBIN"  # 轮询分配
    SKILL_BASED = "SKILL_BASED"  # 技能匹配
    WORKLOAD_BASED = "WORKLOAD_BASED"  # 负载均衡
    CUSTOM = "CUSTOM"  # 自定义规则


class AssignmentRule(BaseModel):
    """派单规则模型"""
    id: str = Field(..., description="规则 ID")
    rule_name: str = Field(..., description="规则名称")
    rule_type: RuleType = Field(..., description="规则类型")
    priority: int = Field(default=0, description="规则优先级（数字越大优先级越高）")
    conditions: Optional[Dict[str, Any]] = Field(default_factory=dict, description="触发条件")
    config: Optional[Dict[str, Any]] = Field(default_factory=dict, description="规则配置")
    is_active: bool = Field(default=True, description="是否激活")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    # 统计信息
    match_count: int = Field(default=0, description="匹配次数")
    success_count: int = Field(default=0, description="成功分配次数")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AssigneeSkill(BaseModel):
    """负责人技能模型"""
    id: str = Field(..., description="ID")
    assignee_id: str = Field(..., description="负责人 ID")
    assignee_name: str = Field(..., description="负责人姓名")
    skill_tags: List[str] = Field(default_factory=list, description="技能标签列表")
    max_workload: int = Field(default=10, description="最大并发工单数")
    current_workload: int = Field(default=0, description="当前工单数")
    is_available: bool = Field(default=True, description="是否可用")
    
    def can_accept(self) -> bool:
        """检查是否可以接受新工单"""
        return self.is_available and self.current_workload < self.max_workload
    
    def match_skills(self, required_skills: List[str]) -> float:
        """
        计算技能匹配度
        
        Args:
            required_skills: 需要的技能标签
            
        Returns:
            float: 匹配度 (0.0-1.0)
        """
        if not required_skills:
            return 1.0
        
        matched = len(set(self.skill_tags) & set(required_skills))
        return matched / len(required_skills)


class AssignmentResult(BaseModel):
    """派单结果"""
    success: bool = Field(..., description="是否成功")
    assignee_id: Optional[str] = Field(None, description="负责人 ID")
    assignee_name: Optional[str] = Field(None, description="负责人姓名")
    rule_id: Optional[str] = Field(None, description="匹配的规则 ID")
    rule_name: Optional[str] = Field(None, description="匹配的规则名称")
    reason: Optional[str] = Field(None, description="分配原因/失败原因")
    confidence: float = Field(default=1.0, description="置信度 (0.0-1.0)")


class DispatchRuleEngine:
    """派单规则引擎"""
    
    def __init__(self):
        """初始化规则引擎"""
        self.rules: List[AssignmentRule] = []
        self.assignees: List[AssigneeSkill] = []
        self.round_robin_index: Dict[str, int] = {}  # 记录轮询位置
    
    def add_rule(self, rule: AssignmentRule) -> None:
        """添加规则"""
        self.rules.append(rule)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        logger.info(f"添加派单规则：{rule.rule_name} (优先级：{rule.priority})")
    
    def remove_rule(self, rule_id: str) -> bool:
        """移除规则"""
        for i, rule in enumerate(self.rules):
            if rule.id == rule_id:
                self.rules.pop(i)
                logger.info(f"移除派单规则：{rule.rule_name}")
                return True
        return False
    
    def add_assignee(self, assignee: AssigneeSkill) -> None:
        """添加负责人"""
        self.assignees.append(assignee)
        logger.info(f"添加负责人：{assignee.assignee_name}")
    
    def update_assignee_workload(self, assignee_id: str, workload: int) -> None:
        """更新负责人工单负载"""
        for assignee in self.assignees:
            if assignee.assignee_id == assignee_id:
                assignee.current_workload = workload
                break
    
    def match_rules(self, ticket: Dict[str, Any]) -> List[AssignmentRule]:
        """
        匹配适用的规则
        
        Args:
            ticket: 工单信息
            
        Returns:
            List[AssignmentRule]: 匹配的规则列表
        """
        matched_rules = []
        
        for rule in self.rules:
            if not rule.is_active:
                continue
            
            if self._check_conditions(rule, ticket):
                matched_rules.append(rule)
        
        return matched_rules
    
    def _check_conditions(self, rule: AssignmentRule, ticket: Dict[str, Any]) -> bool:
        """
        检查规则条件
        
        Args:
            rule: 规则
            ticket: 工单信息
            
        Returns:
            bool: 是否满足条件
        """
        conditions = rule.conditions or {}
        
        for key, expected_value in conditions.items():
            ticket_value = ticket.get(key)
            
            # 支持多种条件匹配
            if isinstance(expected_value, dict):
                # 复杂条件（如：$in, $eq, $gt 等）
                if not self._match_complex_condition(ticket_value, expected_value):
                    return False
            else:
                # 简单相等匹配
                if ticket_value != expected_value:
                    return False
        
        return True
    
    def _match_complex_condition(self, value: Any, condition: Dict[str, Any]) -> bool:
        """匹配复杂条件"""
        if "$in" in condition:
            return value in condition["$in"]
        elif "$eq" in condition:
            return value == condition["$eq"]
        elif "$gt" in condition:
            return value > condition["$gt"]
        elif "$gte" in condition:
            return value >= condition["$gte"]
        elif "$lt" in condition:
            return value < condition["$lt"]
        elif "$lte" in condition:
            return value <= condition["$lte"]
        elif "$ne" in condition:
            return value != condition["$ne"]
        elif "$exists" in condition:
            return (value is not None) == condition["$exists"]
        
        return True
    
    def assign(self, ticket: Dict[str, Any]) -> AssignmentResult:
        """
        执行智能派单
        
        Args:
            ticket: 工单信息
            
        Returns:
            AssignmentResult: 派单结果
        """
        # 1. 匹配适用的规则
        matched_rules = self.match_rules(ticket)
        
        if not matched_rules:
            return AssignmentResult(
                success=False,
                reason="没有匹配的派单规则"
            )
        
        # 2. 按优先级选择规则（已排序，取第一个）
        rule = matched_rules[0]
        
        # 3. 根据规则类型执行分配
        if rule.rule_type == RuleType.ROUND_ROBIN:
            result = self._round_robin_assign(rule, ticket)
        elif rule.rule_type == RuleType.SKILL_BASED:
            result = self._skill_based_assign(rule, ticket)
        elif rule.rule_type == RuleType.WORKLOAD_BASED:
            result = self._workload_based_assign(rule, ticket)
        elif rule.rule_type == RuleType.CUSTOM:
            result = self._custom_assign(rule, ticket)
        else:
            result = AssignmentResult(
                success=False,
                reason=f"未知的规则类型：{rule.rule_type}"
            )
        
        # 4. 更新统计
        if result.success:
            rule.match_count += 1
            rule.success_count += 1
        
        return result
    
    def _round_robin_assign(self, rule: AssignmentRule, ticket: Dict[str, Any]) -> AssignmentResult:
        """
        轮询分配
        
        按顺序循环分配给负责人列表中的成员
        """
        config = rule.config or {}
        assignee_ids = config.get("assignee_ids", [])
        
        if not assignee_ids:
            return AssignmentResult(
                success=False,
                reason="轮询规则未配置负责人列表"
            )
        
        # 获取当前轮询位置
        if rule.id not in self.round_robin_index:
            self.round_robin_index[rule.id] = 0
        
        # 找到下一个可用的负责人
        for _ in range(len(assignee_ids)):
            current_index = self.round_robin_index[rule.id]
            assignee_id = assignee_ids[current_index]
            
            # 更新轮询位置
            self.round_robin_index[rule.id] = (current_index + 1) % len(assignee_ids)
            
            # 检查负责人是否可用
            assignee = self._get_assignee(assignee_id)
            if assignee and assignee.can_accept():
                return AssignmentResult(
                    success=True,
                    assignee_id=assignee.assignee_id,
                    assignee_name=assignee.assignee_name,
                    rule_id=rule.id,
                    rule_name=rule.rule_name,
                    reason="轮询分配",
                    confidence=1.0
                )
        
        return AssignmentResult(
            success=False,
            rule_id=rule.id,
            rule_name=rule.rule_name,
            reason="所有负责人都不可用"
        )
    
    def _skill_based_assign(self, rule: AssignmentRule, ticket: Dict[str, Any]) -> AssignmentResult:
        """
        技能匹配分配
        
        根据工单需要的技能标签，匹配最合适的负责人
        """
        config = rule.config or {}
        required_skills = config.get("required_skills", [])
        
        # 从工单中获取技能要求（如果配置了字段映射）
        skill_field = config.get("skill_field", "issue_type")
        if skill_field in ticket:
            required_skills = ticket[skill_field] if isinstance(ticket[skill_field], list) else [ticket[skill_field]]
        
        # 计算每个负责人的匹配度
        candidates = []
        for assignee in self.assignees:
            if not assignee.can_accept():
                continue
            
            match_score = assignee.match_skills(required_skills)
            if match_score > 0:
                candidates.append((assignee, match_score))
        
        if not candidates:
            return AssignmentResult(
                success=False,
                rule_id=rule.id,
                rule_name=rule.rule_name,
                reason="没有匹配技能的可用负责人"
            )
        
        # 选择匹配度最高的
        candidates.sort(key=lambda x: x[1], reverse=True)
        best_assignee, confidence = candidates[0]
        
        return AssignmentResult(
            success=True,
            assignee_id=best_assignee.assignee_id,
            assignee_name=best_assignee.assignee_name,
            rule_id=rule.id,
            rule_name=rule.rule_name,
            reason=f"技能匹配度：{confidence:.0%}",
            confidence=confidence
        )
    
    def _workload_based_assign(self, rule: AssignmentRule, ticket: Dict[str, Any]) -> AssignmentResult:
        """
        负载均衡分配
        
        分配给当前工单数最少的负责人
        """
        config = rule.config or {}
        assignee_ids = config.get("assignee_ids", [])
        
        # 筛选可用的负责人
        available = []
        for assignee in self.assignees:
            if not assignee.can_accept():
                continue
            if assignee_ids and assignee.assignee_id not in assignee_ids:
                continue
            available.append(assignee)
        
        if not available:
            return AssignmentResult(
                success=False,
                rule_id=rule.id,
                rule_name=rule.rule_name,
                reason="没有可用的负责人"
            )
        
        # 选择工单数最少的
        available.sort(key=lambda a: a.current_workload)
        best_assignee = available[0]
        
        # 计算置信度（基于负载余量）
        workload_ratio = 1.0 - (best_assignee.current_workload / best_assignee.max_workload)
        confidence = 0.5 + (workload_ratio * 0.5)  # 0.5-1.0
        
        return AssignmentResult(
            success=True,
            assignee_id=best_assignee.assignee_id,
            assignee_name=best_assignee.assignee_name,
            rule_id=rule.id,
            rule_name=rule.rule_name,
            reason=f"负载均衡（当前工单：{best_assignee.current_workload}）",
            confidence=confidence
        )
    
    def _custom_assign(self, rule: AssignmentRule, ticket: Dict[str, Any]) -> AssignmentResult:
        """
        自定义分配
        
        使用自定义的分配逻辑（通过配置）
        """
        config = rule.config or {}
        custom_logic = config.get("custom_logic", {})
        
        # 支持简单的自定义逻辑
        if "assign_to" in custom_logic:
            assignee_id = custom_logic["assign_to"]
            assignee = self._get_assignee(assignee_id)
            
            if assignee and assignee.can_accept():
                return AssignmentResult(
                    success=True,
                    assignee_id=assignee.assignee_id,
                    assignee_name=assignee.assignee_name,
                    rule_id=rule.id,
                    rule_name=rule.rule_name,
                    reason="自定义规则分配",
                    confidence=1.0
                )
        
        return AssignmentResult(
            success=False,
            rule_id=rule.id,
            rule_name=rule.rule_name,
            reason="自定义规则执行失败"
        )
    
    def _get_assignee(self, assignee_id: str) -> Optional[AssigneeSkill]:
        """根据 ID 获取负责人"""
        for assignee in self.assignees:
            if assignee.assignee_id == assignee_id:
                return assignee
        return None
    
    def get_available_assignees(self) -> List[AssigneeSkill]:
        """获取所有可用的负责人"""
        return [a for a in self.assignees if a.can_accept()]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取引擎统计信息"""
        return {
            "total_rules": len(self.rules),
            "active_rules": len([r for r in self.rules if r.is_active]),
            "total_assignees": len(self.assignees),
            "available_assignees": len([a for a in self.assignees if a.can_accept()]),
            "rule_stats": [
                {
                    "rule_name": r.rule_name,
                    "match_count": r.match_count,
                    "success_count": r.success_count,
                    "success_rate": r.success_count / r.match_count if r.match_count > 0 else 0
                }
                for r in self.rules
            ]
        }


# 默认规则配置
DEFAULT_RULES = [
    AssignmentRule(
        id="rule_urgent",
        rule_name="紧急工单优先分配",
        rule_type=RuleType.WORKLOAD_BASED,
        priority=100,
        conditions={"priority": "URGENT"},
        config={"assignee_ids": []}  # 空表示所有负责人
    ),
    AssignmentRule(
        id="rule_skill_bug",
        rule_name="BUG 类工单技能匹配",
        rule_type=RuleType.SKILL_BASED,
        priority=50,
        conditions={"issue_type": "BUG"},
        config={"required_skills": ["bug_fix", "debugging"], "skill_field": "issue_type"}
    ),
    AssignmentRule(
        id="rule_default",
        rule_name="默认轮询分配",
        rule_type=RuleType.ROUND_ROBIN,
        priority=1,
        conditions={},
        config={"assignee_ids": []}
    )
]
