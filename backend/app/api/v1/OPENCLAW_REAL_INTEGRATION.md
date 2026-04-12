# 🔌 真实 OpenClaw Agent 集成

**集成时间**: 2026-04-12 11:35  
**目标**: 接入真实的 OpenClaw sessions_spawn

---

## 📊 当前状态

### v3 代码结构

```python
# smart_query_v3_agent.py
async def call_openclaw_agent(query: str, session_id: str):
    # ❌ 当前：使用 mock 响应
    agent_response = {...}
    
    # ✅ 目标：调用真实 OpenClaw
    from openclaw import sessions_spawn
    result = await sessions_spawn(...)
```

---

## 🔧 实现方案

### 方案 1：使用 sessions_send（简单）

```python
import subprocess
import json

async def call_openclaw_agent(query: str, session_id: str) -> Dict:
    """使用 OpenClaw CLI sessions_send 调用"""
    try:
        # 1. 创建或获取会话
        # 2. 发送消息到会话
        result = subprocess.run(
            ['openclaw', 'sessions_send',
             '--label', 'smart-query',
             '--message', query,
             '--timeout-seconds', '30'],
            capture_output=True,
            text=True,
            timeout=35
        )
        
        if result.returncode == 0:
            response = json.loads(result.stdout)
            return {
                "success": True,
                "answer": response.get("response", ""),
                "data_type": "text",
                "reasoning_process": []  # sessions_send 不支持推理过程
            }
    except Exception as e:
        logger.error(f"OpenClaw sessions_send failed: {e}")
    
    # 降级到 v2
    return await fallback_to_v2(query)
```

**优点**：
- ✅ 简单直接
- ✅ 无需额外配置

**缺点**：
- ❌ 无推理过程展示
- ❌ 同步阻塞（subprocess）

---

### 方案 2：使用 sessions_spawn（推荐）

```python
from openclaw.sessions import spawn

async def call_openclaw_agent(query: str, session_id: str) -> Dict:
    """使用 OpenClaw sessions_spawn 调用"""
    try:
        # 构建提示
        system_prompt = """You are an ERP data analysis expert.
Think step by step and show your reasoning process."""

        # Spawn agent
        result = await spawn(
            task=query,
            runtime="subagent",
            model="dashscope/glm-5",
            mode="run",  # One-shot
            timeout_seconds=30
        )
        
        # Parse response
        reasoning_steps = extract_reasoning(result.response)
        
        return {
            "success": True,
            "answer": result.response,
            "data_type": "text",
            "reasoning_process": reasoning_steps
        }
    except Exception as e:
        logger.error(f"OpenClaw sessions_spawn failed: {e}")
        return await fallback_to_v2(query)
```

**优点**：
- ✅ 支持推理过程
- ✅ 异步非阻塞
- ✅ 可配置模型

**缺点**：
- ❌ 需要导入 OpenClaw 内部模块
- ❌ 可能需要额外配置

---

### 方案 3：HTTP Gateway（已验证不可用）

```python
# ❌ Gateway 不支持 chat completion API
# 测试结果显示 404
```

---

## 🎯 推荐实现：方案 1 (sessions_send)

**原因**：
- ✅ 立即可用
- ✅ 无需额外依赖
- ✅ 稳定可靠

**实现步骤**：

### 1. 修改 v3 代码

```python
# smart_query_v3_agent.py
import subprocess
import json

async def call_openclaw_agent(query: str, session_id: str) -> Dict:
    """Call OpenClaw agent via sessions_send"""
    try:
        logger.info(f"[OpenClaw] Calling sessions_send for query: {query[:50]}...")
        
        # Build message with context
        message = f"""Analyze this ERP data query and provide structured response:

Query: {query}

Format your response as:
1. Key findings
2. Data analysis
3. Recommendations
"""
        
        # Call OpenClaw CLI
        result = subprocess.run(
            ['openclaw', 'sessions_send',
             '--label', 'smart-query-agent',
             '--message', message,
             '--timeout-seconds', '30'],
            capture_output=True,
            text=True,
            timeout=35
        )
        
        if result.returncode == 0:
            # Parse response
            response_text = result.stdout.strip()
            
            logger.info(f"[OpenClaw] Response received: {len(response_text)} chars")
            
            return {
                "success": True,
                "answer": response_text,
                "data_type": "text",
                "reasoning_process": [{
                    "step": 1,
                    "action": "openclaw_agent",
                    "description": "使用 OpenClaw Agent 分析查询",
                    "result": f"响应长度：{len(response_text)} 字符"
                }],
                "follow_up": [
                    "查看详细数据",
                    "导出报告",
                    "与上月对比"
                ]
            }
        else:
            logger.warning(f"[OpenClaw] sessions_send failed: {result.stderr}")
            raise Exception(result.stderr)
            
    except Exception as e:
        logger.warning(f"[OpenClaw] Failed, falling back to v2: {e}")
        # Fallback to v2 NL2Cypher
        from app.api.v1.smart_query_v2 import get_knowledge_engine
        engine = get_knowledge_engine()
        v2_response = await engine.query(query)
        
        return {
            "reasoning_steps": [{
                "step": 1,
                "action": "fallback",
                "description": "OpenClaw 调用失败，使用 Neo4j 直接查询",
                "result": "使用 v2 NL2Cypher 引擎"
            }],
            "answer": v2_response.get("answer", "查询完成"),
            "data_type": v2_response.get("data_type", "text"),
            "data": v2_response.get("data"),
            "chart_config": v2_response.get("chart_config"),
            "follow_up": v2_response.get("follow_up", [])
        }
```

### 2. 创建持久会话

```bash
# 创建智能问数专用会话
openclaw sessions_spawn --task "智能问数助手 - ERP 数据分析专家" --runtime subagent --mode session --label "smart-query-agent" --model "dashscope/glm-5"
```

### 3. 测试验证

```bash
# 测试 sessions_send
openclaw sessions_send --label "smart-query-agent" --message "本周销售情况如何？"
```

---

## 📝 实施计划

### 阶段 1：sessions_send 集成（今天）
- [ ] 修改 v3 代码实现 sessions_send 调用
- [ ] 创建持久会话
- [ ] 测试验证
- [ ] 监控日志

### 阶段 2：优化（明天）
- [ ] 添加响应解析
- [ ] 优化提示工程
- [ ] 添加缓存
- [ ] 性能调优

### 阶段 3：sessions_spawn（未来）
- [ ] 研究 sessions_spawn API
- [ ] 实现异步调用
- [ ] 支持推理过程
- [ ] 成本管控

---

**实施时间**: 2026-04-12 11:35  
**执行者**: CodeMaster  
**状态**: 准备实施
