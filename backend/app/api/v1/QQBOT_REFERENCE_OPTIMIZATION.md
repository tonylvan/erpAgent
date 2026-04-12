# 🔄 参考 QQBot 优化智能问数 v3

**优化时间**: 2026-04-12 22:58  
**参考**: QQBot 消息处理逻辑

---

## 📊 QQBot 核心架构分析

### 消息处理流程

```
用户消息 → QQBot 接收 → 消息队列 → 处理器 → 响应生成 → 回复用户
```

### 关键特性

| 特性 | QQBot 实现 | 智能问数 v3 应用 |
|------|-----------|-----------------|
| **消息队列** | ✅ 异步处理 | ✅ asyncio.Queue |
| **会话管理** | ✅ session_id 追踪 | ✅ 已有 session_id |
| **超时处理** | ✅ 30 秒超时 | ✅ 已有超时 |
| **降级方案** | ✅ fallback 机制 | ✅ 已有 v2 降级 |
| **日志记录** | ✅ 完整日志 | ✅ 已有 logging |
| **上下文管理** | ✅ 多轮对话 | ✅ 已有 context |

---

## 🎯 优化方案

### 1. 消息队列（新增）

**QQBot 参考**：
```javascript
// QQBot 使用消息队列处理并发
this.messageQueue = new AsyncQueue();
await this.messageQueue.push({ userId, message, timestamp });
```

**智能问数 v3 实现**：
```python
import asyncio
from collections import deque

class QueryQueue:
    """查询队列管理"""
    
    def __init__(self, max_size: int = 100):
        self.queue = deque(maxlen=max_size)
        self.lock = asyncio.Lock()
    
    async def enqueue(self, query: QueryRequest):
        """加入队列"""
        async with self.lock:
            self.queue.append({
                "query": query,
                "timestamp": datetime.now(),
                "status": "pending"
            })
    
    async def dequeue(self):
        """取出队列"""
        async with self.lock:
            if self.queue:
                return self.queue.popleft()
            return None
    
    def size(self) -> int:
        """队列大小"""
        return len(self.queue)

# 全局队列实例
query_queue = QueryQueue()
```

---

### 2. 会话上下文管理（增强）

**QQBot 参考**：
```javascript
// 会话上下文
this.sessions = new Map();
session = this.sessions.get(userId) || this.createSession(userId);
session.history.push({ role: 'user', content: message });
```

**智能问数 v3 实现**：
```python
from typing import Dict, List
from datetime import timedelta

class SessionManager:
    """会话管理器"""
    
    def __init__(self, max_history: int = 10, ttl_minutes: int = 30):
        self.sessions: Dict[str, Dict] = {}
        self.max_history = max_history
        self.ttl = timedelta(minutes=ttl_minutes)
    
    def get_or_create(self, session_id: str) -> Dict:
        """获取或创建会话"""
        now = datetime.now()
        
        if session_id in self.sessions:
            session = self.sessions[session_id]
            # 检查是否过期
            if now - session["created_at"] > self.ttl:
                del self.sessions[session_id]
            else:
                return session
        
        # 创建新会话
        self.sessions[session_id] = {
            "created_at": now,
            "history": [],
            "query_count": 0
        }
        return self.sessions[session_id]
    
    def add_history(self, session_id: str, query: str, response: Dict):
        """添加对话历史"""
        session = self.get_or_create(session_id)
        session["history"].append({
            "query": query,
            "response": response,
            "timestamp": datetime.now()
        })
        # 保留最近 N 条
        if len(session["history"]) > self.max_history:
            session["history"] = session["history"][-self.max_history:]
        session["query_count"] += 1
    
    def get_context(self, session_id: str) -> List[Dict]:
        """获取会话上下文"""
        session = self.get_or_create(session_id)
        return session["history"][-5:]  # 最近 5 条

# 全局会话管理器
session_manager = SessionManager()
```

---

### 3. 智能路由优化（增强）

**QQBot 参考**：
```javascript
// 根据消息类型路由
if (message.type === 'text') {
    await this.handleTextMessage(message);
} else if (message.type === 'image') {
    await this.handleImageMessage(message);
}
```

**智能问数 v3 实现**：
```python
# 查询类型分类器
QUERY_PATTERNS = {
    'sales': ['销售', '销售额', '订单', '成交'],
    'customer': ['客户', '回款', '付款', '收款'],
    'inventory': ['库存', '存货', '仓库'],
    'trend': ['趋势', '走势', '变化', '对比'],
    'analysis': ['分析', '为什么', '原因', '建议']
}

def classify_query(query: str) -> str:
    """查询分类"""
    for category, keywords in QUERY_PATTERNS.items():
        if any(kw in query for kw in keywords):
            return category
    return 'general'

# 在路由中使用
query_type = classify_query(request.query)
if query_type in ['analysis', 'trend']:
    # 复杂查询：使用 AI 分析
    result = await call_dashscope(request.query)
else:
    # 简单查询：使用 v2
    result = await query_v2(request.query)
```

---

### 4. 响应格式化（增强）

**QQBot 参考**：
```javascript
// 格式化响应
const response = {
    success: true,
    data: {
        type: 'text',
        content: message,
        attachments: []
    },
    timestamp: Date.now()
};
```

**智能问数 v3 实现**：
```python
def format_response(result: Dict, query_type: str) -> AgentQueryResponse:
    """格式化响应"""
    
    # 添加元数据
    metadata = {
        "query_type": query_type,
        "processing_time_ms": result.get("processing_time_ms", 0),
        "data_source": result.get("data_source", "neo4j"),
        "cache_hit": result.get("cache_hit", False)
    }
    
    return AgentQueryResponse(
        success=result["success"],
        answer=result["answer"],
        reasoning_process=result.get("reasoning_process", []),
        data_type=result.get("data_type"),
        data=result.get("data"),
        chart_config=result.get("chart_config"),
        follow_up=result.get("follow_up", []),
        metadata=metadata,  # 新增元数据
        session_id=result.get("session_id"),
        timestamp=datetime.now()
    )
```

---

### 5. 错误处理（增强）

**QQBot 参考**：
```javascript
// 错误处理和重试
try {
    await this.processMessage(message);
} catch (error) {
    logger.error('Message processing failed', error);
    await this.sendErrorReply(message, error);
}
```

**智能问数 v3 实现**：
```python
from functools import wraps
import time

def retry_on_failure(max_attempts: int = 3, delay: float = 1.0):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    logger.warning(f"Attempt {attempt + 1} failed: {e}")
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator

@retry_on_failure(max_attempts=3, delay=0.5)
async def smart_query(request: QueryRequest):
    """智能查询（带重试）"""
    # ... 实现
```

---

## 📊 优化对比

| 特性 | 优化前 | 优化后 |
|------|--------|--------|
| **并发处理** | ❌ 无队列 | ✅ 异步队列 |
| **会话管理** | ⚠️ 基础 | ✅ TTL+ 历史记录 |
| **查询分类** | ❌ 无 | ✅ 5 类分类器 |
| **响应元数据** | ❌ 无 | ✅ 完整元数据 |
| **错误重试** | ❌ 无 | ✅ 3 次重试 |
| **日志追踪** | ⚠️ 基础 | ✅ 完整追踪 |

---

## 📝 实施计划

### 阶段 1：会话管理（今天）
- [ ] 实现 SessionManager
- [ ] 添加 TTL 过期
- [ ] 历史记录管理

### 阶段 2：查询队列（明天）
- [ ] 实现 QueryQueue
- [ ] 并发控制
- [ ] 优先级队列

### 阶段 3：智能分类（后天）
- [ ] 实现 classify_query
- [ ] 查询模式匹配
- [ ] 路由优化

### 阶段 4：监控日志（下周）
- [ ] 添加追踪 ID
- [ ] 性能监控
- [ ] 错误告警

---

**优化设计时间**: 2026-04-12 22:58  
**执行者**: CodeMaster  
**状态**: 设计完成，准备实施
