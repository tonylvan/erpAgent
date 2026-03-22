from fastapi import APIRouter

from app.api import graph as graph_routes
from app.api import intelligence as intelligence_routes

router = APIRouter()
router.include_router(graph_routes.router, prefix="/graph", tags=["graph"])
router.include_router(intelligence_routes.router, prefix="/intelligence", tags=["intelligence"])


@router.get("/hello")
def hello():
    return {"message": "ERP Agent API 已就绪"}
