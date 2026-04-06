"""工单工作流服务 - 实现分配、转派、升级、解决、关闭等操作"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any, List
import logging
from app.models.task import Task, TaskStatus, TaskPriority, TaskLog, TaskStatusMachine, TaskTransitionError
from app.models.ticket_comment import TicketComment
import uuid

logger = logging.getLogger(__name__)


class WorkflowAction(str, Enum):
    """工作流操作类型"""
    ASSIGN = "ASSIGN"
    TRANSFER = "TRANSFER"
    ESCALATE = "ESCALATE"
    RESOLVE = "RESOLVE"
    CLOSE = "CLOSE"
    STATUS_CHANGE = "STATUS_CHANGE"
    COMMENT = "COMMENT"


class TicketWorkflowService:
    """工单工作流服务"""
    
    def __init__(self, db_session=None):
        """
        初始化工作流服务
        
        Args:
            db_session: 数据库会话（用于持久化）
        """
        self.db = db_session
    
    def assign_ticket(
        self, 
        ticket: Task, 
        assignee_id: str, 
        assignee_name: str,
        assignee_email: Optional[str] = None,
        operator_id: Optional[str] = None,
        operator_name: Optional[str] = None,
        comment: Optional[str] = None
    ) -> Task:
        """
        分配工单
        
        Args:
            ticket: 工单对象
            assignee_id: 负责人 ID
            assignee_name: 负责人姓名
            assignee_email: 负责人邮箱
            operator_id: 操作人 ID
            operator_name: 操作人姓名
            comment: 备注说明
            
        Returns:
            Task: 更新后的工单
        """
        old_assignee = ticket.assignee_id
        
        # 执行分配
        ticket.assign_to(
            assignee_id=assignee_id,
            assignee_name=assignee_name,
            assignee_email=assignee_email,
            operator_id=operator_id
        )
        
        # 如果工单处于待处理状态，自动转换为处理中
        if ticket.status == TaskStatus.PENDING:
            ticket.transition_to(
                new_status=TaskStatus.IN_PROGRESS,
                operator_id=operator_id,
                operator_name=operator_name,
                comment=comment or "工单已分配，开始处理"
            )
        else:
            # 添加日志
            ticket.add_log(
                action=WorkflowAction.ASSIGN,
                comment=comment or f"分配给 {assignee_name}",
                operator_id=operator_id,
                operator_name=operator_name,
                metadata={
                    "old_assignee": old_assignee,
                    "new_assignee": assignee_id
                }
            )
        
        logger.info(f"工单分配：{ticket.id} -> {assignee_name} (操作人：{operator_name})")
        return ticket
    
    def transfer_ticket(
        self,
        ticket: Task,
        new_assignee_id: str,
        new_assignee_name: str,
        new_assignee_email: Optional[str] = None,
        operator_id: Optional[str] = None,
        operator_name: Optional[str] = None,
        comment: Optional[str] = None
    ) -> Task:
        """
        转派工单（给其他人）
        
        Args:
            ticket: 工单对象
            new_assignee_id: 新负责人 ID
            new_assignee_name: 新负责人姓名
            new_assignee_email: 新负责人邮箱
            operator_id: 操作人 ID
            operator_name: 操作人姓名
            comment: 转派原因
            
        Returns:
            Task: 更新后的工单
        """
        old_assignee = ticket.assignee_id
        
        if old_assignee == new_assignee_id:
            raise ValueError("不能转派给当前负责人")
        
        # 执行转派
        ticket.assign_to(
            assignee_id=new_assignee_id,
            assignee_name=new_assignee_name,
            assignee_email=new_assignee_email,
            operator_id=operator_id
        )
        
        # 添加日志
        ticket.add_log(
            action=WorkflowAction.TRANSFER,
            comment=comment or f"从 {old_assignee} 转派给 {new_assignee_name}",
            operator_id=operator_id,
            operator_name=operator_name,
            metadata={
                "old_assignee": old_assignee,
                "new_assignee": new_assignee_id,
                "reason": comment
            }
        )
        
        logger.info(f"工单转派：{ticket.id} {old_assignee} -> {new_assignee_name}")
        return ticket
    
    def escalate_ticket(
        self,
        ticket: Task,
        reason: str,
        operator_id: Optional[str] = None,
        operator_name: Optional[str] = None
    ) -> Task:
        """
        升级工单（提升优先级）
        
        Args:
            ticket: 工单对象
            reason: 升级原因
            operator_id: 操作人 ID
            operator_name: 操作人姓名
            
        Returns:
            Task: 更新后的工单
        """
        old_priority = ticket.priority
        
        # 提升优先级
        priority_order = {
            TaskPriority.LOW: 0,
            TaskPriority.MEDIUM: 1,
            TaskPriority.HIGH: 2,
            TaskPriority.URGENT: 3
        }
        
        current_level = priority_order.get(ticket.priority, 1)
        if current_level >= 3:
            raise ValueError("工单已经是最高优先级，无法升级")
        
        # 提升一级
        new_priority = list(priority_order.keys())[current_level + 1]
        ticket.priority = new_priority
        
        # 重新计算截止时间
        hours = ticket.get_timeout_hours()
        ticket.due_date = datetime.now() + timedelta(hours=hours)
        
        # 添加日志
        ticket.add_log(
            action=WorkflowAction.ESCALATE,
            comment=f"优先级升级：{old_priority.value} -> {new_priority.value}. 原因：{reason}",
            operator_id=operator_id,
            operator_name=operator_name,
            metadata={
                "old_priority": old_priority.value,
                "new_priority": new_priority.value,
                "reason": reason
            }
        )
        
        logger.info(f"工单升级：{ticket.id} {old_priority.value} -> {new_priority.value}")
        return ticket
    
    def resolve_ticket(
        self,
        ticket: Task,
        resolution_notes: Optional[str] = None,
        operator_id: Optional[str] = None,
        operator_name: Optional[str] = None
    ) -> Task:
        """
        解决工单
        
        Args:
            ticket: 工单对象
            resolution_notes: 解决说明
            operator_id: 操作人 ID
            operator_name: 操作人姓名
            
        Returns:
            Task: 更新后的工单
        """
        # 执行状态转换
        ticket.transition_to(
            new_status=TaskStatus.RESOLVED,
            operator_id=operator_id,
            operator_name=operator_name,
            comment=resolution_notes or "工单已解决"
        )
        
        logger.info(f"工单解决：{ticket.id} (操作人：{operator_name})")
        return ticket
    
    def close_ticket(
        self,
        ticket: Task,
        closing_notes: Optional[str] = None,
        operator_id: Optional[str] = None,
        operator_name: Optional[str] = None
    ) -> Task:
        """
        关闭工单（闭环）
        
        Args:
            ticket: 工单对象
            closing_notes: 关闭说明
            operator_id: 操作人 ID
            operator_name: 操作人姓名
            
        Returns:
            Task: 更新后的工单
        """
        # 执行状态转换
        ticket.transition_to(
            new_status=TaskStatus.CLOSED,
            operator_id=operator_id,
            operator_name=operator_name,
            comment=closing_notes or "工单已闭环"
        )
        
        logger.info(f"工单关闭：{ticket.id} (操作人：{operator_name})")
        return ticket
    
    def add_comment(
        self,
        ticket: Task,
        comment: TicketComment,
        operator_id: Optional[str] = None,
        operator_name: Optional[str] = None
    ) -> TicketComment:
        """
        添加评论
        
        Args:
            ticket: 工单对象
            comment: 评论对象
            operator_id: 操作人 ID
            operator_name: 操作人姓名
            
        Returns:
            TicketComment: 评论对象
        """
        # 添加工单日志
        ticket.add_log(
            action=WorkflowAction.COMMENT,
            comment=f"添加了评论",
            operator_id=operator_id,
            operator_name=operator_name,
            metadata={
                "comment_id": comment.id,
                "is_internal": comment.is_internal
            }
        )
        
        logger.info(f"工单评论：{ticket.id} (评论 ID: {comment.id})")
        return comment
    
    def get_workflow_logs(self, ticket: Task) -> List[Dict[str, Any]]:
        """
        获取工单工作流日志
        
        Args:
            ticket: 工单对象
            
        Returns:
            List[Dict]: 日志列表
        """
        return [log.dict() for log in ticket.logs]
    
    def validate_transition(self, ticket: Task, new_status: TaskStatus) -> bool:
        """
        验证状态转换是否合法
        
        Args:
            ticket: 工单对象
            new_status: 新状态
            
        Returns:
            bool: 是否合法
        """
        return TaskStatusMachine.can_transition(ticket.status, new_status)
