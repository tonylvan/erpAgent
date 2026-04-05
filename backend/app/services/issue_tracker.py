"""问题追踪服务 - 实现 Neo4j 关系管理"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime, timedelta
import logging
import uuid

from app.models.task import Task, TaskStatus, TaskPriority, TaskLog
from app.services.neo4j_service import get_neo4j_service, execute_neo4j_query

logger = logging.getLogger(__name__)


class IssueTracker:
    """问题追踪服务类 - 基于 Neo4j 的关系管理"""
    
    def __init__(self):
        """初始化问题追踪服务"""
        self.neo4j = get_neo4j_service()
    
    # ==================== Issue 节点管理 ====================
    
    def create_issue(self, issue_id: str, title: str, description: Optional[str] = None,
                     severity: str = "MEDIUM", issue_type: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        创建 Issue 节点
        
        Args:
            issue_id: Issue ID
            title: 标题
            description: 描述
            severity: 严重程度 (LOW/MEDIUM/HIGH/CRITICAL)
            issue_type: 问题类型
            metadata: 附加元数据
            
        Returns:
            bool: 创建成功返回 True
        """
        cypher = """
        CREATE (issue:Issue {
            id: $issue_id,
            title: $title,
            description: $description,
            severity: $severity,
            issue_type: $issue_type,
            status: 'OPEN',
            created_at: datetime($created_at),
            updated_at: datetime($updated_at),
            metadata: $metadata
        })
        RETURN issue.id as id
        """
        
        params = {
            "issue_id": issue_id,
            "title": title,
            "description": description,
            "severity": severity,
            "issue_type": issue_type,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        
        result = self.neo4j.execute_query(cypher, params)
        return len(result) > 0
    
    def get_issue(self, issue_id: str) -> Optional[Dict[str, Any]]:
        """
        获取 Issue 详情
        
        Args:
            issue_id: Issue ID
            
        Returns:
            Optional[Dict]: Issue 信息
        """
        cypher = """
        MATCH (issue:Issue {id: $issue_id})
        RETURN issue
        """
        
        result = self.neo4j.execute_query(cypher, {"issue_id": issue_id})
        if result and len(result) > 0:
            return result[0].get('issue', {})
        return None
    
    def update_issue_status(self, issue_id: str, status: str) -> bool:
        """
        更新 Issue 状态
        
        Args:
            issue_id: Issue ID
            status: 新状态
            
        Returns:
            bool: 更新成功返回 True
        """
        cypher = """
        MATCH (issue:Issue {id: $issue_id})
        SET issue.status = $status,
            issue.updated_at = datetime($updated_at)
        RETURN issue.id as id
        """
        
        result = self.neo4j.execute_query(cypher, {
            "issue_id": issue_id,
            "status": status,
            "updated_at": datetime.now().isoformat()
        })
        return len(result) > 0
    
    # ==================== Task 节点管理 ====================
    
    def create_task_node(self, task: Task) -> bool:
        """
        在 Neo4j 中创建 Task 节点
        
        Args:
            task: Task 对象
            
        Returns:
            bool: 创建成功返回 True
        """
        cypher = """
        CREATE (task:Task {
            id: $id,
            title: $title,
            description: $description,
            status: $status,
            priority: $priority,
            assignee_id: $assignee_id,
            assignee_name: $assignee_name,
            assignee_email: $assignee_email,
            alert_id: $alert_id,
            issue_type: $issue_type,
            related_entities: $related_entities,
            created_at: datetime($created_at),
            updated_at: datetime($updated_at),
            due_date: $due_date,
            started_at: $started_at,
            resolved_at: $resolved_at,
            closed_at: $closed_at
        })
        RETURN task.id as id
        """
        
        params = {
            "id": task.id,
            "title": task.title,
            "description": task.description,
            "status": task.status.value if hasattr(task.status, 'value') else str(task.status),
            "priority": task.priority.value if hasattr(task.priority, 'value') else str(task.priority),
            "assignee_id": task.assignee_id,
            "assignee_name": task.assignee_name,
            "assignee_email": task.assignee_email,
            "alert_id": task.alert_id,
            "issue_type": task.issue_type,
            "related_entities": task.related_entities or {},
            "created_at": task.created_at.isoformat(),
            "updated_at": task.updated_at.isoformat(),
            "due_date": task.due_date.isoformat() if task.due_date else None,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "resolved_at": task.resolved_at.isoformat() if task.resolved_at else None,
            "closed_at": task.closed_at.isoformat() if task.closed_at else None
        }
        
        result = self.neo4j.execute_query(cypher, params)
        return len(result) > 0
    
    def get_task_node(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        获取 Task 节点
        
        Args:
            task_id: Task ID
            
        Returns:
            Optional[Dict]: Task 信息
        """
        cypher = """
        MATCH (task:Task {id: $task_id})
        RETURN task
        """
        
        result = self.neo4j.execute_query(cypher, {"task_id": task_id})
        if result and len(result) > 0:
            return result[0].get('task', {})
        return None
    
    def update_task_status(self, task_id: str, status: str) -> bool:
        """
        更新 Task 状态
        
        Args:
            task_id: Task ID
            status: 新状态
            
        Returns:
            bool: 更新成功返回 True
        """
        cypher = """
        MATCH (task:Task {id: $task_id})
        SET task.status = $status,
            task.updated_at = datetime($updated_at)
        RETURN task.id as id
        """
        
        result = self.neo4j.execute_query(cypher, {
            "task_id": task_id,
            "status": status,
            "updated_at": datetime.now().isoformat()
        })
        return len(result) > 0
    
    # ==================== Employee 节点管理 ====================
    
    def get_or_create_employee(self, employee_id: str, name: str, 
                                email: Optional[str] = None,
                                department: Optional[str] = None) -> bool:
        """
        获取或创建 Employee 节点
        
        Args:
            employee_id: 员工 ID
            name: 姓名
            email: 邮箱
            department: 部门
            
        Returns:
            bool: 操作成功返回 True
        """
        cypher = """
        MERGE (emp:Employee {id: $employee_id})
        SET emp.name = $name,
            emp.email = $email,
            emp.department = $department,
            emp.updated_at = datetime($updated_at)
        RETURN emp.id as id
        """
        
        result = self.neo4j.execute_query(cypher, {
            "employee_id": employee_id,
            "name": name,
            "email": email,
            "department": department,
            "updated_at": datetime.now().isoformat()
        })
        return len(result) > 0
    
    # ==================== 关系管理 ====================
    
    def assign_task_to_employee(self, task_id: str, employee_id: str, 
                                 assigned_at: Optional[datetime] = None) -> bool:
        """
        创建 Task 到 Employee 的分配关系
        
        Args:
            task_id: Task ID
            employee_id: Employee ID
            assigned_at: 分配时间
            
        Returns:
            bool: 创建成功返回 True
        """
        cypher = """
        MATCH (task:Task {id: $task_id})
        MATCH (emp:Employee {id: $employee_id})
        MERGE (task)-[r:ASSIGNED_TO]->(emp)
        SET r.assigned_at = datetime($assigned_at),
            r.updated_at = datetime($updated_at)
        RETURN r
        """
        
        result = self.neo4j.execute_query(cypher, {
            "task_id": task_id,
            "employee_id": employee_id,
            "assigned_at": (assigned_at or datetime.now()).isoformat(),
            "updated_at": datetime.now().isoformat()
        })
        return len(result) > 0
    
    def link_task_to_issue(self, task_id: str, issue_id: str, 
                           link_type: str = "RELATED_TO") -> bool:
        """
        创建 Task 到 Issue 的关联关系
        
        Args:
            task_id: Task ID
            issue_id: Issue ID
            link_type: 关系类型
            
        Returns:
            bool: 创建成功返回 True
        """
        cypher = """
        MATCH (task:Task {id: $task_id})
        MATCH (issue:Issue {id: $issue_id})
        MERGE (task)-[r:`""" + link_type + """`]->(issue)
        SET r.created_at = datetime($created_at)
        RETURN r
        """
        
        result = self.neo4j.execute_query(cypher, {
            "task_id": task_id,
            "issue_id": issue_id,
            "created_at": datetime.now().isoformat()
        })
        return len(result) > 0
    
    def link_task_to_entity(self, task_id: str, entity_label: str, 
                            entity_id: str, relation_type: str = "RELATED_TO") -> bool:
        """
        创建 Task 到业务实体的关联关系
        
        Args:
            task_id: Task ID
            entity_label: 实体标签 (Product/Customer/Supplier 等)
            entity_id: 实体 ID
            relation_type: 关系类型
            
        Returns:
            bool: 创建成功返回 True
        """
        cypher = f"""
        MATCH (task:Task {{id: $task_id}})
        MATCH (entity:{entity_label} {{id: $entity_id}})
        MERGE (task)-[r:`{relation_type}`]->(entity)
        SET r.created_at = datetime($created_at)
        RETURN r
        """
        
        result = self.neo4j.execute_query(cypher, {
            "task_id": task_id,
            "entity_id": entity_id,
            "created_at": datetime.now().isoformat()
        })
        return len(result) > 0
    
    def create_task_dependency(self, from_task_id: str, to_task_id: str,
                               dependency_type: str = "DEPENDS_ON") -> bool:
        """
        创建 Task 之间的依赖关系
        
        Args:
            from_task_id: 源 Task ID
            to_task_id: 目标 Task ID
            dependency_type: 依赖类型
            
        Returns:
            bool: 创建成功返回 True
        """
        cypher = f"""
        MATCH (from:Task {{id: $from_task_id}})
        MATCH (to:Task {{id: $to_task_id}})
        MERGE (from)-[r:`{dependency_type}`]->(to)
        SET r.created_at = datetime($created_at)
        RETURN r
        """
        
        result = self.neo4j.execute_query(cypher, {
            "from_task_id": from_task_id,
            "to_task_id": to_task_id,
            "created_at": datetime.now().isoformat()
        })
        return len(result) > 0
    
    # ==================== 日志管理 ====================
    
    def add_task_log(self, task_id: str, log: TaskLog) -> bool:
        """
        添加 Task 日志
        
        Args:
            task_id: Task ID
            log: TaskLog 对象
            
        Returns:
            bool: 添加成功返回 True
        """
        cypher = """
        MATCH (task:Task {id: $task_id})
        CREATE (log:LogEntry {
            id: $log_id,
            task_id: $task_id,
            action: $action,
            from_status: $from_status,
            to_status: $to_status,
            operator_id: $operator_id,
            operator_name: $operator_name,
            comment: $comment,
            created_at: datetime($created_at),
            metadata: $metadata
        })
        CREATE (task)-[:HAS_LOG]->(log)
        RETURN log.id as id
        """
        
        params = {
            "task_id": task_id,
            "log_id": str(uuid.uuid4()),
            "action": log.action,
            "from_status": log.from_status,
            "to_status": log.to_status,
            "operator_id": log.operator_id,
            "operator_name": log.operator_name,
            "comment": log.comment,
            "created_at": log.created_at.isoformat(),
            "metadata": log.metadata or {}
        }
        
        result = self.neo4j.execute_query(cypher, params)
        return len(result) > 0
    
    def get_task_logs(self, task_id: str) -> List[Dict[str, Any]]:
        """
        获取 Task 日志列表
        
        Args:
            task_id: Task ID
            
        Returns:
            List[Dict]: 日志列表
        """
        cypher = """
        MATCH (task:Task {id: $task_id})-[:HAS_LOG]->(log:LogEntry)
        RETURN log
        ORDER BY log.created_at ASC
        """
        
        result = self.neo4j.execute_query(cypher, {"task_id": task_id})
        return [record.get('log', {}) for record in result]
    
    # ==================== 查询统计 ====================
    
    def get_employee_tasks(self, employee_id: str, 
                           status: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        获取员工的任务列表
        
        Args:
            employee_id: 员工 ID
            status: 状态筛选（可选）
            
        Returns:
            List[Dict]: 任务列表
        """
        if status:
            cypher = """
            MATCH (task:Task {status: $status})-[:ASSIGNED_TO]->(emp:Employee {id: $employee_id})
            RETURN task
            ORDER BY task.created_at DESC
            """
            params = {"employee_id": employee_id, "status": status}
        else:
            cypher = """
            MATCH (task:Task)-[:ASSIGNED_TO]->(emp:Employee {id: $employee_id})
            RETURN task
            ORDER BY task.created_at DESC
            """
            params = {"employee_id": employee_id}
        
        result = self.neo4j.execute_query(cypher, params)
        return [record.get('task', {}) for record in result]
    
    def get_overdue_tasks(self) -> List[Dict[str, Any]]:
        """
        获取超时的任务列表
        
        Returns:
            List[Dict]: 超时任务列表
        """
        cypher = """
        MATCH (task:Task)
        WHERE task.due_date IS NOT NULL 
          AND task.due_date < datetime()
          AND NOT task.status IN ['RESOLVED', 'CLOSED', 'CANCELLED']
        RETURN task
        ORDER BY task.due_date ASC
        """
        
        result = self.neo4j.execute_query(cypher)
        return [record.get('task', {}) for record in result]
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """
        获取任务统计信息
        
        Returns:
            Dict: 统计信息
        """
        cypher = """
        MATCH (task:Task)
        RETURN 
            count(task) as total,
            sum(CASE WHEN task.status = 'PENDING' THEN 1 ELSE 0 END) as pending,
            sum(CASE WHEN task.status = 'IN_PROGRESS' THEN 1 ELSE 0 END) as in_progress,
            sum(CASE WHEN task.status = 'PENDING_VALIDATION' THEN 1 ELSE 0 END) as pending_validation,
            sum(CASE WHEN task.status = 'RESOLVED' THEN 1 ELSE 0 END) as resolved,
            sum(CASE WHEN task.status = 'CLOSED' THEN 1 ELSE 0 END) as closed,
            sum(CASE WHEN task.status = 'TIMEOUT' THEN 1 ELSE 0 END) as timeout,
            sum(CASE WHEN task.status = 'CANCELLED' THEN 1 ELSE 0 END) as cancelled
        """
        
        result = self.neo4j.execute_query(cypher)
        if result and len(result) > 0:
            return result[0]
        return {}
    
    def get_issue_related_tasks(self, issue_id: str) -> List[Dict[str, Any]]:
        """
        获取与 Issue 关联的所有任务
        
        Args:
            issue_id: Issue ID
            
        Returns:
            List[Dict]: 任务列表
        """
        cypher = """
        MATCH (issue:Issue {id: $issue_id})<-[:RELATED_TO]-(task:Task)
        RETURN task
        ORDER BY task.created_at DESC
        """
        
        result = self.neo4j.execute_query(cypher, {"issue_id": issue_id})
        return [record.get('task', {}) for record in result]
    
    def trace_task_impact(self, task_id: str) -> Dict[str, Any]:
        """
        追踪任务的影响链（关联的实体）
        
        Args:
            task_id: Task ID
            
        Returns:
            Dict: 影响链信息
        """
        cypher = """
        MATCH (task:Task {id: $task_id})-[r]-(related)
        WHERE NOT related:Task AND NOT related:Employee AND NOT related:LogEntry
        RETURN related, type(r) as relation_type
        """
        
        result = self.neo4j.execute_query(cypher, {"task_id": task_id})
        return {
            "task_id": task_id,
            "related_entities": [
                {
                    "entity": record.get('related', {}),
                    "relation": record.get('relation_type', '')
                }
                for record in result
            ]
        }


# 全局服务实例
_issue_tracker: Optional[IssueTracker] = None


def get_issue_tracker() -> IssueTracker:
    """获取 IssueTracker 服务实例"""
    global _issue_tracker
    
    if _issue_tracker is None:
        _issue_tracker = IssueTracker()
    
    return _issue_tracker


def create_issue_and_task(title: str, description: Optional[str] = None,
                          severity: str = "MEDIUM", issue_type: Optional[str] = None,
                          assignee_id: Optional[str] = None,
                          assignee_name: Optional[str] = None,
                          priority: TaskPriority = TaskPriority.MEDIUM,
                          related_entities: Optional[Dict[str, str]] = None) -> Tuple[str, str]:
    """
    便捷函数：创建 Issue 并关联 Task
    
    Args:
        title: 标题
        description: 描述
        severity: 严重程度
        issue_type: 问题类型
        assignee_id: 负责人 ID
        assignee_name: 负责人姓名
        priority: 优先级
        related_entities: 关联实体
        
    Returns:
        Tuple[str, str]: (issue_id, task_id)
    """
    tracker = get_issue_tracker()
    
    # 生成 ID
    issue_id = f"ISSUE-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    task_id = f"TASK-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    # 创建 Issue
    tracker.create_issue(
        issue_id=issue_id,
        title=title,
        description=description,
        severity=severity,
        issue_type=issue_type
    )
    
    # 创建 Task
    task = Task(
        id=task_id,
        title=title,
        description=description,
        status=TaskStatus.PENDING,
        priority=priority,
        issue_type=issue_type,
        alert_id=issue_id,
        related_entities=related_entities or {}
    )
    
    # 分配负责人
    if assignee_id and assignee_name:
        task.assign_to(assignee_id, assignee_name)
        # 创建或更新 Employee 节点
        tracker.get_or_create_employee(assignee_id, assignee_name, assignee_name)
    
    # 在 Neo4j 中创建 Task 节点
    tracker.create_task_node(task)
    
    # 创建关联关系
    tracker.link_task_to_issue(task_id, issue_id)
    
    # 分配任务给员工
    if assignee_id:
        tracker.assign_task_to_employee(task_id, assignee_id)
    
    return issue_id, task_id
