"""工单工作流测试"""

import pytest
from datetime import datetime, timedelta
from app.models.task import Task, TaskStatus, TaskPriority, TaskStatusMachine, TaskTransitionError
from app.services.ticket_workflow import TicketWorkflowService, WorkflowAction
import uuid


class TestTaskStatusMachine:
    """测试工单状态机"""
    
    def test_valid_transition_pending_to_in_progress(self):
        """测试 PENDING -> IN_PROGRESS 合法转换"""
        assert TaskStatusMachine.can_transition(TaskStatus.PENDING, TaskStatus.IN_PROGRESS)
    
    def test_valid_transition_in_progress_to_pending_validation(self):
        """测试 IN_PROGRESS -> PENDING_VALIDATION 合法转换"""
        assert TaskStatusMachine.can_transition(TaskStatus.IN_PROGRESS, TaskStatus.PENDING_VALIDATION)
    
    def test_valid_transition_pending_validation_to_resolved(self):
        """测试 PENDING_VALIDATION -> RESOLVED 合法转换"""
        assert TaskStatusMachine.can_transition(TaskStatus.PENDING_VALIDATION, TaskStatus.RESOLVED)
    
    def test_valid_transition_resolved_to_closed(self):
        """测试 RESOLVED -> CLOSED 合法转换"""
        assert TaskStatusMachine.can_transition(TaskStatus.RESOLVED, TaskStatus.CLOSED)
    
    def test_invalid_transition_pending_to_closed(self):
        """测试 PENDING -> CLOSED 非法转换"""
        assert not TaskStatusMachine.can_transition(TaskStatus.PENDING, TaskStatus.CLOSED)
    
    def test_invalid_transition_closed_to_any(self):
        """测试 CLOSED 终态不可转换"""
        assert not TaskStatusMachine.can_transition(TaskStatus.CLOSED, TaskStatus.IN_PROGRESS)
    
    def test_transition_method_success(self):
        """测试 transition 方法成功"""
        result = TaskStatusMachine.transition(TaskStatus.PENDING, TaskStatus.IN_PROGRESS)
        assert result is True
    
    def test_transition_method_failure(self):
        """测试 transition 方法失败抛出异常"""
        with pytest.raises(TaskTransitionError):
            TaskStatusMachine.transition(TaskStatus.PENDING, TaskStatus.CLOSED)


class TestTaskModel:
    """测试工单模型"""
    
    def test_create_task(self):
        """测试创建工单"""
        task = Task(
            id=str(uuid.uuid4()),
            title="测试工单",
            description="这是一个测试工单"
        )
        assert task.status == TaskStatus.PENDING
        assert task.priority == TaskPriority.MEDIUM
        assert task.created_at is not None
    
    def test_assign_task(self):
        """测试分配工单"""
        task = Task(
            id=str(uuid.uuid4()),
            title="测试工单"
        )
        
        task.assign_to(
            assignee_id="user123",
            assignee_name="张三",
            assignee_email="zhangsan@example.com",
            operator_id="admin"
        )
        
        assert task.assignee_id == "user123"
        assert task.assignee_name == "张三"
        assert task.due_date is not None
        assert len(task.logs) > 0
        assert task.logs[0].action == "ASSIGN"
    
    def test_transition_to_success(self):
        """测试状态转换成功"""
        task = Task(
            id=str(uuid.uuid4()),
            title="测试工单"
        )
        
        task.transition_to(
            new_status=TaskStatus.IN_PROGRESS,
            operator_id="user123",
            operator_name="张三",
            comment="开始处理"
        )
        
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.started_at is not None
        assert len(task.logs) == 1
    
    def test_transition_to_invalid(self):
        """测试非法状态转换抛出异常"""
        task = Task(
            id=str(uuid.uuid4()),
            title="测试工单",
            status=TaskStatus.PENDING
        )
        
        with pytest.raises(TaskTransitionError):
            task.transition_to(new_status=TaskStatus.CLOSED)
    
    def test_is_overdue(self):
        """测试超时检测"""
        task = Task(
            id=str(uuid.uuid4()),
            title="测试工单",
            due_date=datetime.now() - timedelta(hours=1)
        )
        
        assert task.is_overdue() is True
        
        # 已关闭的工单不超时
        task.status = TaskStatus.CLOSED
        assert task.is_overdue() is False
    
    def test_get_remaining_time(self):
        """测试剩余时间计算"""
        due_date = datetime.now() + timedelta(hours=2)
        task = Task(
            id=str(uuid.uuid4()),
            title="测试工单",
            due_date=due_date
        )
        
        remaining = task.get_remaining_time()
        assert remaining is not None
        assert 1.9 < remaining < 2.1  # 允许小误差


class TestTicketWorkflowService:
    """测试工单工作流服务"""
    
    def setup_method(self):
        """每个测试前的准备工作"""
        self.service = TicketWorkflowService()
        self.task = Task(
            id=str(uuid.uuid4()),
            title="测试工单",
            description="测试描述"
        )
    
    def test_assign_ticket(self):
        """测试分配工单"""
        result = self.service.assign_ticket(
            ticket=self.task,
            assignee_id="user123",
            assignee_name="张三",
            operator_id="admin",
            operator_name="管理员"
        )
        
        assert result.assignee_id == "user123"
        assert result.status == TaskStatus.IN_PROGRESS
        assert len(result.logs) >= 1
    
    def test_transfer_ticket(self):
        """测试转派工单"""
        # 先分配
        self.service.assign_ticket(
            ticket=self.task,
            assignee_id="user123",
            assignee_name="张三"
        )
        
        # 再转派
        result = self.service.transfer_ticket(
            ticket=self.task,
            new_assignee_id="user456",
            new_assignee_name="李四",
            operator_name="管理员",
            comment="工作调整"
        )
        
        assert result.assignee_id == "user456"
        assert result.logs[-1].action == WorkflowAction.TRANSFER
    
    def test_transfer_to_same_assignee(self):
        """测试转派给同一人抛出异常"""
        self.service.assign_ticket(
            ticket=self.task,
            assignee_id="user123",
            assignee_name="张三"
        )
        
        with pytest.raises(ValueError, match="不能转派给当前负责人"):
            self.service.transfer_ticket(
                ticket=self.task,
                new_assignee_id="user123",
                new_assignee_name="张三"
            )
    
    def test_escalate_ticket(self):
        """测试升级工单"""
        assert self.task.priority == TaskPriority.MEDIUM
        
        result = self.service.escalate_ticket(
            ticket=self.task,
            reason="客户投诉",
            operator_name="管理员"
        )
        
        assert result.priority == TaskPriority.HIGH
        assert result.logs[-1].action == WorkflowAction.ESCALATE
    
    def test_escalate_already_urgent(self):
        """测试已经是紧急优先级无法升级"""
        self.task.priority = TaskPriority.URGENT
        
        with pytest.raises(ValueError, match="已经是最高优先级"):
            self.service.escalate_ticket(
                ticket=self.task,
                reason="非常重要"
            )
    
    def test_resolve_ticket(self):
        """测试解决工单"""
        self.task.status = TaskStatus.PENDING_VALIDATION
        
        result = self.service.resolve_ticket(
            ticket=self.task,
            resolution_notes="问题已解决",
            operator_name="张三"
        )
        
        assert result.status == TaskStatus.RESOLVED
        assert result.resolved_at is not None
    
    def test_close_ticket(self):
        """测试关闭工单"""
        self.task.status = TaskStatus.RESOLVED
        
        result = self.service.close_ticket(
            ticket=self.task,
            closing_notes="确认无误，关闭",
            operator_name="管理员"
        )
        
        assert result.status == TaskStatus.CLOSED
        assert result.closed_at is not None
    
    def test_get_workflow_logs(self):
        """测试获取工作流日志"""
        self.service.assign_ticket(
            ticket=self.task,
            assignee_id="user123",
            assignee_name="张三"
        )
        
        logs = self.service.get_workflow_logs(self.task)
        assert len(logs) > 0
        assert logs[0]['action'] == 'ASSIGN'
    
    def test_validate_transition(self):
        """测试验证状态转换"""
        self.task.status = TaskStatus.PENDING
        
        assert self.service.validate_transition(self.task, TaskStatus.IN_PROGRESS) is True
        assert self.service.validate_transition(self.task, TaskStatus.CLOSED) is False


class TestWorkflowIntegration:
    """测试工作流集成"""
    
    def test_full_workflow(self):
        """测试完整工单流程"""
        service = TicketWorkflowService()
        task = Task(
            id=str(uuid.uuid4()),
            title="完整流程测试",
            priority=TaskPriority.MEDIUM
        )
        
        # 1. 分配
        service.assign_ticket(
            ticket=task,
            assignee_id="user123",
            assignee_name="张三"
        )
        assert task.status == TaskStatus.IN_PROGRESS
        
        # 2. 升级
        service.escalate_ticket(
            ticket=task,
            reason="优先级提升"
        )
        assert task.priority == TaskPriority.HIGH
        
        # 3. 转为待验证
        task.transition_to(
            new_status=TaskStatus.PENDING_VALIDATION,
            operator_name="张三",
            comment="申请验证"
        )
        
        # 4. 解决
        service.resolve_ticket(
            ticket=task,
            resolution_notes="已完成"
        )
        assert task.status == TaskStatus.RESOLVED
        
        # 5. 关闭
        service.close_ticket(
            ticket=task,
            closing_notes="确认关闭"
        )
        assert task.status == TaskStatus.CLOSED
        
        # 验证日志数量
        assert len(task.logs) >= 4
    
    def test_cannot_close_pending_ticket(self):
        """测试不能直接关闭待处理工单"""
        service = TicketWorkflowService()
        task = Task(
            id=str(uuid.uuid4()),
            title="测试工单",
            status=TaskStatus.PENDING
        )
        
        with pytest.raises(TaskTransitionError):
            service.close_ticket(ticket=task)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
