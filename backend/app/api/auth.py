# -*- coding: utf-8 -*-
"""
JWT 认证模块
"""

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional
import jwt
import hashlib
import os

router = APIRouter(prefix="/api/v4/auth", tags=["认证"])

# JWT 配置
JWT_SECRET = os.getenv("JWT_SECRET_KEY", "erp-agent-secret-2026-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 30

# 安全方案
security = HTTPBearer()

# 模拟用户数据库（生产环境应使用真实数据库）
USERS_DB = {
    "admin": {
        "username": "admin",
        "password_hash": hashlib.sha256("admin123".encode()).hexdigest(),
        "role": "admin",
        "email": "admin@gsd.com"
    },
    "user": {
        "username": "user",
        "password_hash": hashlib.sha256("user123".encode()).hexdigest(),
        "role": "user",
        "email": "user@gsd.com"
    }
}


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    username: str
    role: str


class UserResponse(BaseModel):
    username: str
    email: str
    role: str


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """验证密码"""
    return hashlib.sha256(plain_password.encode()).hexdigest() == hashed_password


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """创建 JWT Token"""
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> dict:
    """获取当前用户（依赖注入）"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        token = credentials.credentials
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        username: str = payload.get("sub")
        
        if username is None:
            raise credentials_exception
        
        user = USERS_DB.get(username)
        if user is None:
            raise credentials_exception
        
        return user
    except jwt.PyJWTError:
        raise credentials_exception


@router.post("/login", response_model=LoginResponse, summary="用户登录")
async def login(request: LoginRequest):
    """
    用户登录获取 JWT Token
    
    - **username**: 用户名
    - **password**: 密码
    
    默认测试账号:
    - admin / admin123 (管理员权限)
    - user / user123 (普通用户权限)
    """
    user = USERS_DB.get(request.username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not verify_password(request.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=JWT_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"], "role": user["role"]},
        expires_delta=access_token_expires,
    )
    
    return LoginResponse(
        access_token=access_token,
        expires_in=JWT_EXPIRE_MINUTES * 60,
        username=user["username"],
        role=user["role"]
    )


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """获取当前登录用户信息"""
    return UserResponse(
        username=current_user["username"],
        email=current_user["email"],
        role=current_user["role"]
    )


@router.post("/logout", summary="用户登出")
async def logout():
    """
    用户登出
    
    注意：JWT 是无状态的，登出只是客户端删除 Token
    如需实现黑名单机制，需要 Redis 配合
    """
    return {"message": "登出成功"}


@router.post("/refresh", summary="刷新 Token")
async def refresh_token(current_user: dict = Depends(get_current_user)):
    """刷新 JWT Token"""
    access_token_expires = timedelta(minutes=JWT_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user["username"], "role": current_user["role"]},
        expires_delta=access_token_expires,
    )
    
    return LoginResponse(
        access_token=access_token,
        expires_in=JWT_EXPIRE_MINUTES * 60,
        username=current_user["username"],
        role=current_user["role"]
    )
