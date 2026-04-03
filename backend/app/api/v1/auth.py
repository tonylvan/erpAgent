"""认证授权 API。"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

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

router = APIRouter(prefix="/auth", tags=["认证授权"])


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
