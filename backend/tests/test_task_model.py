"""工单模型测试 - 状态机转换测试"""

import pytest
from datetime import datetime, timedelta
from app.models.task import (
    Task, TaskStatus, TaskPriority, TaskLog,
    TaskStatusMachine, TaskTransitionError,
    TaskFilter, TaskStatistics
)


class TestTaskStatusMachine:
    """测试工单状态机"""
    
    def test_valid_transitions_pending(self):
        """测试 PENDING 状态的合法转换"""
        assert TaskStatusMachine.can_transition(TaskStatus.PENDING, TaskStatus.IN_PROGRESS)
        assert TaskStatusMachine.can_transition(TaskStatus.PENDING, TaskStatus.TIMEOUT)
        assert TaskStatusMachine.can_transition(TaskStatus.PENDING, TaskStatus.CANCELLED)
        assert not TaskStatusMachine.can_transition(TaskStatus.PENDING, TaskStatus.RESOLVED)
        assert not TaskStatusMachine.can_transition(TaskStatus.PENDING, TaskStatus.CLOSED)
    
    def test_valid_transitions_in_progress(self):
        """测试 IN_PROGRESS 状态的合法转换"""
        assert TaskStatusMachine.can_transition(TaskStatus.IN_PROGRESS, TaskStatus.PENDING_VALIDATION)
        assert TaskStatusMachine.can_transition(TaskStatus.IN_PROGRESS, TaskStatus.TIMEOUT)
        assert TaskStatusMachine.can_transition(TaskStatus.IN_PROGRESS, TaskStatus.CANCELLED)
        assert not TaskStatusMachine.can_transition(TaskStatus.IN_PROGRESS, TaskStatus.PENDING)
        assert not TaskStatusMachine.can_transition(TaskStatus.IN_PROGRESS, TaskStatus.CLOSED)
    
    def test_valid_transitions_pending_validation(self):
        """测试 PENDING_VALIDATION 状态的合法转换"""
        assert TaskStatusMachine.can_transition(TaskStatus.PENDING_VALIDATION, TaskStatus.RESOLVED)
        assert TaskStatusMachine.can_transition(TaskStatus.PENDING_VALIDATION, TaskStatus.IN_PROGRESS)
        assert TaskStatusMachine.can_transition(TaskStatus.PENDING_VALIDATION, TaskStatus.TIMEOUT)
        assert TaskStatusMachine.can_transition(TaskStatus.PENDING_VALIDATION, TaskStatus.CANCELLED)
        assert not TaskStatusMachine.can_transition(TaskStatus.PENDING_VALIDATION, TaskStatus.PENDING)
    
    def test_valid_transitions_resolved(self):
        """测试 RESOLVED 状态的合法转换"""
        assert TaskStatusMachine.can_transition(TaskStatus.RESOLVED, TaskStatus.CLOSED)
        assert TaskStatusMachine.can_transition(TaskStatus.RESOLVED, TaskStatus.IN_PROGRESS)
        assert not TaskStatusMachine.can_transition(TaskStatus.RESOLVED, TaskStatus.PENDING)
        assert not TaskStatusMachine.can_transition(TaskStatus.RESOLVED, TaskStatus.PENDING_VALIDATION)
    
    def test_terminal_states(self):
        """测试终态（CLOSED 和 CANCELLED）"""
        # CLOSED 是终态，不能有转换
        assert TaskStatusMachine.get_valid_transitions(TaskStatus.CLOSED) == []
        assert not TaskStatusMachine.can_transition(TaskStatus.CLOSED, TaskStatus.IN_PROGRESS)
        
        # CANCELLED 是终态，不能有转换
        assert TaskStatusMachine.get_valid_transitions(TaskStatus.CANCELLED) == []
        assert not TaskStatusMachine.can_transition(TaskStatus.CANCELLED, TaskStatus.IN_PROGRESS)
    
    def test_transition_method_success(self):
        """测试 transition 方法成功场景"""
        # 不应该抛出异常
        result = TaskStatusMachine.transition(TaskStatus.PENDING, TaskStatus.IN_PROGRESS)
        assert result is True
    
    def test_transition_method_failure(self):
        """测试 transition 方法失败场景"""
        with pytest.raises(TaskTransitionError):
            TaskStatusMachine.transition(TaskStatus.PENDING, TaskStatus.CLOSED)
    
    def test_get_valid_transitions(self):
        """测试获取合法转换列表"""
        transitions = TaskStatusMachine.get_valid_transitions(TaskStatus.PENDING)
        assert TaskStatus.IN_PROGRESS in transitions
        assert TaskStatus.TIMEOUT in transitions
        assert TaskStatus.CANCELLED in transitions
        assert len(transitions) == 3


class TestTaskModel:
    """测试工单模型"""
    
    def test_create_task_basic(self):
        """测试创建基本工单"""
        task = Task(
            id="TASK-001",
            title="测试工单",
            description="这是一个测试工单"
        )
        
        assert task.id == "TASK-001"
        assert task.title == "测试工单"
        assert task.description == "这是一个测试工单"
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.MEDIUM
        assert task.assignee_id is None
        assert task.logs == []
    
    def test_task_with_assignee(self):
        """测试带负责人的工单"""
        task = Task(
            id="TASK-002",
            title="分配工单",
            assignee_id="EMP-123",
            assignee_name="张三",
            assignee_email="zhangsan@example.com"
        )
        
        assert task.assignee_id == "EMP-123"
        assert task.assignee_name == "张三"
        assert task.assignee_email == "zhangsan@example.com"
    
    def test_task_with_priority(self):
        """测试不同优先级的工单"""
        task_urgent = Task(id="TASK-003", title="紧急工单", priority=TaskPriority.URGENT)
        task_low = Task(id="TASK-004", title="低优先级工单", priority=TaskPriority.LOW)
        
        assert task_urgent.priority == TaskPriority.URGENT
        assert task_low.priority == TaskPriority.LOW
        assert task_urgent.get_timeout_hours() == 2
        assert task_low.get_timeout_hours() == 168
    
    def test_task_status_transitions(self):
        """测试工单状态转换"""
        task = Task(id="TASK-005", title="状态转换测试")
        
        # PENDING -> IN_PROGRESS
        task.transition_to(TaskStatus.IN_PROGRESS, operator_id="EMP-123", operator_name="张三")
        assert task.status == TaskStatus.IN_PROGRESS
        assert len(task.logs) == 1
        assert task.logs[0].action == "STATUS_CHANGE"
        assert task.logs[0].from_status == "PENDING"
        assert task.logs[0].to_status == "IN_PROGRESS"
        
        # IN_PROGRESS -> PENDING_VALIDATION
        task.transition_to(TaskStatus.PENDING_VALIDATION, comment="完成处理，等待验证")
        assert task.status == TaskStatus.PENDING_VALIDATION
        assert len(task.logs) == 2
        
        # PENDING_VALIDATION -> RESOLVED
        task.transition_to(TaskStatus.RESOLVED, comment="验证通过")
        assert task.status == TaskStatus.RESOLVED
        assert task.resolved_at is not None
        assert len(task.logs) == 3
        
        # RESOLVED -> CLOSED
        task.transition_to(TaskStatus.CLOSED)
        assert task.status == TaskStatus.CLOSED
        assert task.closed_at is not None
        assert len(task.logs) == 4
    
    def test_invalid_status_transition(self):
        """测试非法状态转换"""
        task = Task(id="TASK-006", title="非法转换测试")
        
        with pytest.raises(TaskTransitionError):
            task.transition_to(TaskStatus.CLOSED)  # PENDING 不能直接到 CLOSED
        
        # 状态应该保持不变
        assert task.status == TaskStatus.PENDING
    
    def test_task_assignment(self):
        """测试工单分配"""
        task = Task(id="TASK-007", title="分配测试")
        
        # 初始无负责人
        assert task.assignee_id is None
        
        # 分配负责人
        task.assign_to("EMP-456", "李四", "lisi@example.com")
        
        assert task.assignee_id == "EMP-456"
        assert task.assignee_name == "李四"
        assert task.assignee_email == "lisi@example.com"
        assert task.due_date is not None  # 自动设置截止时间
        assert len(task.logs) == 1
        assert task.logs[0].action == "ASSIGN"
    
    def test_task_assignment_with_priority(self):
        """测试不同优先级的工单分配（截止时间不同）"""
        task_urgent = Task(id="TASK-008", title="紧急", priority=TaskPriority.URGENT)
        task_low = Task(id="TASK-009", title="低优", priority=TaskPriority.LOW)
        
        before = datetime.now()
        task_urgent.assign_to("EMP-001", "员工 1")
        task_low.assign_to("EMP-002", "员工 2")
        after = datetime.now()
        
        # 紧急工单截止时间应该在 2 小时后
        assert task_urgent.due_date >= before + timedelta(hours=2)
        assert task_urgent.due_date <= after + timedelta(hours=2)
        
        # 低优先级工单截止时间应该在 168 小时后
        assert task_low.due_date >= before + timedelta(hours=168)
        assert task_low.due_date <= after + timedelta(hours=168)
    
    def test_task_add_log(self):
        """测试添加日志"""
        task = Task(id="TASK-010", title="日志测试")
        
        task.add_log(
            action="COMMENT",
            comment="这是一条备注",
            operator_id="EMP-789",
            operator_name="王五",
            metadata={"key": "value"}
        )
        
        assert len(task.logs) == 1
        assert task.logs[0].action == "COMMENT"
        assert task.logs[0].comment == "这是一条备注"
        assert task.logs[0].operator_id == "EMP-789"
        assert task.logs[0].metadata == {"key": "value"}
    
    def test_task_overdue_check(self):
        """测试超时检查"""
        task = Task(id="TASK-011", title="超时测试")
        
        # 无截止时间，不超时
        assert task.is_overdue() is False
        assert task.get_remaining_time() is None
        
        # 设置未来截止时间，不超时
        task.due_date = datetime.now() + timedelta(hours=1)
        assert task.is_overdue() is False
        assert task.get_remaining_time() > 0
        
        # 设置过去截止时间，超时
        task.due_date = datetime.now() - timedelta(hours=1)
        task.status = TaskStatus.IN_PROGRESS  # 非终态
        assert task.is_overdue() is True
        assert task.get_remaining_time() == 0
    
    def test_task_overdue_terminal_state(self):
        """测试终态工单即使截止时间过去也不算超时"""
        task = Task(id="TASK-012", title="终态测试")
        task.due_date = datetime.now() - timedelta(hours=1)
        
        # 终态：CLOSED
        task.status = TaskStatus.CLOSED
        assert task.is_overdue() is False
        
        # 终态：CANCELLED
        task.status = TaskStatus.CANCELLED
        assert task.is_overdue() is False
        
        # 终态：RESOLVED
        task.status = TaskStatus.RESOLVED
        assert task.is_overdue() is False
    
    def test_task_to_dict(self):
        """测试转换为字典"""
        task = Task(id="TASK-013", title="字典转换测试")
        task_dict = task.to_dict()
        
        assert task_dict['id'] == "TASK-013"
        assert task_dict['title'] == "字典转换测试"
        assert 'status' in task_dict
        assert 'priority' in task_dict
        assert 'created_at' in task_dict
    
    def test_task_from_dict(self):
        """测试从字典创建"""
        task_dict = {
            "id": "TASK-014",
            "title": "从字典创建",
            "description": "测试",
            "status": TaskStatus.IN_PROGRESS,
            "priority": TaskPriority.HIGH
        }
        
        task = Task.from_dict(task_dict)
        
        assert task.id == "TASK-014"
        assert task.title == "从字典创建"
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.priority == TaskPriority.HIGH
    
    def test_task_timestamps(self):
        """测试时间戳自动设置"""
        before = datetime.now()
        task = Task(id="TASK-015", title="时间戳测试")
        after = datetime.now()
        
        assert task.created_at >= before
        assert task.created_at <= after
        assert task.updated_at >= before
        assert task.updated_at <= after
        
        # 状态转换后更新时间
        import time
        time.sleep(0.01)  # 确保时间差
        before_transition = datetime.now()
        task.transition_to(TaskStatus.IN_PROGRESS)
        after_transition = datetime.now()
        
        assert task.updated_at >= before_transition
        assert task.updated_at <= after_transition
        # created_at 不应该改变
        assert task.created_at < task.updated_at
    
    def test_task_status_timestamps(self):
        """测试状态相关时间戳"""
        task = Task(id="TASK-016", title="状态时间戳测试")
        
        # 初始状态
        assert task.started_at is None
        assert task.resolved_at is None
        assert task.closed_at is None
        
        # IN_PROGRESS 设置 started_at
        task.transition_to(TaskStatus.IN_PROGRESS)
        assert task.started_at is not None
        
        # RESOLVED 设置 resolved_at
        task.transition_to(TaskStatus.PENDING_VALIDATION)
        task.transition_to(TaskStatus.RESOLVED)
        assert task.resolved_at is not None
        assert task.resolved_at >= task.started_at
        
        # CLOSED 设置 closed_at
        task.transition_to(TaskStatus.CLOSED)
        assert task.closed_at is not None
        assert task.closed_at >= task.resolved_at


class TestTaskFilter:
    """测试工单筛选"""
    
    def test_create_filter(self):
        """测试创建筛选条件"""
        filter = TaskFilter(
            status=[TaskStatus.PENDING, TaskStatus.IN_PROGRESS],
            priority=[TaskPriority.URGENT, TaskPriority.HIGH],
            assignee_id="EMP-123",
            is_overdue=True
        )
        
        assert len(filter.status) == 2
        assert len(filter.priority) == 2
        assert filter.assignee_id == "EMP-123"
        assert filter.is_overdue is True


class TestTaskStatistics:
    """测试工单统计"""
    
    def test_create_statistics(self):
        """测试创建统计对象"""
        stats = TaskStatistics(
            total=100,
            by_status={"PENDING": 20, "IN_PROGRESS": 30, "CLOSED": 50},
            by_priority={"URGENT": 10, "HIGH": 30, "MEDIUM": 40, "LOW": 20},
            overdue_count=5,
            avg_resolution_hours=24.5
        )
        
        assert stats.total == 100
        assert stats.by_status["PENDING"] == 20
        assert stats.by_priority["URGENT"] == 10
        assert stats.overdue_count == 5
        assert stats.avg_resolution_hours == 24.5


class TestTaskLog:
    """测试工单日志"""
    
    def test_create_log(self):
        """测试创建日志"""
        log = TaskLog(
            task_id="TASK-017",
            action="STATUS_CHANGE",
            from_status="PENDING",
            to_status="IN_PROGRESS",
            operator_id="EMP-123",
            operator_name="张三",
            comment="开始处理"
        )
        
        assert log.task_id == "TASK-017"
        assert log.action == "STATUS_CHANGE"
        assert log.from_status == "PENDING"
        assert log.to_status == "IN_PROGRESS"
        assert log.operator_id == "EMP-123"
        assert log.operator_name == "张三"
        assert log.comment == "开始处理"
        assert log.created_at is not None


class TestCompleteWorkflow:
    """测试完整工单流程"""
    
    def test_full_lifecycle(self):
        """测试完整生命周期"""
        # 创建工单
        task = Task(
            id="TASK-018",
            title="完整流程测试",
            description="从创建到闭环的完整流程",
            priority=TaskPriority.HIGH
        )
        
        # 分配
        task.assign_to("EMP-001", "张三")
        assert task.status == TaskStatus.PENDING
        assert task.assignee_id == "EMP-001"
        
        # 开始处理
        task.transition_to(TaskStatus.IN_PROGRESS, operator_id="EMP-001", operator_name="张三")
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.started_at is not None
        
        # 添加处理日志
        task.add_log(
            action="PROGRESS_UPDATE",
            comment="已完成 50%",
            operator_id="EMP-001",
            operator_name="张三"
        )
        assert len(task.logs) == 3  # ASSIGN + STATUS_CHANGE + PROGRESS_UPDATE
        
        # 提交验证
        task.transition_to(TaskStatus.PENDING_VALIDATION, comment="处理完成，申请验证")
        assert task.status == TaskStatus.PENDING_VALIDATION
        
        # 验证不通过，重新处理
        task.transition_to(TaskStatus.IN_PROGRESS, comment="验证不通过，需要补充材料")
        assert task.status == TaskStatus.IN_PROGRESS
        
        # 再次处理完成
        task.add_log(action="PROGRESS_UPDATE", comment="补充材料完成")
        task.transition_to(TaskStatus.PENDING_VALIDATION, comment="重新提交验证")
        
        # 验证通过
        task.transition_to(TaskStatus.RESOLVED, comment="验证通过")
        assert task.status == TaskStatus.RESOLVED
        assert task.resolved_at is not None
        
        # 闭环
        task.transition_to(TaskStatus.CLOSED, comment="问题已闭环")
        assert task.status == TaskStatus.CLOSED
        assert task.closed_at is not None
        
        # 验证日志数量
        assert len(task.logs) >= 8
        
        # 验证终态不可转换
        with pytest.raises(TaskTransitionError):
            task.transition_to(TaskStatus.IN_PROGRESS)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
