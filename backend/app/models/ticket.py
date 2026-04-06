"""
SQLAlchemy models for GSD Ticket system
"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class Ticket(Base):
    """Ticket database model"""
    __tablename__ = "tickets"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    status = Column(String(20), default="OPEN", index=True)  # OPEN/IN_PROGRESS/RESOLVED/CLOSED
    priority = Column(String(20), default="MEDIUM", index=True)  # LOW/MEDIUM/HIGH/URGENT
    description = Column(Text)
    category = Column(String(100), index=True)  # 工单分类
    created_by = Column(String(100), index=True)
    assigned_to = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True))
    resolved_by = Column(String(100))
    solution = Column(Text)  # 解决方案描述
    resolution_type = Column(String(50))  # 解决类型：fixed/negotiated/cannot_reproduce/etc
    closed_at = Column(DateTime(timezone=True))  # 关闭时间
    closed_by = Column(String(100))  # 关闭人
    close_reason = Column(Text)  # 关闭原因
    satisfaction = Column(String(50))  # 满意度：satisfied/unsatisfied
    reopen_reason = Column(Text)  # 重新打开原因
    reopened_at = Column(DateTime(timezone=True))  # 重新打开时间
    reopened_by = Column(String(100))  # 重新打开人
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "priority": self.priority,
            "description": self.description,
            "category": self.category,
            "created_by": self.created_by,
            "assigned_to": self.assigned_to,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "resolved_by": self.resolved_by,
            "solution": self.solution,
            "resolution_type": self.resolution_type,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
            "closed_by": self.closed_by,
            "close_reason": self.close_reason,
            "satisfaction": self.satisfaction,
            "reopen_reason": self.reopen_reason,
            "reopened_at": self.reopened_at.isoformat() if self.reopened_at else None,
            "reopened_by": self.reopened_by,
        }
