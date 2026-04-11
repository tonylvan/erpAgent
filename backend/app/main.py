import logging
import os
from pathlib import Path

from dotenv import load_dotenv

#  app.services ?ontology ?INFO  uvicorn ?handler?
if not logging.root.handlers:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

# ?import app.* ?backend/.env?uvicorn 
_backend_root = Path(__file__).resolve().parent.parent
load_dotenv(_backend_root / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.api.v1 import router as api_v1_router
from app.api.v1.smart_query import router as smart_query_router
from app.api.v1.smart_query_v2 import router as smart_query_v2_router
from app.api.v1.smart_query_v3_agent import router as smart_query_v3_agent_router
from app.api.v1.smart_query_unified import router as smart_query_unified_router  # New unified API
from app.api.v1.smart_query_openclaw_real import router as smart_query_openclaw_router  # OpenClaw Agent mode
from app.api.v1.auth import router as auth_router
from app.api.v1.query_history import router as query_history_router
from app.api.v1.alerts_v3 import router as alerts_v3_router
from app.api.v1.tickets import router as tickets_router
from app.api.v1.ticket_workflow import router as ticket_workflow_router
from app.api.v1.ticket_comments import router as ticket_comments_router
from app.api.v1.graph import router as graph_router
from app.api.v1.path_analysis import router as path_analysis_router
from app.api.v1.community_detection import router as community_detection_router
from app.api.v1.alert_escalation import router as alert_escalation_router
from app.api.v1.ticket_alert_integration import router as ticket_alert_integration_router
from app.websocket.server import manager

app = FastAPI(
    title="GSD  API",
    description="""
## 

### 
- JWT Token 
-  (RBAC)
- Token 

### 
- PostgreSQL ?
- ?
- 

### ?
- Neo4j 
- Cypher 
- ?

### WebSocket
- ?
- ?
- 

## 

1.  `/api/v1/auth/login`  Token
2. ?`Authorization: Bearer <token>`
3. Token ?`/api/v1/auth/refresh` 

## 

- admin / admin123
- user / user123
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS 配置 - 支持 localhost、127.0.0.1 和局域网
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:5175",
        "http://localhost:5176",
        "http://localhost:5177",
        "http://localhost:5178",
        "http://localhost:5179",
        "http://localhost:5180",
        "http://localhost:5181",
        "http://localhost:5182",
        "http://localhost:5183",
        "http://localhost:5184",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
        "http://127.0.0.1:5175",
        "http://127.0.0.1:5176",
        "http://127.0.0.1:5177",
        "http://127.0.0.1:5178",
        "http://127.0.0.1:5179",
        "http://127.0.0.1:5180",
        "http://127.0.0.1:5181",
        "http://127.0.0.1:5182",
        "http://127.0.0.1:5183",
        "http://127.0.0.1:5184",
        "http://192.168.1.113:5180",
        "http://192.168.1.113:5181",
        "http://192.168.1.113:5182",
        "http://192.168.1.113:5183",
        "http://192.168.1.113:5184",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 
app.include_router(api_router, prefix="/api")  #  API
app.include_router(api_v1_router, prefix="/api/v1")  #  API v1
app.include_router(smart_query_unified_router, prefix="/api/v1/smart-query")  # 🚀 Unified API (recommended)
app.include_router(smart_query_router, prefix="/api/v1/smart-query-legacy")  # Legacy v1 (deprecated)
app.include_router(smart_query_v2_router, prefix="/api/v1/smart-query-v2")  # Legacy v2 (still available)
app.include_router(smart_query_v3_agent_router, prefix="/api/v1/smart-query-v3-agent")  # Legacy v3 (still available)
app.include_router(smart_query_openclaw_router, prefix="/api/v1/smart-query-agent")  # OpenClaw Agent
# P0  - ?
app.include_router(auth_router, prefix="/api/v1")
app.include_router(query_history_router, prefix="/api/v1")
app.include_router(alerts_v3_router, prefix="/api/v1/alerts")  # Alert Center v2.0 API
app.include_router(tickets_router, prefix="/api/v1/tickets")  # Ticket Center API
app.include_router(ticket_workflow_router, prefix="/api/v1/tickets")  # Ticket Workflow API
app.include_router(ticket_comments_router, prefix="/api/v1")  # Ticket Comments API (prefix already set in router)
app.include_router(graph_router, prefix="/api/v1/graph")  # Knowledge Graph API
app.include_router(path_analysis_router, prefix="/api/v1/path-analysis")  # Path Analysis API
app.include_router(community_detection_router, prefix="/api/v1/community")  # Community Detection API
app.include_router(alert_escalation_router, prefix="/api/v1")  # Alert Escalation API (prefix already set in router)
app.include_router(ticket_alert_integration_router, prefix="/api/v1")  # Ticket-Alert Integration API

# Test route to verify server is running with latest code
@app.get("/api/v1/test")
def test_endpoint():
    """Test endpoint to verify code reload"""
    return {"status": "ok", "message": "Alert Center v2.0 API loaded", "timestamp": "2026-04-06 02:00"}


@app.get("/health")
def health():
    """Health check endpoint"""
    return {
        "status": "ok",
        "version": "1.0.0",
        "websocket_connections": manager.get_total_connections(),
    }


@app.get("/")
def root():
    """GSD Platform API Root"""
    return {
        "name": "GSD  API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger = logging.getLogger(__name__)
    logger.info(f"WebSocket {manager.get_total_connections()}")
    # TODO: Cleanup resources

