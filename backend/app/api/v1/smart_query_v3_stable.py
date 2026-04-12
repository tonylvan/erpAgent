"""
GSD Smart Query v3 - 稳定版
参考 QQBot sessions_send 设计，但使用更稳定的实现

架构设计：
1. 简单查询：v2 NL2Cypher（1-3 秒，¥0.01）
2. 复杂查询：Dashscope API（3-8 秒，¥0.10）
3. 降级方案：自动 fallback 到 v2

不再使用 OpenClaw sessions_send（超时问题）
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import asyncio
import json
import os
import sys
import logging
from datetime import datetime

# Setup logging
logger = logging.getLogger(__name__)

# Add project path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

router = APIRouter(tags=["智能问数 v3 - 稳定版"])


# Request/Response Models
class QueryRequest(BaseModel):
    query: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ReasoningStep(BaseModel):
    """推理步骤"""
    step: int
    action: str
    description: str
    result: Optional[str] = None


class AgentQueryResponse(BaseModel):
    """查询响应"""
    success: bool
    answer: str
    reasoning_process: List[ReasoningStep] = []
    data_type: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    chart_config: Optional[Dict[str, Any]] = None
    follow_up: Optional[List[str]] = None
    session_id: str
    timestamp: datetime = None


# 复杂查询关键词
COMPLEX_KEYWORDS = ['分析', '预测', '为什么', '如何', '评估', '建议', '深度', '趋势', '原因']


def is_complex_query(query: str) -> bool:
    """检测是否为复杂查询"""
    return any(kw in query for kw in COMPLEX_KEYWORDS)


async def query_v2(query: str) -> Dict:
    """
    使用 v2 NL2Cypher 引擎（稳定方案）
    响应时间：1-3 秒
    成本：¥0.01/查询
    """
    try:
        from app.api.v1.smart_query_v2 import get_knowledge_engine
        engine = get_knowledge_engine()
        response = await engine.query(query)
        
        return {
            "success": True,
            "answer": response.get("answer", "查询完成"),
            "data_type": response.get("data_type", "text"),
            "data": response.get("data"),
            "chart_config": response.get("chart_config"),
            "follow_up": response.get("follow_up", []),
            "reasoning_process": [{
                "step": 1,
                "action": "nl2cypher",
                "description": "使用 NL2Cypher 引擎查询 Neo4j 知识图谱",
                "result": f"查询类型：{response.get('data_type', 'text')}"
            }]
        }
    except Exception as e:
        logger.error(f"v2 query failed: {e}")
        raise


async def call_dashscope(query: str) -> Dict:
    """
    使用 Dashscope API（复杂查询）
    响应时间：3-8 秒
    成本：¥0.10/查询
    
    注意：需要配置 DASHSCOPE_API_KEY 环境变量
    """
    try:
        # 检查 API Key
        api_key = os.getenv('DASHSCOPE_API_KEY')
        if not api_key:
            logger.warning("Dashscope API Key not configured, falling back to v2")
            return await query_v2(query)
        
        # TODO: 实现 Dashscope 调用
        # 当前先降级到 v2
        logger.info(f"Dashscope not implemented yet, using v2 for: {query[:50]}...")
        return await query_v2(query)
        
    except Exception as e:
        logger.error(f"Dashscope API failed: {e}")
        return await query_v2(query)


@router.post("/query", response_model=AgentQueryResponse)
async def smart_query(request: QueryRequest):
    """
    智能问数 v3 - 稳定版
    
    智能路由：
    - 简单查询 → v2 NL2Cypher（快速稳定）
    - 复杂查询 → Dashscope API（AI 深度分析）
    - 失败 → 自动降级到 v2
    """
    try:
        # 生成或使用现有 session_id
        session_id = request.session_id or f"session_{datetime.now().timestamp()}"
        
        # 检测查询复杂度
        complex_flag = is_complex_query(request.query)
        query_type = "复杂" if complex_flag else "简单"
        
        logger.info(f"[v3-Stable] {query_type}查询：{request.query[:50]}...")
        
        # 智能路由
        if complex_flag:
            # 复杂查询：使用 Dashscope（当前降级到 v2）
            result = await call_dashscope(request.query)
        else:
            # 简单查询：直接使用 v2
            result = await query_v2(request.query)
        
        # 构建响应
        return AgentQueryResponse(
            success=result["success"],
            answer=result["answer"],
            reasoning_process=[
                ReasoningStep(**step) if isinstance(step, dict) else step
                for step in result.get("reasoning_process", [])
            ],
            data_type=result.get("data_type"),
            data=result.get("data"),
            chart_config=result.get("chart_config"),
            follow_up=result.get("follow_up", []),
            session_id=session_id,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"[v3-Stable] Query failed: {e}")
        
        # 最终降级：返回友好错误
        return AgentQueryResponse(
            success=False,
            answer=f"抱歉，查询失败：{str(e)}\n\n请尝试：\n1. 简化问题\n2. 使用更具体的关键词\n3. 联系管理员",
            reasoning_process=[{
                "step": 1,
                "action": "error",
                "description": "查询处理失败",
                "result": str(e)
            }],
            data_type="text",
            follow_up=["重新提问", "查看帮助文档"],
            session_id=request.session_id or "unknown",
            timestamp=datetime.now()
        )


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "version": "v3-stable",
        "timestamp": datetime.now().isoformat(),
        "features": {
            "v2_nl2cypher": True,
            "dashscope_api": False,  # TODO: 配置 API Key 后启用
            "openclaw_sessions": False  # 已弃用（超时问题）
        }
    }
