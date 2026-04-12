"""
GSD Smart Query v3 - QQBot 优化版
参考 QQBot 消息处理逻辑：
1. 消息队列管理
2. 会话上下文追踪
3. 智能查询分类
4. 错误重试机制
5. 完整日志追踪
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from collections import deque
from functools import wraps
import asyncio
import json
import os
import sys
import logging
import time

# Setup logging
logger = logging.getLogger(__name__)

# Add project path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

router = APIRouter(tags=["智能问数 v3 - QQBot 优化版"])


# ==================== 数据模型 ====================

class QueryRequest(BaseModel):
    """查询请求"""
    query: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ReasoningStep(BaseModel):
    """推理步骤"""
    step: int
    action: str
    description: str
    result: Optional[str] = None


class QueryMetadata(BaseModel):
    """查询元数据"""
    query_type: str
    processing_time_ms: int
    data_source: str
    cache_hit: bool
    retry_count: int = 0


class AgentQueryResponse(BaseModel):
    """查询响应"""
    success: bool
    answer: str
    reasoning_process: List[ReasoningStep] = []
    data_type: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    chart_config: Optional[Dict[str, Any]] = None
    follow_up: Optional[List[str]] = None
    metadata: Optional[QueryMetadata] = None
    session_id: str
    timestamp: datetime = None


# ==================== 查询队列（参考 QQBot） ====================

class QueryQueue:
    """查询队列管理（参考 QQBot 消息队列）"""
    
    def __init__(self, max_size: int = 100):
        self.queue = deque(maxlen=max_size)
        self.lock = asyncio.Lock()
        self.processing = False
    
    async def enqueue(self, request: QueryRequest) -> int:
        """加入队列，返回队列位置"""
        async with self.lock:
            position = len(self.queue) + 1
            self.queue.append({
                "request": request,
                "timestamp": datetime.now(),
                "status": "pending",
                "trace_id": f"trace_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
            })
            logger.info(f"[Queue] Enqueued query, position: {position}, trace_id: {self.queue[-1]['trace_id']}")
            return position
    
    async def dequeue(self) -> Optional[Dict]:
        """取出队列"""
        async with self.lock:
            if self.queue:
                item = self.queue.popleft()
                item["status"] = "processing"
                logger.info(f"[Queue] Dequeued query, trace_id: {item['trace_id']}")
                return item
            return None
    
    def size(self) -> int:
        """队列大小"""
        return len(self.queue)
    
    def get_stats(self) -> Dict:
        """队列统计"""
        return {
            "size": len(self.queue),
            "max_size": self.queue.maxlen,
            "processing": self.processing
        }

# 全局查询队列
query_queue = QueryQueue()


# ==================== 会话管理（参考 QQBot） ====================

class SessionManager:
    """会话管理器（参考 QQBot 会话追踪）"""
    
    def __init__(self, max_history: int = 10, ttl_minutes: int = 30):
        self.sessions: Dict[str, Dict] = {}
        self.max_history = max_history
        self.ttl = timedelta(minutes=ttl_minutes)
        self.lock = asyncio.Lock()
    
    async def get_or_create(self, session_id: str) -> Dict:
        """获取或创建会话"""
        async with self.lock:
            now = datetime.now()
            
            if session_id in self.sessions:
                session = self.sessions[session_id]
                # 检查是否过期
                if now - session["created_at"] > self.ttl:
                    logger.info(f"[Session] Session {session_id} expired, creating new one")
                    del self.sessions[session_id]
                else:
                    return session
            
            # 创建新会话
            self.sessions[session_id] = {
                "created_at": now,
                "history": [],
                "query_count": 0,
                "last_activity": now
            }
            logger.info(f"[Session] Created new session: {session_id}")
            return self.sessions[session_id]
    
    async def add_history(self, session_id: str, query: str, response: Dict):
        """添加对话历史"""
        session = await self.get_or_create(session_id)
        session["history"].append({
            "query": query,
            "response": response,
            "timestamp": datetime.now()
        })
        # 保留最近 N 条
        if len(session["history"]) > self.max_history:
            session["history"] = session["history"][-self.max_history:]
        session["query_count"] += 1
        session["last_activity"] = datetime.now()
        logger.info(f"[Session] Added history to session {session_id}, total queries: {session['query_count']}")
    
    async def get_context(self, session_id: str) -> List[Dict]:
        """获取会话上下文"""
        session = await self.get_or_create(session_id)
        return session["history"][-5:]  # 最近 5 条
    
    async def cleanup_expired(self):
        """清理过期会话"""
        async with self.lock:
            now = datetime.now()
            expired = [
                sid for sid, session in self.sessions.items()
                if now - session["created_at"] > self.ttl
            ]
            for sid in expired:
                del self.sessions[sid]
            if expired:
                logger.info(f"[Session] Cleaned up {len(expired)} expired sessions")

# 全局会话管理器
session_manager = SessionManager()


# ==================== 查询分类器（参考 QQBot 消息类型） ====================

QUERY_PATTERNS = {
    'sales': ['销售', '销售额', '订单', '成交', '收入'],
    'customer': ['客户', '回款', '付款', '收款', '欠款'],
    'inventory': ['库存', '存货', '仓库', '备货'],
    'trend': ['趋势', '走势', '变化', '对比', '环比', '同比'],
    'analysis': ['分析', '为什么', '原因', '建议', '如何', '预测']
}

def classify_query(query: str) -> str:
    """
    查询分类（参考 QQBot 消息类型路由）
    返回：sales, customer, inventory, trend, analysis, general
    """
    for category, keywords in QUERY_PATTERNS.items():
        if any(kw in query for kw in keywords):
            logger.debug(f"[Classifier] Query '{query[:30]}...' classified as '{category}'")
            return category
    logger.debug(f"[Classifier] Query '{query[:30]}...' classified as 'general'")
    return 'general'


# ==================== 重试装饰器（参考 QQBot 错误处理） ====================

def retry_on_failure(max_attempts: int = 3, delay: float = 1.0):
    """重试装饰器（参考 QQBot 错误重试）"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    logger.warning(f"[Retry] Attempt {attempt + 1}/{max_attempts} failed: {e}")
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))  # 指数退避
            raise last_error
        return wrapper
    return decorator


# ==================== 查询处理 ====================

async def query_v2(query: str) -> Dict:
    """使用 v2 NL2Cypher 引擎"""
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
            }],
            "data_source": "neo4j",
            "cache_hit": False
        }
    except Exception as e:
        logger.error(f"v2 query failed: {e}")
        raise


async def call_dashscope(query: str) -> Dict:
    """使用 Dashscope API（复杂查询）"""
    try:
        api_key = os.getenv('DASHSCOPE_API_KEY')
        if not api_key:
            logger.warning("Dashscope API Key not configured, falling back to v2")
            return await query_v2(query)
        
        # TODO: 实现 Dashscope 调用
        logger.info(f"Dashscope not implemented yet, using v2 for: {query[:50]}...")
        return await query_v2(query)
        
    except Exception as e:
        logger.error(f"Dashscope API failed: {e}")
        return await query_v2(query)


@retry_on_failure(max_attempts=3, delay=0.5)
async def process_query(request: QueryRequest, trace_id: str) -> Dict:
    """处理查询（带重试）"""
    start_time = time.time()
    
    # 查询分类
    query_type = classify_query(request.query)
    logger.info(f"[{trace_id}] Query type: {query_type}")
    
    # 智能路由
    if query_type in ['analysis', 'trend']:
        logger.info(f"[{trace_id}] Complex query, using AI analysis")
        result = await call_dashscope(request.query)
    else:
        logger.info(f"[{trace_id}] Simple query, using v2 NL2Cypher")
        result = await query_v2(request.query)
    
    # 添加元数据
    processing_time = int((time.time() - start_time) * 1000)
    result["metadata"] = {
        "query_type": query_type,
        "processing_time_ms": processing_time,
        "data_source": result.get("data_source", "neo4j"),
        "cache_hit": result.get("cache_hit", False),
        "trace_id": trace_id
    }
    
    logger.info(f"[{trace_id}] Query processed in {processing_time}ms")
    return result


# ==================== API 端点 ====================

@router.post("/query", response_model=AgentQueryResponse)
async def smart_query(request: QueryRequest):
    """
    智能问数 v3 - QQBot 优化版
    
    功能：
    1. 消息队列管理
    2. 会话上下文追踪
    3. 智能查询分类
    4. 错误重试机制
    5. 完整日志追踪
    """
    trace_id = f"trace_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"
    logger.info(f"[{trace_id}] Received query: {request.query[:50]}...")
    
    try:
        # 1. 加入队列
        position = await query_queue.enqueue(request)
        logger.info(f"[{trace_id}] Queue position: {position}")
        
        # 2. 获取或创建会话
        session_id = request.session_id or f"session_{datetime.now().timestamp()}"
        session = await session_manager.get_or_create(session_id)
        
        # 3. 处理查询
        result = await process_query(request, trace_id)
        
        # 4. 添加到会话历史
        await session_manager.add_history(session_id, request.query, result)
        
        # 5. 构建响应
        response = AgentQueryResponse(
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
            metadata=QueryMetadata(**result["metadata"]) if "metadata" in result else None,
            session_id=session_id,
            timestamp=datetime.now()
        )
        
        logger.info(f"[{trace_id}] Query completed successfully")
        return response
        
    except Exception as e:
        logger.error(f"[{trace_id}] Query failed: {e}", exc_info=True)
        
        # 错误响应
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
        "version": "v3-qqbot-optimized",
        "timestamp": datetime.now().isoformat(),
        "queue_stats": query_queue.get_stats(),
        "session_count": len(session_manager.sessions),
        "features": {
            "message_queue": True,
            "session_management": True,
            "query_classification": True,
            "retry_mechanism": True,
            "trace_logging": True,
            "v2_nl2cypher": True,
            "dashscope_api": False
        }
    }


@router.get("/queue/stats")
async def queue_stats():
    """队列统计"""
    return query_queue.get_stats()


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """获取会话信息"""
    session = await session_manager.get_or_create(session_id)
    return {
        "session_id": session_id,
        "created_at": session["created_at"].isoformat(),
        "query_count": session["query_count"],
        "history_count": len(session["history"]),
        "last_activity": session["last_activity"].isoformat()
    }
