"""API v1 路由汇总。"""

from fastapi import APIRouter

from app.api.v1 import auth as auth_routes
from app.api.v1 import data as data_routes
from app.api.v1 import graph as graph_routes
from app.api.v1 import websocket as ws_routes

router = APIRouter(prefix="/v1")

# 注册路由
router.include_router(auth_routes.router)
router.include_router(data_routes.router)
router.include_router(graph_routes.router)
router.include_router(ws_routes.router)
