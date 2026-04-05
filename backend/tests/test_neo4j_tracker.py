"""Neo4j 问题追踪服务测试"""

import pytest
import uuid
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from app.services.issue_tracker import IssueTracker, get_issue_tracker, create_issue_and_task
from app.models.task import Task, TaskStatus, TaskPriority, TaskLog


@pytest.fixture
def mock_neo4j_service():
    """模拟 Neo4j 服务"""
    mock_service = Mock()
    mock_service.execute_query = Mock(return_value=[])
    return mock_service


@pytest.fixture
def tracker(mock_neo4j_service):
    """创建 IssueTracker 实例（使用模拟的 Neo4j 服务）"""
    with patch('app.services.issue_tracker.get_neo4j_service', return_value=mock_neo4j_service):
        tracker = IssueTracker()
        yield tracker


class TestIssueManagement:
    """测试 Issue 节点管理"""
    
    def test_create_issue(self, tracker, mock_neo4j_service):
        """测试创建 Issue"""
        mock_neo4j_service.execute_query.return_value = [{"id": "ISSUE-001"}]
        
        result = tracker.create_issue(
            issue_id="ISSUE-001",
            title="测试问题",
            description="这是一个测试问题",
            severity="HIGH",
            issue_type="BUG"
        )
        
        assert result is True
        mock_neo4j_service.execute_query.assert_called_once()
        
        # 验证调用参数
        call_args = mock_neo4j_service.execute_query.call_args
        cypher = call_args[0][0]
        params = call_args[0][1]
        
        assert "CREATE (issue:Issue" in cypher
        assert params["issue_id"] == "ISSUE-001"
        assert params["title"] == "测试问题"
        assert params["severity"] == "HIGH"
    
    def test_get_issue_success(self, tracker, mock_neo4j_service):
        """测试获取 Issue 成功"""
        mock_issue = {
            "id": "ISSUE-001",
            "title": "测试问题",
            "status": "OPEN"
        }
        mock_neo4j_service.execute_query.return_value = [{"issue": mock_issue}]
        
        result = tracker.get_issue("ISSUE-001")
        
        assert result is not None
        assert result["id"] == "ISSUE-001"
        assert result["title"] == "测试问题"
    
    def test_get_issue_not_found(self, tracker, mock_neo4j_service):
        """测试获取 Issue 不存在"""
        mock_neo4j_service.execute_query.return_value = []
        
        result = tracker.get_issue("ISSUE-NOTFOUND")
        
        assert result is None
    
    def test_update_issue_status(self, tracker, mock_neo4j_service):
        """测试更新 Issue 状态"""
        mock_neo4j_service.execute_query.return_value = [{"id": "ISSUE-001"}]
        
        result = tracker.update_issue_status("ISSUE-001", "IN_PROGRESS")
        
        assert result is True
        mock_neo4j_service.execute_query.assert_called_once()
        
        call_args = mock_neo4j_service.execute_query.call_args
        params = call_args[0][1]
        assert params["status"] == "IN_PROGRESS"


class TestTaskNodeManagement:
    """测试 Task 节点管理"""
    
    def test_create_task_node(self, tracker, mock_neo4j_service):
        """测试创建 Task 节点"""
        mock_neo4j_service.execute_query.return_value = [{"id": "TASK-001"}]
        
        task = Task(
            id="TASK-001",
            title="测试任务",
            description="测试描述",
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH,
            assignee_id="EMP-123",
            assignee_name="张三"
        )
        
        result = tracker.create_task_node(task)
        
        assert result is True
        mock_neo4j_service.execute_query.assert_called_once()
        
        call_args = mock_neo4j_service.execute_query.call_args
        cypher = call_args[0][0]
        assert "CREATE (task:Task" in cypher
    
    def test_get_task_node_success(self, tracker, mock_neo4j_service):
        """测试获取 Task 节点成功"""
        mock_task = {
            "id": "TASK-001",
            "title": "测试任务",
            "status": "PENDING"
        }
        mock_neo4j_service.execute_query.return_value = [{"task": mock_task}]
        
        result = tracker.get_task_node("TASK-001")
        
        assert result is not None
        assert result["id"] == "TASK-001"
    
    def test_get_task_node_not_found(self, tracker, mock_neo4j_service):
        """测试获取 Task 节点不存在"""
        mock_neo4j_service.execute_query.return_value = []
        
        result = tracker.get_task_node("TASK-NOTFOUND")
        
        assert result is None
    
    def test_update_task_status(self, tracker, mock_neo4j_service):
        """测试更新 Task 状态"""
        mock_neo4j_service.execute_query.return_value = [{"id": "TASK-001"}]
        
        result = tracker.update_task_status("TASK-001", "IN_PROGRESS")
        
        assert result is True


class TestEmployeeManagement:
    """测试 Employee 节点管理"""
    
    def test_get_or_create_employee(self, tracker, mock_neo4j_service):
        """测试获取或创建 Employee"""
        mock_neo4j_service.execute_query.return_value = [{"id": "EMP-123"}]
        
        result = tracker.get_or_create_employee(
            employee_id="EMP-123",
            name="张三",
            email="zhangsan@example.com",
            department="技术部"
        )
        
        assert result is True
        mock_neo4j_service.execute_query.assert_called_once()


class TestRelationshipManagement:
    """测试关系管理"""
    
    def test_assign_task_to_employee(self, tracker, mock_neo4j_service):
        """测试分配任务给员工"""
        mock_neo4j_service.execute_query.return_value = [{}]
        
        result = tracker.assign_task_to_employee("TASK-001", "EMP-123")
        
        assert result is True
        
        call_args = mock_neo4j_service.execute_query.call_args
        cypher = call_args[0][0]
        assert "ASSIGNED_TO" in cypher
    
    def test_link_task_to_issue(self, tracker, mock_neo4j_service):
        """测试关联 Task 到 Issue"""
        mock_neo4j_service.execute_query.return_value = [{}]
        
        result = tracker.link_task_to_issue("TASK-001", "ISSUE-001")
        
        assert result is True
        
        call_args = mock_neo4j_service.execute_query.call_args
        cypher = call_args[0][0]
        assert "RELATED_TO" in cypher
    
    def test_link_task_to_entity_product(self, tracker, mock_neo4j_service):
        """测试关联 Task 到产品实体"""
        mock_neo4j_service.execute_query.return_value = [{}]
        
        result = tracker.link_task_to_entity(
            task_id="TASK-001",
            entity_label="Product",
            entity_id="PROD-456",
            relation_type="AFFECTS"
        )
        
        assert result is True
        
        call_args = mock_neo4j_service.execute_query.call_args
        cypher = call_args[0][0]
        assert "Product" in cypher
        assert "AFFECTS" in cypher
    
    def test_create_task_dependency(self, tracker, mock_neo4j_service):
        """测试创建 Task 依赖关系"""
        mock_neo4j_service.execute_query.return_value = [{}]
        
        result = tracker.create_task_dependency("TASK-001", "TASK-002")
        
        assert result is True
        
        call_args = mock_neo4j_service.execute_query.call_args
        cypher = call_args[0][0]
        assert "DEPENDS_ON" in cypher


class TestLogManagement:
    """测试日志管理"""
    
    def test_add_task_log(self, tracker, mock_neo4j_service):
        """测试添加 Task 日志"""
        mock_neo4j_service.execute_query.return_value = [{"id": "LOG-001"}]
        
        log = TaskLog(
            task_id="TASK-001",
            action="STATUS_CHANGE",
            from_status="PENDING",
            to_status="IN_PROGRESS",
            operator_id="EMP-123",
            operator_name="张三",
            comment="开始处理"
        )
        
        result = tracker.add_task_log("TASK-001", log)
        
        assert result is True
        
        call_args = mock_neo4j_service.execute_query.call_args
        cypher = call_args[0][0]
        assert "CREATE (log:LogEntry" in cypher
        assert "HAS_LOG" in cypher
    
    def test_get_task_logs(self, tracker, mock_neo4j_service):
        """测试获取 Task 日志列表"""
        mock_logs = [
            {"log": {"id": "LOG-001", "action": "STATUS_CHANGE"}},
            {"log": {"id": "LOG-002", "action": "COMMENT"}}
        ]
        mock_neo4j_service.execute_query.return_value = mock_logs
        
        result = tracker.get_task_logs("TASK-001")
        
        assert len(result) == 2
        assert result[0]["id"] == "LOG-001"
        assert result[1]["id"] == "LOG-002"


class TestQueryStatistics:
    """测试查询统计"""
    
    def test_get_employee_tasks(self, tracker, mock_neo4j_service):
        """测试获取员工任务列表"""
        mock_tasks = [
            {"task": {"id": "TASK-001", "title": "任务 1"}},
            {"task": {"id": "TASK-002", "title": "任务 2"}}
        ]
        mock_neo4j_service.execute_query.return_value = mock_tasks
        
        result = tracker.get_employee_tasks("EMP-123")
        
        assert len(result) == 2
        assert result[0]["id"] == "TASK-001"
    
    def test_get_employee_tasks_with_status(self, tracker, mock_neo4j_service):
        """测试按状态获取员工任务"""
        mock_neo4j_service.execute_query.return_value = [
            {"task": {"id": "TASK-001"}}
        ]
        
        result = tracker.get_employee_tasks("EMP-123", status="IN_PROGRESS")
        
        assert len(result) == 1
        
        call_args = mock_neo4j_service.execute_query.call_args
        params = call_args[0][1]
        assert params["status"] == "IN_PROGRESS"
    
    def test_get_overdue_tasks(self, tracker, mock_neo4j_service):
        """测试获取超时任务"""
        mock_tasks = [
            {"task": {"id": "TASK-001", "title": "超时任务 1"}},
            {"task": {"id": "TASK-002", "title": "超时任务 2"}}
        ]
        mock_neo4j_service.execute_query.return_value = mock_tasks
        
        result = tracker.get_overdue_tasks()
        
        assert len(result) == 2
    
    def test_get_task_statistics(self, tracker, mock_neo4j_service):
        """测试获取任务统计"""
        mock_stats = {
            "total": 100,
            "pending": 20,
            "in_progress": 30,
            "resolved": 40,
            "closed": 10
        }
        mock_neo4j_service.execute_query.return_value = [mock_stats]
        
        result = tracker.get_task_statistics()
        
        assert result["total"] == 100
        assert result["pending"] == 20
        assert result["in_progress"] == 30
    
    def test_get_issue_related_tasks(self, tracker, mock_neo4j_service):
        """测试获取 Issue 关联的任务"""
        mock_tasks = [
            {"task": {"id": "TASK-001"}},
            {"task": {"id": "TASK-002"}}
        ]
        mock_neo4j_service.execute_query.return_value = mock_tasks
        
        result = tracker.get_issue_related_tasks("ISSUE-001")
        
        assert len(result) == 2
    
    def test_trace_task_impact(self, tracker, mock_neo4j_service):
        """测试追踪任务影响链"""
        mock_impact = [
            {
                "related": {"id": "PROD-001", "name": "产品 A"},
                "relation_type": "AFFECTS"
            },
            {
                "related": {"id": "CUST-001", "name": "客户 B"},
                "relation_type": "IMPACTS"
            }
        ]
        mock_neo4j_service.execute_query.return_value = mock_impact
        
        result = tracker.trace_task_impact("TASK-001")
        
        assert result["task_id"] == "TASK-001"
        assert len(result["related_entities"]) == 2


class TestConvenienceFunctions:
    """测试便捷函数"""
    
    def test_create_issue_and_task(self, mock_neo4j_service):
        """测试创建 Issue 并关联 Task"""
        with patch('app.services.issue_tracker.get_neo4j_service', return_value=mock_neo4j_service):
            mock_neo4j_service.execute_query.return_value = [{"id": "TEST"}]
            
            issue_id, task_id = create_issue_and_task(
                title="测试问题",
                description="测试描述",
                severity="HIGH",
                issue_type="BUG",
                assignee_id="EMP-123",
                assignee_name="张三",
                priority=TaskPriority.HIGH
            )
            
            assert issue_id.startswith("ISSUE-")
            assert task_id.startswith("TASK-")
            assert mock_neo4j_service.execute_query.call_count >= 3  # 至少 3 次调用


class TestIssueTrackerIntegration:
    """测试 IssueTracker 集成场景"""
    
    def test_full_workflow_with_mocks(self, tracker, mock_neo4j_service):
        """测试完整工作流程（使用模拟）"""
        # 1. 创建 Employee
        mock_neo4j_service.execute_query.return_value = [{"id": "EMP-123"}]
        tracker.get_or_create_employee("EMP-123", "张三", "zhangsan@example.com")
        
        # 2. 创建 Issue
        mock_neo4j_service.execute_query.return_value = [{"id": "ISSUE-001"}]
        tracker.create_issue("ISSUE-001", "测试问题", "详细描述", "HIGH")
        
        # 3. 创建 Task
        mock_neo4j_service.execute_query.return_value = [{"id": "TASK-001"}]
        task = Task(
            id="TASK-001",
            title="处理测试问题",
            status=TaskStatus.PENDING,
            assignee_id="EMP-123",
            assignee_name="张三"
        )
        tracker.create_task_node(task)
        
        # 4. 创建关系
        mock_neo4j_service.execute_query.return_value = [{}]
        tracker.link_task_to_issue("TASK-001", "ISSUE-001")
        tracker.assign_task_to_employee("TASK-001", "EMP-123")
        
        # 5. 添加日志
        mock_neo4j_service.execute_query.return_value = [{"id": "LOG-001"}]
        log = TaskLog(
            task_id="TASK-001",
            action="CREATE",
            comment="工单创建"
        )
        tracker.add_task_log("TASK-001", log)
        
        # 验证调用次数
        assert mock_neo4j_service.execute_query.call_count >= 6
    
    def test_error_handling(self, tracker, mock_neo4j_service):
        """测试错误处理"""
        mock_neo4j_service.execute_query.side_effect = Exception("Neo4j 连接失败")
        
        # 应该抛出异常
        with pytest.raises(Exception, match="Neo4j"):
            tracker.create_issue("ISSUE-ERR", "测试")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
