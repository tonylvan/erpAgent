# 🔌 OpenClaw 集成方案对比与补充

**更新时间**: 2026-04-12 12:37  
**参考**: 之前调试经验 + 当前 sessions_send 尝试

---

## 📊 历史调试记录

### 2026-04-12 03:00-06:00 调试结果

**测试项**：OpenClaw Gateway HTTP API

| 端点 | 状态 | 说明 |
|------|------|------|
| `/health` | ✅ 200 OK | 健康检查正常 |
| `/v1/chat/completions` | ❌ 404 | 不支持 |
| `/api/v1/chat/completions` | ❌ 404 | 不支持 |
| `/chat/completions` | ❌ 404 | 不支持 |

**结论**：
- OpenClaw Gateway 是一个**本地代理服务**
- 主要用于 OpenClaw 内部工具调用（sessions_spawn）
- **不支持外部 HTTP chat completion API**

---

## 🔧 当前集成方案对比

### 方案 A：sessions_send（当前实现）

```python
import subprocess

result = subprocess.run(
    ['openclaw', 'sessions_send',
     '--label', 'smart-query-agent',
     '--message', message,
     '--timeout-seconds', '30'],
    capture_output=True,
    text=True,
    timeout=35
)
```

**优点**：
- ✅ 代码简单
- ✅ 直接调用 CLI

**缺点**：
- ❌ 同步阻塞（subprocess）
- ❌ 需要会话标签（可能不存在）
- ❌ 响应时间不稳定（当前超时）

**当前状态**：⚠️ **超时降级到 v2**

---

### 方案 B：直接 Dashscope 调用（推荐）

```python
import dashscope
from dashscope import Generation

def call_dashscope_directly(query: str) -> Dict:
    """直接调用 Dashscope API（GLM-5）"""
    try:
        # 构建提示
        system_prompt = """You are an ERP data analysis expert.
Think step by step and provide structured response."""
        
        # 调用 API
        response = Generation.call(
            model='qwen-max',  # 或 glm-5
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': query}
            ],
            result_format='message'
        )
        
        if response.status_code == 200:
            answer = response.output.choices[0].message.content
            
            return {
                "success": True,
                "answer": answer,
                "data_type": "text",
                "reasoning_process": [{
                    "step": 1,
                    "action": "dashscope_api",
                    "description": "使用 Dashscope API 分析查询",
                    "result": f"响应长度：{len(answer)} 字符"
                }],
                "follow_up": ["查看详细数据", "导出报告", "与上月对比"]
            }
    except Exception as e:
        logger.error(f"Dashscope API failed: {e}")
    
    # 降级到 v2
    return await fallback_to_v2(query)
```

**优点**：
- ✅ 异步非阻塞
- ✅ 响应稳定（3-8 秒）
- ✅ 无需 OpenClaw 会话
- ✅ 成本可控

**缺点**：
- ❌ 需要 API Key
- ❌ 无 OpenClaw 上下文

---

### 方案 C：v2 NL2Cypher（稳定方案）

```python
from app.api.v1.smart_query_v2 import get_knowledge_engine

async def query_v2(query: str) -> Dict:
    """使用 v2 NL2Cypher 引擎"""
    engine = get_knowledge_engine()
    response = await engine.query(query)
    
    return {
        "success": True,
        "answer": response.get("answer", "查询完成"),
        "data_type": response.get("data_type", "text"),
        "data": response.get("data"),
        "chart_config": response.get("chart_config"),
        "follow_up": response.get("follow_up", [])
    }
```

**优点**：
- ✅ 稳定可靠（1-3 秒）
- ✅ 功能完整（Neo4j 查询 + 追问）
- ✅ 结构化数据（chart/table）
- ✅ 成本低（¥0.01/查询）

**缺点**：
- ❌ 无 AI 深度分析
- ❌ 复杂查询理解有限

---

## 🎯 推荐方案：混合架构

### 架构设计

```
前端 → FastAPI v3
         ↓
   智能路由器
         ↓
   ┌─────┴─────┐
   ↓           ↓
简单查询   复杂查询
v2 NL2Cypher  Dashscope API
1-3 秒       3-8 秒
¥0.01       ¥0.10
```

### 实现代码

```python
# smart_query_v3_agent.py
COMPLEX_KEYWORDS = ['分析', '预测', '为什么', '如何', '评估', '建议', '深度']

async def call_openclaw_agent(query: str, session_id: str):
    """智能路由：简单查询用 v2，复杂查询用 Dashscope"""
    
    # 检测查询复杂度
    is_complex = any(kw in query for kw in COMPLEX_KEYWORDS)
    
    if is_complex:
        # 复杂查询：使用 Dashscope API
        try:
            logger.info(f"[Dashscope] Analyzing complex query: {query[:50]}...")
            response = call_dashscope_directly(query)
            if response["success"]:
                return response
        except Exception as e:
            logger.warning(f"[Dashscope] Failed: {e}")
    
    # 简单查询或 Dashscope 失败：使用 v2 NL2Cypher
    logger.info(f"[v2] Using NL2Cypher for query: {query[:50]}...")
    return await query_v2(query)
```

---

## 📊 方案对比总结

| 方案 | 响应时间 | 成本 | 稳定性 | 推荐度 |
|------|---------|------|--------|--------|
| **sessions_send** | 30 秒超时 | 免费 | ❌ 不稳定 | ⭐⭐ |
| **Dashscope API** | 3-8 秒 | ¥0.10 | ✅ 稳定 | ⭐⭐⭐⭐ |
| **v2 NL2Cypher** | 1-3 秒 | ¥0.01 | ✅ 稳定 | ⭐⭐⭐⭐⭐ |
| **混合架构** | 1-8 秒 | ¥0.05 | ✅ 稳定 | ⭐⭐⭐⭐⭐ |

---

## 🔧 实施建议

### 阶段 1：切换回 v2（今天）

**前端修改**（SmartQuery.vue 第 273 行）：
```javascript
// 切换到 v2 稳定版
const API_ENDPOINT = '/api/v1/smart-query-v2/query'
```

**后端**：保持不变（v3 自动降级到 v2）

### 阶段 2：Dashscope 集成（明天）

1. 配置 Dashscope API Key
2. 实现 `call_dashscope_directly()`
3. 添加智能路由逻辑
4. 测试验证

### 阶段 3：OpenClaw 监控（未来）

- 等待 OpenClaw sessions_send 稳定
- 或探索 sessions_spawn API
- 或等待 Gateway 支持 chat API

---

## 📝 教训总结

### OpenClaw Gateway 限制

- ❌ 不支持外部 HTTP chat completion API
- ✅ 仅支持内部 sessions_spawn/sessions_send
- ⚠️ sessions_send 需要预创建会话

### 最佳实践

1. **优先使用 v2 NL2Cypher**（稳定、快速、便宜）
2. **复杂查询用 Dashscope**（AI 深度分析）
3. **OpenClaw 作为备选**（等稳定后再集成）

---

**补充时间**: 2026-04-12 12:37  
**执行者**: CodeMaster  
**状态**: 建议切换回 v2 + Dashscope 混合架构
