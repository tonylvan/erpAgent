"""
GSD 智能问数后端 API v2.6 - OpenClaw HTTP API 集成版
- 使用 OpenClaw Gateway HTTP API 进行查询
- 支持 WebSocket 连接到 Gateway
- 保留 Redis 缓存和降级机制
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import json
import os
import sys
import re
import hashlib
import asyncio
import aiohttp
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from app.core.redis_cache import cache

router = APIRouter(tags=["智能问数 v2.6"])


class QueryRequest(BaseModel):
    query: str
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    success: bool
    answer: str
    data_type: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    chart_config: Optional[Dict[str, Any]] = None
    follow_up: Optional[List[str]] = None


# OpenClaw Gateway 配置
GATEWAY_URL = os.getenv("OPENCLAW_GATEWAY_URL", "http://127.0.0.1:18789")
GATEWAY_TOKEN = os.getenv("OPENCLAW_GATEWAY_TOKEN", "3354bfe288d7b3d499d84d5b21d540ce21ff0c3e7dedbc18")


class SmartQueryEngine:
    """智能问数引擎 - OpenClaw HTTP API 集成"""
    
    def __init__(self):
        self.cache = cache
        self.memory_cache = {}
        self.session_id = None
        self.http_session = None
    
    async def init_session(self):
        """初始化 HTTP 会话"""
        if self.http_session is None:
            self.http_session = aiohttp.ClientSession(
                headers={"Authorization": f"Bearer {GATEWAY_TOKEN}"}
            )
    
    async def close_session(self):
        """关闭 HTTP 会话"""
        if self.http_session:
            await self.http_session.close()
            self.http_session = None
    
    async def query(self, question: str) -> dict:
        """处理查询 - 使用 OpenClaw HTTP API"""
        cache_key = f"gsd:query:{hashlib.md5(question.encode()).hexdigest()}"
        
        cached = self.cache.get(cache_key)
        if cached:
            print(f"[CACHE] Redis 命中：{question}")
            return cached
        
        if cache_key in self.memory_cache:
            print(f"[CACHE] 内存命中：{question}")
            return self.memory_cache[cache_key]
        
        print(f"[HTTP API] 查询：{question}")
        response = await self._query_openclaw_http(question)
        
        if self.cache.enabled:
            self.cache.set(cache_key, response, expire=3600)
        else:
            self.memory_cache[cache_key] = response
        
        if len(self.memory_cache) > 1000:
            self.memory_cache.pop(next(iter(self.memory_cache)))
        
        return response
    
    async def _query_openclaw_http(self, question: str) -> dict:
        """使用 OpenClaw HTTP API 查询"""
        await self.init_session()
        
        try:
            # 调用 OpenClaw Gateway HTTP API
            payload = {
                "message": question,
                "json": True,
                "timeout": 60
            }
            
            if self.session_id:
                payload["session_id"] = self.session_id
            
            async with self.http_session.post(
                f"{GATEWAY_URL}/agent",
                json=payload,
                timeout=aiohttp.ClientTimeout(total=60)
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # 保存会话 ID 以便复用
                    if "session_id" in result:
                        self.session_id = result["session_id"]
                    
                    # 解析响应
                    return self._parse_openclaw_response(result)
                else:
                    error_text = await response.text()
                    print(f"[HTTP API] 错误：{response.status} - {error_text}")
        except aiohttp.ClientError as e:
            print(f"[HTTP API] 网络错误：{e}")
        except asyncio.TimeoutError:
            print(f"[HTTP API] 查询超时")
        except Exception as e:
            print(f"[HTTP API] 异常：{e}")
        
        # 降级响应
        return self._fallback_response(question)
    
    def _parse_openclaw_response(self, result: dict) -> dict:
        """解析 OpenClaw 响应"""
        # 尝试从响应中提取结构化数据
        text = result.get("answer", result.get("text", str(result)))
        
        # 尝试解析为 JSON（如果 OpenClaw 返回结构化数据）
        try:
            data = json.loads(text)
            return {
                "answer": data.get("answer", text),
                "data_type": data.get("data_type", "text"),
                "data": data.get("data"),
                "chart_config": data.get("chart_config"),
                "follow_up": data.get("follow_up", ["继续询问"])
            }
        except (json.JSONDecodeError, TypeError):
            # 纯文本响应，尝试提取结构化数据
            return self._extract_structured_data(text)
    
    def _extract_structured_data(self, text: str) -> dict:
        """从纯文本中提取结构化数据"""
        # 检测数据类型
        if "【库存" in text or "库存" in text:
            return {
                "answer": text,
                "data_type": "text",
                "follow_up": ["查看库存详情", "生成补货订单"]
            }
        elif "【付款" in text or "付款" in text:
            return {
                "answer": text,
                "data_type": "text",
                "follow_up": ["查看付款详情", "导出付款报表"]
            }
        else:
            return {
                "answer": text,
                "data_type": "text",
                "follow_up": ["继续询问", "查看更多"]
            }
    
    def _fallback_response(self, question: str) -> dict:
        """降级响应"""
        return {
            "answer": f"""【智能问数助手】

我理解您想了解：{question}

目前支持的查询类型：
- 库存查询："查询当前库存状态"
- 付款单："查最近一笔付款单"
- 客户排行："Top 10 客户排行"
- 销售趋势："显示本周销售趋势"
- 财务概览："显示财务关键指标"

请尝试以上问题！""",
            "data_type": "text",
            "follow_up": ["显示本周销售趋势", "查询 Top 10 客户", "显示库存预警商品"]
        }


# 全局引擎
query_engine = SmartQueryEngine()


@router.on_event("shutdown")
async def shutdown_event():
    """关闭时清理资源"""
    await query_engine.close_session()


@router.post("/query", response_model=QueryResponse)
async def smart_query(request: QueryRequest):
    """智能问数 v2.6 - OpenClaw HTTP API"""
    try:
        result = await query_engine.query(request.query)
        return QueryResponse(
            success=True,
            answer=result["answer"],
            data_type=result.get("data_type"),
            data=result.get("data"),
            chart_config=result.get("chart_config"),
            follow_up=result.get("follow_up")
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"查询失败：{str(e)}")


@router.get("/suggested-questions")
async def get_suggested_questions():
    """推荐问题"""
    return {
        "questions": [
            "显示本周销售趋势",
            "查询 Top 10 客户",
            "统计各产品类别销售额",
            "显示库存预警商品",
            "分析本周付款预测"
        ]
    }


@router.get("/cache-stats")
async def get_cache_stats():
    """获取缓存统计信息"""
    stats = cache.stats()
    return {
        "cache_enabled": stats.get("enabled", False),
        "redis_connected": stats.get("connected", False),
        "db_size": stats.get("db_size", 0),
        "total_commands": stats.get("total_commands_processed", 0),
        "cache_hits": stats.get("keyspace_hits", 0),
        "cache_misses": stats.get("keyspace_misses", 0),
        "hit_rate": f"{(stats.get('keyspace_hits', 0) / max(stats.get('keyspace_hits', 0) + stats.get('keyspace_misses', 1), 1)) * 100:.1f}%"
    }
