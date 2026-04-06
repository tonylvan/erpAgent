"""通知服务 - 实现站内通知、邮件通知、微信通知"""

from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
import logging
import smtplib
import httpx
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)


class NotificationChannel(str, Enum):
    """通知渠道"""
    IN_APP = "IN_APP"  # 站内通知
    EMAIL = "EMAIL"  # 邮件
    WECHAT = "WECHAT"  # 企业微信


class NotificationType(str, Enum):
    """通知类型"""
    ASSIGN = "ASSIGN"  # 工单分配
    TRANSFER = "TRANSFER"  # 工单转派
    ESCALATE = "ESCALATE"  # 工单升级
    RESOLVE = "RESOLVE"  # 工单解决
    CLOSE = "CLOSE"  # 工单关闭
    COMMENT = "COMMENT"  # 工单评论
    MENTION = "MENTION"  # 被提及
    SLA_WARNING = "SLA_WARNING"  # SLA 预警
    SLA_TIMEOUT = "SLA_TIMEOUT"  # SLA 超时


class NotificationPriority(str, Enum):
    """通知优先级"""
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class Notification(BaseModel):
    """通知模型"""
    id: str = Field(..., description="通知 ID")
    ticket_id: str = Field(..., description="工单 ID")
    user_id: str = Field(..., description="接收用户 ID")
    user_name: str = Field(..., description="接收用户姓名")
    user_email: Optional[str] = Field(None, description="用户邮箱")
    notification_type: NotificationType = Field(..., description="通知类型")
    channel: NotificationChannel = Field(..., description="通知渠道")
    priority: NotificationPriority = Field(default=NotificationPriority.NORMAL, description="优先级")
    title: str = Field(..., description="通知标题")
    content: str = Field(..., description="通知内容")
    is_read: bool = Field(default=False, description="是否已读")
    read_at: Optional[datetime] = Field(None, description="阅读时间")
    sent_at: Optional[datetime] = Field(None, description="发送时间")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="附加信息")
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class NotificationTemplate(BaseModel):
    """通知模板"""
    type: NotificationType
    title_template: str
    content_template: str
    channels: List[NotificationChannel]
    
    def render(self, context: Dict[str, Any]) -> tuple[str, str]:
        """
        渲染模板
        
        Args:
            context: 渲染上下文
            
        Returns:
            tuple: (标题，内容)
        """
        title = self.title_template.format(**context)
        content = self.content_template.format(**context)
        return title, content


# 通知模板配置
NOTIFICATION_TEMPLATES = {
    NotificationType.ASSIGN: NotificationTemplate(
        type=NotificationType.ASSIGN,
        title_template="【工单分配】您有新的工单 #{ticket_id}",
        content_template="""
您被分配了一个新的工单：

工单编号：#{ticket_id}
工单标题：{ticket_title}
优先级：{priority}
截止时间：{due_date}

请及时处理。
        """,
        channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL]
    ),
    NotificationType.TRANSFER: NotificationTemplate(
        type=NotificationType.TRANSFER,
        title_template="【工单转派】工单 #{ticket_id} 已转派给您",
        content_template="""
工单已转派给您：

工单编号：#{ticket_id}
工单标题：{ticket_title}
转派原因：{reason}

请查看并处理。
        """,
        channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL]
    ),
    NotificationType.ESCALATE: NotificationTemplate(
        type=NotificationType.ESCALATE,
        title_template="【工单升级】工单 #{ticket_id} 优先级已提升",
        content_template="""
工单优先级已升级：

工单编号：#{ticket_id}
工单标题：{ticket_title}
新优先级：{new_priority}
升级原因：{reason}

请优先处理。
        """,
        channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL]
    ),
    NotificationType.RESOLVE: NotificationTemplate(
        type=NotificationType.RESOLVE,
        title_template="【工单解决】工单 #{ticket_id} 已解决",
        content_template="""
工单已解决：

工单编号：#{ticket_id}
工单标题：{ticket_title}
解决说明：{resolution_notes}

请确认是否接受。
        """,
        channels=[NotificationChannel.IN_APP]
    ),
    NotificationType.CLOSE: NotificationTemplate(
        type=NotificationType.CLOSE,
        title_template="【工单关闭】工单 #{ticket_id} 已关闭",
        content_template="""
工单已关闭：

工单编号：#{ticket_id}
工单标题：{ticket_title}
关闭说明：{closing_notes}

工单已归档。
        """,
        channels=[NotificationChannel.IN_APP]
    ),
    NotificationType.COMMENT: NotificationTemplate(
        type=NotificationType.COMMENT,
        title_template="【新评论】工单 #{ticket_id} 有新评论",
        content_template="""
工单有新评论：

工单编号：#{ticket_id}
工单标题：{ticket_title}
评论人：{commenter_name}
评论内容：{comment_content}

请查看。
        """,
        channels=[NotificationChannel.IN_APP, NotificationChannel.WECHAT]
    ),
    NotificationType.SLA_WARNING: NotificationTemplate(
        type=NotificationType.SLA_WARNING,
        title_template="【SLA 预警】工单 #{ticket_id} 即将超时",
        content_template="""
工单即将超时：

工单编号：#{ticket_id}
工单标题：{ticket_title}
剩余时间：{remaining_time}
当前状态：{status}

请尽快处理！
        """,
        channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL, NotificationChannel.WECHAT]
    ),
    NotificationType.SLA_TIMEOUT: NotificationTemplate(
        type=NotificationType.SLA_TIMEOUT,
        title_template="【SLA 超时】工单 #{ticket_id} 已超时",
        content_template="""
工单已超时：

工单编号：#{ticket_id}
工单标题：{ticket_title}
超时时长：{overtime_duration}
当前状态：{status}

请立即处理并说明原因！
        """,
        channels=[NotificationChannel.IN_APP, NotificationChannel.EMAIL, NotificationChannel.WECHAT]
    )
}


class NotificationService:
    """通知服务"""
    
    def __init__(self, db_session=None, config: Optional[Dict[str, Any]] = None):
        """
        初始化通知服务
        
        Args:
            db_session: 数据库会话
            config: 配置信息
        """
        self.db = db_session
        self.config = config or {}
        
        # SMTP 配置
        self.smtp_config = self.config.get("smtp", {})
        
        # 企业微信配置
        self.wechat_config = self.config.get("wechat", {})
    
    def send_notification(
        self,
        ticket_id: str,
        user_id: str,
        user_name: str,
        user_email: Optional[str],
        notification_type: NotificationType,
        context: Dict[str, Any],
        channels: Optional[List[NotificationChannel]] = None
    ) -> List[Notification]:
        """
        发送通知
        
        Args:
            ticket_id: 工单 ID
            user_id: 用户 ID
            user_name: 用户姓名
            user_email: 用户邮箱
            notification_type: 通知类型
            context: 渲染上下文
            channels: 通知渠道列表
            
        Returns:
            List[Notification]: 发送的通知列表
        """
        import uuid
        
        # 获取模板
        template = NOTIFICATION_TEMPLATES.get(notification_type)
        if not template:
            logger.error(f"未找到通知模板：{notification_type}")
            return []
        
        # 渲染内容
        title, content = template.render(context)
        
        # 确定发送渠道
        if channels is None:
            channels = template.channels
        
        notifications = []
        
        for channel in channels:
            notification = Notification(
                id=str(uuid.uuid4()),
                ticket_id=ticket_id,
                user_id=user_id,
                user_name=user_name,
                user_email=user_email,
                notification_type=notification_type,
                channel=channel,
                title=title,
                content=content,
                metadata=context
            )
            
            # 发送到对应渠道
            if channel == NotificationChannel.IN_APP:
                self._send_in_app(notification)
            elif channel == NotificationChannel.EMAIL:
                self._send_email(notification)
            elif channel == NotificationChannel.WECHAT:
                self._send_wechat(notification)
            
            # 记录发送时间
            notification.sent_at = datetime.now()
            notifications.append(notification)
            
            logger.info(f"发送通知：{notification_type} -> {user_name} via {channel}")
        
        return notifications
    
    def _send_in_app(self, notification: Notification) -> None:
        """
        发送站内通知
        
        Args:
            notification: 通知对象
        """
        # TODO: 保存到数据库
        # if self.db:
        #     self.db.add(notification)
        #     self.db.commit()
        logger.debug(f"站内通知：{notification.title}")
    
    def _send_email(self, notification: Notification) -> None:
        """
        发送邮件通知
        
        Args:
            notification: 通知对象
        """
        if not notification.user_email:
            logger.warning(f"用户邮箱为空，跳过邮件发送：{notification.user_id}")
            return
        
        if not self.smtp_config:
            logger.warning("SMTP 配置缺失，跳过邮件发送")
            return
        
        try:
            # 创建邮件
            msg = MIMEMultipart()
            msg['From'] = self.smtp_config.get("from_email")
            msg['To'] = notification.user_email
            msg['Subject'] = notification.title
            
            # 添加正文
            msg.attach(MIMEText(notification.content, 'plain', 'utf-8'))
            
            # 发送邮件
            with smtplib.SMTP(self.smtp_config.get("host"), self.smtp_config.get("port")) as server:
                if self.smtp_config.get("use_tls"):
                    server.starttls()
                
                if self.smtp_config.get("username") and self.smtp_config.get("password"):
                    server.login(self.smtp_config["username"], self.smtp_config["password"])
                
                server.send_message(msg)
            
            logger.info(f"邮件发送成功：{notification.user_email}")
        
        except Exception as e:
            logger.error(f"邮件发送失败：{e}")
    
    def _send_wechat(self, notification: Notification) -> None:
        """
        发送企业微信通知
        
        Args:
            notification: 通知对象
        """
        if not self.wechat_config:
            logger.warning("企业微信配置缺失，跳过微信通知")
            return
        
        try:
            webhook_url = self.wechat_config.get("webhook_url")
            
            # 构建消息
            message = {
                "msgtype": "markdown",
                "markdown": {
                    "content": f"""**{notification.title}**

{notification.content}
"""
                }
            }
            
            # 发送请求
            response = httpx.post(webhook_url, json=message, timeout=10)
            response.raise_for_status()
            
            logger.info(f"企业微信发送成功：{notification.user_name}")
        
        except Exception as e:
            logger.error(f"企业微信发送失败：{e}")
    
    def mark_as_read(self, notification_id: str) -> bool:
        """
        标记通知为已读
        
        Args:
            notification_id: 通知 ID
            
        Returns:
            bool: 是否成功
        """
        # TODO: 更新数据库
        logger.info(f"标记通知为已读：{notification_id}")
        return True
    
    def get_unread_count(self, user_id: str) -> int:
        """
        获取用户未读通知数量
        
        Args:
            user_id: 用户 ID
            
        Returns:
            int: 未读数量
        """
        # TODO: 查询数据库
        return 0
    
    def get_user_notifications(
        self,
        user_id: str,
        is_read: Optional[bool] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        """
        获取用户通知列表
        
        Args:
            user_id: 用户 ID
            is_read: 是否已读（None 表示全部）
            limit: 数量限制
            offset: 偏移量
            
        Returns:
            List[Notification]: 通知列表
        """
        # TODO: 查询数据库
        return []


# 便捷函数
def send_assignment_notification(
    ticket_id: str,
    assignee_id: str,
    assignee_name: str,
    assignee_email: Optional[str],
    ticket_title: str,
    priority: str,
    due_date: str,
    service: NotificationService
) -> List[Notification]:
    """
    发送工单分配通知
    
    Args:
        ticket_id: 工单 ID
        assignee_id: 负责人 ID
        assignee_name: 负责人姓名
        assignee_email: 负责人邮箱
        ticket_title: 工单标题
        priority: 优先级
        due_date: 截止时间
        service: 通知服务
        
    Returns:
        List[Notification]: 发送的通知列表
    """
    return service.send_notification(
        ticket_id=ticket_id,
        user_id=assignee_id,
        user_name=assignee_name,
        user_email=assignee_email,
        notification_type=NotificationType.ASSIGN,
        context={
            "ticket_id": ticket_id,
            "ticket_title": ticket_title,
            "priority": priority,
            "due_date": due_date
        }
    )
