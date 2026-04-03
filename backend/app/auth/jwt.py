"""JWT 认证授权模块。"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# JWT 配置
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "7"))

# 安全方案
security = HTTPBearer(auto_error=False)


class TokenPayload(BaseModel):
    """Token 负载。"""
    sub: str  # 用户 ID
    exp: datetime  # 过期时间
    iat: datetime  # 签发时间
    type: str  # token 类型：access / refresh
    roles: list[str] | None = None  # 角色列表


class TokenResponse(BaseModel):
    """Token 响应。"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # 过期时间（秒）


class RefreshRequest(BaseModel):
    """刷新 Token 请求。"""
    refresh_token: str


class UserCredentials(BaseModel):
    """用户登录凭证。"""
    username: str
    password: str


class UserInfo(BaseModel):
    """用户信息。"""
    id: str
    username: str
    roles: list[str]
    email: str | None = None


def create_access_token(subject: str, roles: list[str] | None = None) -> str:
    """创建访问 Token。"""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    payload: dict[str, Any] = {
        "sub": subject,
        "exp": expire,
        "iat": now,
        "type": "access",
    }
    if roles:
        payload["roles"] = roles
    
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def create_refresh_token(subject: str) -> str:
    """创建刷新 Token。"""
    now = datetime.now(timezone.utc)
    expire = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    payload = {
        "sub": subject,
        "exp": expire,
        "iat": now,
        "type": "refresh",
    }
    
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str, expected_type: str | None = None) -> TokenPayload:
    """
    解码并验证 Token。
    
    Args:
        token: JWT Token
        expected_type: 期望的 token 类型（access / refresh）
    
    Returns:
        TokenPayload
    
    Raises:
        HTTPException: Token 无效或过期
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # 验证 token 类型
        if expected_type and payload.get("type") != expected_type:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Token 类型错误，期望：{expected_type}",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return TokenPayload(**payload)
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 已过期",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token 无效",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> UserInfo:
    """
    获取当前用户（依赖注入）。
    
    用于需要认证的路由。
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证信息",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    payload = decode_token(credentials.credentials, expected_type="access")
    
    # 模拟用户信息（实际应从数据库查询）
    return UserInfo(
        id=payload.sub,
        username=payload.sub,
        roles=payload.roles or ["user"],
        email=f"{payload.sub}@example.com",
    )


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> UserInfo | None:
    """
    获取当前用户（可选认证）。
    
    用于公开但支持认证的路由。
    """
    if credentials is None:
        return None
    
    try:
        payload = decode_token(credentials.credentials, expected_type="access")
        return UserInfo(
            id=payload.sub,
            username=payload.sub,
            roles=payload.roles or ["user"],
            email=f"{payload.sub}@example.com",
        )
    except HTTPException:
        return None


def require_role(required_role: str):
    """
    角色权限检查装饰器。
    
    用法：
        @router.get("/admin", dependencies=[Depends(require_role("admin"))])
        def admin_endpoint():
            ...
    """
    def role_checker(current_user: UserInfo = Depends(get_current_user)):
        if required_role not in current_user.roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"权限不足，需要角色：{required_role}",
            )
        return current_user
    return role_checker


# ============ 模拟用户数据库 ============
# 实际项目中应替换为真实数据库查询

MockUsers = {
    "admin": {
        "password": "admin123",  # 实际应存储 hash
        "roles": ["admin", "user"],
        "email": "admin@example.com",
    },
    "user": {
        "password": "user123",
        "roles": ["user"],
        "email": "user@example.com",
    },
}


def authenticate_user(username: str, password: str) -> UserInfo | None:
    """验证用户凭证。"""
    user = MockUsers.get(username)
    if not user:
        return None
    
    # 简单密码比较（实际应使用 bcrypt 等 hash）
    if user["password"] != password:
        return None
    
    return UserInfo(
        id=username,
        username=username,
        roles=user["roles"],
        email=user["email"],
    )


def login(username: str, password: str) -> TokenResponse:
    """用户登录。"""
    user = authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(user.username, user.roles)
    refresh_token = create_refresh_token(user.username)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


def refresh_token(refresh_token_str: str) -> TokenResponse:
    """刷新 Token。"""
    payload = decode_token(refresh_token_str, expected_type="refresh")
    
    # 创建新的 access token
    access_token = create_access_token(payload.sub)
    new_refresh_token = create_refresh_token(payload.sub)
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
