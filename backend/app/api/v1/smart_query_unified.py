"""
GSD Smart Query Unified API - Single Entry Point
All queries go through the unified router for automatic engine selection
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

from app.services.smart_query_router import smart_query_router

logger = logging.getLogger(__name__)

router = APIRouter(tags=["智能问数 - 统一入口"])


class UnifiedQueryRequest(BaseModel):
    """Unified query request"""
    query: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class UnifiedQueryResponse(BaseModel):
    """Unified query response"""
    success: bool
    answer: str
    engine: Optional[str] = None  # Which engine was used
    data_type: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    chart_config: Optional[Dict[str, Any]] = None
    follow_up: Optional[List[str]] = None
    reasoning_process: Optional[List[Dict[str, Any]]] = None  # Agent reasoning
    timestamp: Optional[str] = None


class SuggestedQuestionsResponse(BaseModel):
    """Suggested questions response"""
    success: bool = True
    questions: List[str] = []
    categories: Optional[Dict[str, List[str]]] = None
    timestamp: datetime = None


@router.post("/query", response_model=UnifiedQueryResponse)
async def unified_query(request: UnifiedQueryRequest):
    """
    Unified query endpoint - Automatic engine selection
    
    Features:
    - Single entry point for all queries
    - Automatic intent detection and engine selection
    - Fallback mechanism when engine fails
    - Unified response format
    
    Supported query types:
    - ERP Data: Neo4j engine (fast, structured)
    - Complex Analysis: Agent engine (reasoning, insights)
    - General Questions: LLM engine (fallback)
    """
    try:
        logger.info(f"[UnifiedAPI] Query received: {request.query[:50]}...")
        
        # Use unified router
        result = await smart_query_router.query(
            query=request.query,
            session_id=request.session_id
        )
        
        return UnifiedQueryResponse(**result)
        
    except Exception as e:
        logger.error(f"[UnifiedAPI] Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/suggested-questions", response_model=SuggestedQuestionsResponse)
async def get_suggested_questions():
    """
    Get suggested questions for quick access
    
    Categories:
    - 销售分析
    - 采购分析
    - 库存管理
    - 财务分析
    """
    suggestions = {
        "销售分析": [
            "本月销售趋势如何？",
            "客户销售排行Top 10",
            "最近一周销售额统计"
        ],
        "采购分析": [
            "供应商采购排行",
            "采购订单趋势分析",
            "供应商评价统计"
        ],
        "库存管理": [
            "库存预警列表",
            "库存周转率分析",
            "呆滞库存统计"
        ],
        "财务分析": [
            "客户回款排行",
            "应收账款统计",
            "付款趋势分析"
        ]
    }
    
    return SuggestedQuestionsResponse(
        success=True,
        questions=[
            "本月销售趋势如何？",
            "客户销售排行Top 10",
            "库存预警列表",
            "供应商采购排行"
        ],
        categories=suggestions,
        timestamp=datetime.now()
    )


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "service": "Smart Query Unified API",
        "version": "1.0.0",
        "engines": {
            "neo4j": smart_query_router.neo4j_engine is not None,
            "agent": True
        }
    }