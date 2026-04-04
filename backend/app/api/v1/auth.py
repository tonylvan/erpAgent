"""认证授权 API。"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from app.auth.jwt import (
    TokenResponse,
    UserCredentials,
    RefreshRequest,
    UserInfo,
    login,
    refresh_token,
    get_current_user,
    security,
)
from app.core.database import get_db

# 导出 UserInfo 供其他模块使用
__all__ = ["UserInfo", "get_current_user"]

router = APIRouter(prefix="/auth", tags=["认证授权"])


class AuditLog(BaseModel):
    log_id: int
    user_id: int
    action: str
    resource: str
    ip_address: Optional[str] = None
    created_at: datetime


@router.post("/login", response_model=TokenResponse)
def user_login(credentials: UserCredentials):
    """
    用户登录。
    
    测试账号:
    - admin / admin123 (管理员权限)
    - user / user123 (普通用户)
    """
    return login(credentials.username, credentials.password)


@router.post("/refresh", response_model=TokenResponse)
def refresh_access_token(request: RefreshRequest):
    """刷新访问 Token。"""
    return refresh_token(request.refresh_token)


@router.get("/me", response_model=UserInfo)
def get_me(current_user: UserInfo = Depends(get_current_user)):
    """获取当前用户信息。"""
    return current_user


@router.post("/logout")
def user_logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    用户登出。
    
    注意：JWT 是无状态的，登出只是客户端删除 Token。
    如需实现黑名单，需要 Redis 等存储已撤销的 Token。
    """
    # TODO: 将 Token 加入黑名单（需要 Redis）
    return {"message": "登出成功"}


@router.get("/audit-logs", response_model=List[AuditLog])
def get_audit_logs(
    limit: int = 100,
    offset: int = 0,
    current_user: UserInfo = Depends(get_current_user),
    db=Depends(get_db)
):
    """
    查询审计日志（仅管理员）
    
    - **limit**: 返回数量限制
    - **offset**: 偏移量
    """
    # TODO: 添加权限检查（仅管理员）
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT log_id, user_id, action, resource, ip_address, created_at
            FROM sys_audit_logs
            ORDER BY created_at DESC
            LIMIT %s OFFSET %s
        """, (limit, offset))
        
        rows = cursor.fetchall()
        cursor.close()
        
        return [
            AuditLog(
                log_id=row[0],
                user_id=row[1],
                action=row[2],
                resource=row[3],
                ip_address=row[4],
                created_at=row[5]
            )
            for row in rows
        ]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"查询审计日志失败：{str(e)}"
        )
