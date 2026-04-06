"""API v1 路由汇总。"""

from fastapi import APIRouter

from app.api.v1 import data as data_routes
from app.api.v1 import graph as graph_routes
from app.api.v1 import websocket as ws_routes
from app.api.v1 import ticket_workflow as ticket_workflow_routes

router = APIRouter(prefix="/v1")

# 注册路由（P0 功能已移到 main.py 直接注册）
router.include_router(data_routes.router)
router.include_router(graph_routes.router)
router.include_router(ws_routes.router)
router.include_router(ticket_workflow_routes.router)
