"""WebSocket 路由。"""

import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Depends

from app.websocket.server import manager
from app.auth.jwt import decode_token, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str | None = Query(None, description="JWT Token"),
    user_id: str | None = Query(None, description="用户 ID（测试用）"),
):
    """
    WebSocket 连接端点。
    
    连接方式:
    - 认证连接：ws://host:port/ws?token=<JWT_TOKEN>
    - 测试连接：ws://host:port/ws?user_id=test_user
    
    消息格式:
    {
        "type": "message_type",
        "data": {...},
        "channel": "optional_channel"
    }
    """
    # 认证
    authenticated_user_id = user_id
    
    if token:
        try:
            payload = decode_token(token, expected_type="access")
            authenticated_user_id = payload.sub
            logger.info(f"WebSocket 认证成功：user={payload.sub}")
        except HTTPException as e:
            logger.warning(f"WebSocket 认证失败：{e.detail}")
            await websocket.close(code=4001, reason="认证失败")
            return
    elif not user_id:
        await websocket.close(code=4000, reason="需要 token 或 user_id")
        return
    
    if not authenticated_user_id:
        await websocket.close(code=4000, reason="用户 ID 为空")
        return
    
    # 建立连接
    await manager.connect(websocket, authenticated_user_id)
    
    try:
        while True:
            # 接收消息
            data = await websocket.receive_json()
            msg_type = data.get("type")
            msg_data = data.get("data", {})
            
            logger.debug(f"收到消息：user={authenticated_user_id}, type={msg_type}")
            
            # 处理消息
            if msg_type == "ping":
                await manager.send_personal(websocket, {"type": "pong"})
            
            elif msg_type == "join_room":
                room_id = msg_data.get("room_id")
                if room_id:
                    manager.join_room(authenticated_user_id, room_id)
                    await manager.send_personal(
                        websocket,
                        {"type": "room_joined", "room_id": room_id},
                    )
            
            elif msg_type == "leave_room":
                room_id = msg_data.get("room_id")
                if room_id:
                    manager.leave_room(authenticated_user_id, room_id)
                    await manager.send_personal(
                        websocket,
                        {"type": "room_left", "room_id": room_id},
                    )
            
            elif msg_type == "get_stats":
                stats = manager.get_stats()
                await manager.send_personal(
                    websocket,
                    {"type": "stats", "data": stats},
                )
            
            else:
                logger.warning(f"未知消息类型：{msg_type}")
    
    except WebSocketDisconnect:
        logger.info(f"WebSocket 断开：user={authenticated_user_id}")
    except Exception as e:
        logger.error(f"WebSocket 错误：{e}")
    finally:
        manager.disconnect(websocket, authenticated_user_id)


@router.get("/ws/stats")
def get_websocket_stats():
    """获取 WebSocket 连接统计。"""
    return {
        "success": True,
        "data": manager.get_stats(),
    }
