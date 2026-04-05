"""问题生命周期集成测试 - 完整流程测试"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from app.models.task import Task, TaskStatus, TaskPriority, TaskLog, TaskTransitionError
from app.services.issue_tracker import IssueTracker, create_issue_and_task


@pytest.fixture
def mock_neo4j_service():
    """模拟 Neo4j 服务"""
    mock_service = Mock()
    mock_service.execute_query = Mock(return_value=[])
    return mock_service


@pytest.fixture
def tracker(mock_neo4j_service):
    """创建 IssueTracker 实例"""
    with patch('app.services.issue_tracker.get_neo4j_service', return_value=mock_neo4j_service):
        tracker = IssueTracker()
        yield tracker


class TestIssueLifecycle:
    """测试问题完整生命周期"""
    
    def test_issue_creation_to_assignment(self, mock_neo4j_service):
        """测试问题从创建到分配"""
        # 设置模拟返回
        mock_neo4j_service.execute_query.return_value = [{"id": "TEST"}]
        
        # 使用 patch 创建 tracker 和便捷函数
        with patch('app.services.issue_tracker.get_neo4j_service', return_value=mock_neo4j_service):
            # 创建 Issue 和 Task
            issue_id, task_id = create_issue_and_task(
                title="库存预警",
                description="iPhone 15 Pro 库存为 0",
                severity="HIGH",
                issue_type="INVENTORY",
                assignee_id="EMP-001",
                assignee_name="张三",
                priority=TaskPriority.URGENT
            )
            
            # 验证 ID 生成
            assert issue_id.startswith("ISSUE-")
            assert task_id.startswith("TASK-")
            
            # 验证 Neo4j 调用（创建 Issue、Task、Employee、关联关系）
            assert mock_neo4j_service.execute_query.call_count >= 1
    
    def test_complete_workflow_with_mocks(self, tracker, mock_neo4j_service):
        """测试完整工作流程：创建→分配→处理→验证→闭环"""
        # 设置模拟返回
        mock_neo4j_service.execute_query.return_value = [{"id": "TEST"}]
        
        # 1. 创建 Issue 和 Task
        issue_id, task_id = create_issue_and_task(
            title="客户投诉处理",
            description="客户反映产品质量问题",
            severity="MEDIUM",
            issue_type="COMPLAINT",
            assignee_id="EMP-001",
            assignee_name="李四",
            priority=TaskPriority.HIGH
        )
        
        # 2. 在内存中创建 Task 对象进行状态转换
        task = Task(
            id=task_id,
            title="客户投诉处理",
            description="客户反映产品质量问题",
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH,
            assignee_id="EMP-001",
            assignee_name="李四",
            issue_type="COMPLAINT"
        )
        
        # 3. 开始处理（PENDING -> IN_PROGRESS）
        mock_neo4j_service.execute_query.return_value = [{"id": task_id}]
        task.transition_to(
            TaskStatus.IN_PROGRESS,
            operator_id="EMP-001",
            operator_name="李四",
            comment="开始处理客户投诉"
        )
        assert task.status == TaskStatus.IN_PROGRESS
        assert task.started_at is not None
        
        # 4. 更新 Neo4j 状态
        tracker.update_task_status(task_id, "IN_PROGRESS")
        
        # 5. 添加处理日志
        log = TaskLog(
            task_id=task_id,
            action="PROGRESS_UPDATE",
            comment="已联系客户，了解详细情况",
            operator_id="EMP-001",
            operator_name="李四"
        )
        tracker.add_task_log(task_id, log)
        
        # 6. 提交验证（IN_PROGRESS -> PENDING_VALIDATION）
        task.transition_to(
            TaskStatus.PENDING_VALIDATION,
            operator_id="EMP-001",
            operator_name="李四",
            comment="处理完成，等待验证"
        )
        assert task.status == TaskStatus.PENDING_VALIDATION
        
        # 7. 更新 Neo4j 状态
        tracker.update_task_status(task_id, "PENDING_VALIDATION")
        
        # 8. 验证通过（PENDING_VALIDATION -> RESOLVED）
        task.transition_to(
            TaskStatus.RESOLVED,
            operator_id="EMP-002",
            operator_name="王五",
            comment="验证通过，客户满意"
        )
        assert task.status == TaskStatus.RESOLVED
        assert task.resolved_at is not None
        
        # 9. 更新 Neo4j 状态
        tracker.update_task_status(task_id, "RESOLVED")
        
        # 10. 闭环（RESOLVED -> CLOSED）
        task.transition_to(
            TaskStatus.CLOSED,
            operator_id="EMP-002",
            operator_name="王五",
            comment="问题已闭环"
        )
        assert task.status == TaskStatus.CLOSED
        assert task.closed_at is not None
        
        # 11. 更新 Neo4j 状态
        tracker.update_task_status(task_id, "CLOSED")
        
        # 验证日志数量
        assert len(task.logs) >= 4
        
        # 验证 Neo4j 调用次数（至少创建 Issue、Task、Employee + 4 次状态更新 + 1 次日志）
        assert mock_neo4j_service.execute_query.call_count >= 5
    
    def test_workflow_with_rejection(self, tracker, mock_neo4j_service):
        """测试验证不通过重新处理的流程"""
        mock_neo4j_service.execute_query.return_value = [{"id": "TEST"}]
        
        # 创建任务
        task = Task(
            id="TASK-REJECT-001",
            title="验证不通过测试",
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM
        )
        
        # PENDING -> IN_PROGRESS
        task.transition_to(TaskStatus.IN_PROGRESS, operator_id="EMP-001", operator_name="张三")
        assert task.status == TaskStatus.IN_PROGRESS
        
        # IN_PROGRESS -> PENDING_VALIDATION
        task.transition_to(TaskStatus.PENDING_VALIDATION, comment="完成处理")
        assert task.status == TaskStatus.PENDING_VALIDATION
        
        # PENDING_VALIDATION -> IN_PROGRESS (验证不通过，重新处理)
        task.transition_to(
            TaskStatus.IN_PROGRESS,
            comment="验证不通过，需要补充材料",
            operator_id="EMP-002",
            operator_name="李四"
        )
        assert task.status == TaskStatus.IN_PROGRESS
        
        # 再次处理完成
        task.add_log(action="MATERIAL_ADDED", comment="已补充材料")
        
        # 再次提交验证
        task.transition_to(TaskStatus.PENDING_VALIDATION, comment="重新提交验证")
        assert task.status == TaskStatus.PENDING_VALIDATION
        
        # 验证通过
        task.transition_to(TaskStatus.RESOLVED, comment="验证通过")
        task.transition_to(TaskStatus.CLOSED, comment="闭环")
        
        assert task.status == TaskStatus.CLOSED
        # 验证有多次状态转换
        assert len(task.logs) >= 6
    
    def test_workflow_timeout_handling(self, tracker, mock_neo4j_service):
        """测试超时处理流程"""
        mock_neo4j_service.execute_query.return_value = [{"id": "TEST"}]
        
        # 创建紧急任务（2 小时超时）
        task = Task(
            id="TASK-TIMEOUT-001",
            title="超时测试",
            priority=TaskPriority.URGENT,
            status=TaskStatus.PENDING
        )
        
        # 分配任务，自动设置截止时间
        task.assign_to("EMP-001", "张三")
        assert task.due_date is not None
        
        # 模拟超时（手动设置过去时间）
        task.due_date = datetime.now() - timedelta(hours=1)
        
        # 检查是否超时
        assert task.is_overdue() is True
        assert task.get_remaining_time() == 0
        
        # 超时后状态转换到 TIMEOUT
        task.transition_to(TaskStatus.TIMEOUT, comment="任务超时")
        assert task.status == TaskStatus.TIMEOUT
        
        # 超时后可以重新开始
        task.transition_to(
            TaskStatus.IN_PROGRESS,
            operator_id="EMP-001",
            operator_name="张三",
            comment="重新开始处理"
        )
        assert task.status == TaskStatus.IN_PROGRESS
        
        # 继续正常流程（需要经过 PENDING_VALIDATION）
        task.transition_to(TaskStatus.PENDING_VALIDATION)
        task.transition_to(TaskStatus.RESOLVED)
        task.transition_to(TaskStatus.CLOSED)
        
        assert task.status == TaskStatus.CLOSED
    
    def test_workflow_cancellation(self, tracker, mock_neo4j_service):
        """测试任务取消流程"""
        mock_neo4j_service.execute_query.return_value = [{"id": "TEST"}]
        
        task = Task(
            id="TASK-CANCEL-001",
            title="取消测试",
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM
        )
        
        # PENDING -> CANCELLED
        task.transition_to(
            TaskStatus.CANCELLED,
            operator_id="EMP-001",
            operator_name="张三",
            comment="问题已解决，无需处理"
        )
        assert task.status == TaskStatus.CANCELLED
        
        # 终态不能转换
        with pytest.raises(TaskTransitionError):
            task.transition_to(TaskStatus.IN_PROGRESS)
        
        with pytest.raises(TaskTransitionError):
            task.transition_to(TaskStatus.CLOSED)
    
    def test_workflow_with_entity_relations(self, tracker, mock_neo4j_service):
        """测试带实体关联的工作流程"""
        mock_neo4j_service.execute_query.return_value = [{"id": "TEST"}]
        
        # 创建 Issue 和 Task
        issue_id, task_id = create_issue_and_task(
            title="产品质量问题",
            description="某批次产品存在缺陷",
            severity="HIGH",
            issue_type="QUALITY",
            assignee_id="EMP-001",
            assignee_name="张三",
            priority=TaskPriority.URGENT,
            related_entities={
                "product_id": "PROD-123",
                "batch_id": "BATCH-456"
            }
        )
        
        # 创建产品关联
        tracker.link_task_to_entity(
            task_id=task_id,
            entity_label="Product",
            entity_id="PROD-123",
            relation_type="AFFECTS"
        )
        
        # 创建批次关联
        tracker.link_task_to_entity(
            task_id=task_id,
            entity_label="Batch",
            entity_id="BATCH-456",
            relation_type="RELATED_TO"
        )
        
        # 验证 Neo4j 调用（创建 Issue+Task + 2 次关联）
        assert mock_neo4j_service.execute_query.call_count >= 2
        
        # 查询影响链
        mock_neo4j_service.execute_query.return_value = [
            {"related": {"id": "PROD-123"}, "relation_type": "AFFECTS"},
            {"related": {"id": "BATCH-456"}, "relation_type": "RELATED_TO"}
        ]
        
        impact = tracker.trace_task_impact(task_id)
        assert impact["task_id"] == task_id
        assert len(impact["related_entities"]) == 2
    
    def test_workflow_multiple_assignees(self, tracker, mock_neo4j_service):
        """测试多负责人协作流程"""
        mock_neo4j_service.execute_query.return_value = [{"id": "TEST"}]
        
        # 创建任务
        task = Task(
            id="TASK-MULTI-001",
            title="多部门协作",
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH
        )
        
        # 第一次分配
        task.assign_to("EMP-001", "张三", "zhangsan@example.com")
        assert task.assignee_id == "EMP-001"
        
        # 开始处理
        task.transition_to(TaskStatus.IN_PROGRESS, operator_id="EMP-001", operator_name="张三")
        
        # 需要其他部门协助，重新分配
        task.assign_to("EMP-002", "李四", "lisi@example.com", operator_id="EMP-001")
        assert task.assignee_id == "EMP-002"
        
        # 添加协作日志
        task.add_log(
            action="REASSIGN",
            comment="转交技术部处理",
            operator_id="EMP-001",
            operator_name="张三",
            metadata={"from": "EMP-001", "to": "EMP-002"}
        )
        
        # 继续处理
        task.transition_to(TaskStatus.PENDING_VALIDATION, operator_id="EMP-002", operator_name="李四")
        task.transition_to(TaskStatus.RESOLVED, operator_id="EMP-003", operator_name="王五")
        task.transition_to(TaskStatus.CLOSED)
        
        assert task.status == TaskStatus.CLOSED
        # 验证有多次分配日志
        assign_logs = [log for log in task.logs if log.action == "ASSIGN"]
        assert len(assign_logs) == 2


class TestIssueLifecycleEdgeCases:
    """测试边界情况"""
    
    def test_rapid_status_changes(self, tracker, mock_neo4j_service):
        """测试快速状态变更"""
        mock_neo4j_service.execute_query.return_value = [{"id": "TEST"}]
        
        task = Task(id="TASK-RAPID-001", title="快速变更测试")
        
        # 快速连续变更
        task.transition_to(TaskStatus.IN_PROGRESS)
        task.transition_to(TaskStatus.PENDING_VALIDATION)
        task.transition_to(TaskStatus.RESOLVED)
        task.transition_to(TaskStatus.CLOSED)
        
        assert task.status == TaskStatus.CLOSED
        assert len(task.logs) == 4
    
    def test_concurrent_updates(self, tracker, mock_neo4j_service):
        """测试并发更新（模拟）"""
        mock_neo4j_service.execute_query.return_value = [{"id": "TEST"}]
        
        task = Task(id="TASK-CONCURRENT-001", title="并发测试")
        
        # 第一次更新
        task.transition_to(TaskStatus.IN_PROGRESS, operator_id="EMP-001")
        first_updated_at = task.updated_at
        
        # 模拟时间流逝
        import time
        time.sleep(0.01)
        
        # 第二次更新
        task.transition_to(TaskStatus.PENDING_VALIDATION, operator_id="EMP-002")
        second_updated_at = task.updated_at
        
        # 验证更新时间递增
        assert second_updated_at > first_updated_at
    
    def test_large_log_history(self, tracker, mock_neo4j_service):
        """测试大量日志"""
        mock_neo4j_service.execute_query.return_value = [{"id": "TEST"}]
        
        task = Task(id="TASK-LARGE-001", title="大量日志测试")
        
        # 添加 100 条日志
        for i in range(100):
            task.add_log(
                action=f"ACTION_{i}",
                comment=f"日志 {i}",
                operator_id=f"EMP-{i % 10}"
            )
        
        assert len(task.logs) == 100
        assert task.logs[0].comment == "日志 0"
        assert task.logs[99].comment == "日志 99"


class TestIssueLifecycleStatistics:
    """测试统计功能"""
    
    def test_resolution_time_calculation(self, tracker, mock_neo4j_service):
        """测试解决时长计算"""
        mock_neo4j_service.execute_query.return_value = [{"id": "TEST"}]
        
        task = Task(id="TASK-TIME-001", title="时长测试")
        
        # 记录开始时间
        start_time = datetime.now()
        
        task.transition_to(TaskStatus.IN_PROGRESS)
        task.transition_to(TaskStatus.PENDING_VALIDATION)
        task.transition_to(TaskStatus.RESOLVED)
        
        # 计算解决时长
        resolution_time = task.resolved_at - start_time
        assert resolution_time.total_seconds() >= 0
        
        task.transition_to(TaskStatus.CLOSED)
        total_time = task.closed_at - start_time
        assert total_time >= resolution_time
    
    def test_status_distribution(self, tracker, mock_neo4j_service):
        """测试状态分布统计"""
        mock_stats = {
            "total": 100,
            "pending": 20,
            "in_progress": 30,
            "pending_validation": 10,
            "resolved": 25,
            "closed": 10,
            "timeout": 3,
            "cancelled": 2
        }
        mock_neo4j_service.execute_query.return_value = [mock_stats]
        
        stats = tracker.get_task_statistics()
        
        assert stats["total"] == 100
        assert stats["pending"] == 20
        assert stats["in_progress"] == 30


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
