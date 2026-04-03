"""WebSocket 实时推送服务。"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)


class ConnectionManager:
    """WebSocket 连接管理器。"""
    
    def __init__(self):
        # 活跃连接：{user_id: [WebSocket, ...]}
        self.active_connections: dict[str, list[WebSocket]] = {}
        # 广播房间：{room_id: [user_id, ...]}
        self.rooms: dict[str, list[str]] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        """接受 WebSocket 连接。"""
        await websocket.accept()
        
        async with self._lock:
            if user_id not in self.active_connections:
                self.active_connections[user_id] = []
            self.active_connections[user_id].append(websocket)
        
        logger.info(f"WebSocket 连接：user_id={user_id}, 总连接数={self.get_total_connections()}")
        
        # 发送欢迎消息
        await self.send_personal(
            websocket,
            {
                "type": "connected",
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
            },
        )
    
    def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        """断开 WebSocket 连接。"""
        if user_id in self.active_connections:
            connections = self.active_connections[user_id]
            if websocket in connections:
                connections.remove(websocket)
            
            # 清理空列表
            if not connections:
                del self.active_connections[user_id]
        
        logger.info(f"WebSocket 断开：user_id={user_id}, 剩余连接数={self.get_total_connections()}")
    
    async def send_personal(self, websocket: WebSocket, message: dict[str, Any]) -> None:
        """发送个人消息。"""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"发送消息失败：{e}")
    
    async def broadcast_to_user(self, user_id: str, message: dict[str, Any]) -> None:
        """广播消息给特定用户的所有连接。"""
        if user_id not in self.active_connections:
            return
        
        # 复制到列表避免迭代中修改
        connections = list(self.active_connections.get(user_id, []))
        
        for websocket in connections:
            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"广播消息失败 (user={user_id}): {e}")
    
    async def broadcast_to_room(self, room_id: str, message: dict[str, Any]) -> None:
        """广播消息给房间内的所有用户。"""
        if room_id not in self.rooms:
            return
        
        for user_id in self.rooms[room_id]:
            await self.broadcast_to_user(user_id, message)
    
    async def broadcast_all(self, message: dict[str, Any]) -> None:
        """广播消息给所有连接。"""
        for user_id in list(self.active_connections.keys()):
            await self.broadcast_to_user(user_id, message)
    
    def join_room(self, user_id: str, room_id: str) -> None:
        """加入房间。"""
        if room_id not in self.rooms:
            self.rooms[room_id] = []
        
        if user_id not in self.rooms[room_id]:
            self.rooms[room_id].append(user_id)
        
        logger.info(f"用户 {user_id} 加入房间 {room_id}")
    
    def leave_room(self, user_id: str, room_id: str) -> None:
        """离开房间。"""
        if room_id in self.rooms and user_id in self.rooms[room_id]:
            self.rooms[room_id].remove(user_id)
            
            # 清理空房间
            if not self.rooms[room_id]:
                del self.rooms[room_id]
    
    def get_total_connections(self) -> int:
        """获取总连接数。"""
        return sum(len(conns) for conns in self.active_connections.values())
    
    def get_stats(self) -> dict[str, Any]:
        """获取连接统计。"""
        return {
            "total_connections": self.get_total_connections(),
            "unique_users": len(self.active_connections),
            "rooms": len(self.rooms),
            "room_details": {
                room_id: len(users) for room_id, users in self.rooms.items()
            },
        }


# 全局管理器实例
manager = ConnectionManager()


# ============ 消息类型定义 ============

class MessageType:
    """消息类型常量。"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    
    # 业务消息
    AGENT_STATUS = "agent_status"  # 代理状态更新
    DATA_SYNC = "data_sync"  # 数据同步进度
    QUERY_RESULT = "query_result"  # 查询结果
    NOTIFICATION = "notification"  # 通知
    ALERT = "alert"  # 告警


def create_message(
    msg_type: str,
    data: Any = None,
    channel: str | None = None,
) -> dict[str, Any]:
    """创建标准消息格式。"""
    return {
        "type": msg_type,
        "data": data,
        "channel": channel,
        "timestamp": datetime.now().isoformat(),
    }


async def send_agent_status(user_id: str, agent_name: str, status: str, details: dict | None = None):
    """发送代理状态更新。"""
    await manager.broadcast_to_user(
        user_id,
        create_message(
            MessageType.AGENT_STATUS,
            {
                "agent": agent_name,
                "status": status,
                "details": details or {},
            },
        ),
    )


async def send_data_sync_progress(
    user_id: str,
    task_id: str,
    progress: int,
    total: int,
    message: str,
):
    """发送数据同步进度。"""
    await manager.broadcast_to_user(
        user_id,
        create_message(
            MessageType.DATA_SYNC,
            {
                "task_id": task_id,
                "progress": progress,
                "total": total,
                "percentage": round(progress / total * 100, 2) if total > 0 else 0,
                "message": message,
            },
        ),
    )


async def send_notification(user_id: str, title: str, content: str, level: str = "info"):
    """发送通知。"""
    await manager.broadcast_to_user(
        user_id,
        create_message(
            MessageType.NOTIFICATION,
            {
                "title": title,
                "content": content,
                "level": level,  # info, warning, error, success
            },
        ),
    )


async def send_alert(user_id: str, alert_type: str, message: str, severity: str = "medium"):
    """发送告警。"""
    await manager.broadcast_to_user(
        user_id,
        create_message(
            MessageType.ALERT,
            {
                "alert_type": alert_type,
                "message": message,
                "severity": severity,  # low, medium, high, critical
            },
        ),
    )
