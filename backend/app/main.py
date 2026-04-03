import logging
import os
from pathlib import Path

from dotenv import load_dotenv

# 便于 app.services 中 ontology 等 INFO 日志在控制台可见（与 uvicorn 并存时仅补充根 handler）
if not logging.root.handlers:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

# 必须在 import app.* 之前执行：固定读取 backend/.env，避免从项目根目录启动 uvicorn 时读不到
_backend_root = Path(__file__).resolve().parent.parent
load_dotenv(_backend_root / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.api.v1 import router as api_v1_router
from app.websocket.server import manager

app = FastAPI(
    title="GSD 企业智能决策中枢平台 API",
    description="""
## 功能模块

### 认证授权
- JWT Token 认证
- 角色权限控制 (RBAC)
- Token 刷新机制

### 数据查询
- PostgreSQL 表数据查询
- 表结构浏览
- 数据统计

### 图查询
- Neo4j 本体图谱
- Cypher 只读查询
- 图统计信息

### WebSocket
- 实时消息推送
- 代理状态更新
- 数据同步进度

## 认证流程

1. 调用 `/api/v1/auth/login` 获取 Token
2. 在请求头中添加 `Authorization: Bearer <token>`
3. Token 过期后使用 `/api/v1/auth/refresh` 刷新

## 测试账号

- 管理员：admin / admin123
- 普通用户：user / user123
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

origins = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(api_router, prefix="/api")  # 旧版 API（兼容）
app.include_router(api_v1_router, prefix="/api/v1")  # 新版 API v1


@app.get("/health")
def health():
    """健康检查。"""
    return {
        "status": "ok",
        "version": "1.0.0",
        "websocket_connections": manager.get_total_connections(),
    }


@app.get("/")
def root():
    """根路径。"""
    return {
        "name": "GSD 企业智能决策中枢平台 API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源。"""
    logger = logging.getLogger(__name__)
    logger.info(f"WebSocket 连接数：{manager.get_total_connections()}")
    # TODO: 清理数据库连接池等
