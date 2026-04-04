# -*- coding: utf-8 -*-
"""
GSD 智能问数 v4.0 - 智能路由引擎

根据查询类型自动路由：
- ERP 查询 → Neo4j 知识图谱（本地调用）
- 通用问题 → DashScope LLM（直接调用）
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import json
import os
from dotenv import load_dotenv

router = APIRouter()

# 加载环境变量
load_dotenv()

# DashScope 配置
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
try:
    import dashscope
    dashscope.api_key = DASHSCOPE_API_KEY
    DASHSCOPE_AVAILABLE = True
except ImportError:
    DASHSCOPE_AVAILABLE = False

# ERP 关键词识别
ERP_KEYWORDS = [
    '付款', '采购', '订单', '应付', '客户',
    '销售', '库存', '商品', '供应商', '仓库',
    '排行', '趋势', '预警', '账单', '收款',
    '物料', '入库', '出库', '退货', '对账',
    '财务', '会计', '应收', '结算', '核销'
]


class SmartQueryRequest(BaseModel):
    query: str
    user_id: str = "admin"
    session_id: Optional[str] = None


class SmartQueryResponse(BaseModel):
    success: bool
    route: str  # "neo4j" | "llm" | "error"
    data_type: str  # "chart" | "table" | "stats" | "text"
    answer: str
    data: Optional[dict] = None
    suggested_questions: Optional[List[str]] = None


def is_erp_query(query: str) -> bool:
    """判断是否为 ERP 相关查询"""
    return any(kw in query for kw in ERP_KEYWORDS)


def call_dashscope_llm(query: str) -> str:
    """调用 DashScope LLM 回答通用问题"""
    if not DASHSCOPE_AVAILABLE:
        return "DashScope SDK 未安装，无法回答通用问题。"
    
    try:
        response = dashscope.Generation.call(
            model="qwen-plus",
            messages=[
                {"role": "system", "content": "你是 GSD 智能问数助手，擅长回答企业 ERP 相关问题和通用问题。请用简洁的中文回答。"},
                {"role": "user", "content": query}
            ]
        )
        
        if response.status_code == 200:
            return response.output.text
        else:
            return f"LLM 调用失败：{response.message}"
    except Exception as e:
        return f"LLM 调用异常：{str(e)}"


def call_neo4j_query(query: str) -> dict:
    """
    调用 Neo4j 查询 ERP 数据
    这里简化实现，实际应调用 smart_query_v2 引擎
    """
    # TODO: 集成真实的 Neo4j 查询引擎
    return {
        "answer": f"[Neo4j] 查询：{query}\n\n（此处应返回真实 ERP 数据，待集成 v2.7 引擎）",
        "data_type": "text",
        "data": None
    }


@router.post("/query", response_model=SmartQueryResponse)
async def smart_query_v40(request: SmartQueryRequest):
    """
    v4.0 - 智能路由引擎
    
    根据查询类型自动路由：
    - ERP 查询 → Neo4j 知识图谱
    - 通用问题 → DashScope LLM
    """
    
    # 路由决策
    route = "neo4j" if is_erp_query(request.query) else "llm"
    
    try:
        if route == "neo4j":
            # Neo4j 查询
            result = call_neo4j_query(request.query)
            return SmartQueryResponse(
                success=True,
                route="neo4j",
                data_type=result.get("data_type", "text"),
                answer=result.get("answer", ""),
                data=result.get("data"),
                suggested_questions=[
                    "查询相关的其他维度",
                    "查看历史趋势",
                    "导出查询结果"
                ]
            )
        else:
            # LLM 回答
            answer = call_dashscope_llm(request.query)
            return SmartQueryResponse(
                success=True,
                route="llm",
                data_type="text",
                answer=answer,
                data=None,
                suggested_questions=[
                    "还有其他问题吗？",
                    "查询 ERP 数据",
                    "了解更多功能"
                ]
            )
        
    except Exception as e:
        return SmartQueryResponse(
            success=False,
            route="error",
            data_type="text",
            answer=f"v4.0 处理失败：{str(e)}",
            suggested_questions=[]
        )


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "ok",
        "version": "v4.0",
        "dashscope_available": DASHSCOPE_AVAILABLE,
        "erp_keywords_count": len(ERP_KEYWORDS),
        "description": "GSD Smart Query v4.0 - 智能路由引擎（Neo4j + DashScope LLM）"
    }
