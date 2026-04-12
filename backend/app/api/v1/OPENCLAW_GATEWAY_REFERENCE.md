# 🦞 OpenClaw CLI 命令参考

## sessions_send 命令

**用途**: 向另一个可见会话发送消息

### 语法

```bash
openclaw sessions_send --label <label> --message <message>
openclaw sessions_send --session-key <key> --message <message>
```

### 参数

| 参数 | 说明 | 必需 |
|------|------|------|
| `--label` | 会话标签 | 二选一 |
| `--session-key` | 会话密钥 | 二选一 |
| `--message` | 要发送的消息 | ✅ 必需 |
| `--agent-id` | 指定 Agent ID | 可选 |
| `--timeout-seconds` | 超时时间 | 可选 |

### 示例

```bash
# 发送到标签为"smart-query"的会话
openclaw sessions_send --label "smart-query" --message "分析本周销售趋势"

# 发送到指定 session-key
openclaw sessions_send --session-key "abc123" --message "客户回款排行"

# 指定 Agent 和超时
openclaw sessions_send --label "analysis" --message "预测下月销售额" --agent-id "glm-5" --timeout-seconds 60
```

### 返回值

```json
{
  "success": true,
  "sessionKey": "abc123",
  "message": "分析本周销售趋势",
  "response": "【销售趋势深度分析】...",
  "tookSeconds": 2.3
}
```

---

## sessions_spawn 命令

**用途**: spawn 一个新的子代理会话

### 语法

```bash
openclaw sessions_spawn --task <task> --runtime subagent|acp
```

### 参数

| 参数 | 说明 | 必需 |
|------|------|------|
| `--task` | 任务描述 | ✅ 必需 |
| `--runtime` | 运行时：subagent 或 acp | ✅ 必需 |
| `--mode` | run（一次性）或 session（持久） | 可选 |
| `--model` | 模型覆盖 | 可选 |
| `--label` | 会话标签 | 可选 |
| `--thread` | 绑定到线程 | 可选 |

### 示例

```bash
# Spawn 一个子代理分析销售数据
openclaw sessions_spawn --task "分析本周销售数据并生成报告" --runtime subagent --model "dashscope/glm-5"

# Spawn 一个持久会话用于智能问数
openclaw sessions_spawn --task "智能问数助手" --runtime subagent --mode session --label "smart-query-assistant"

# Spawn ACP  harness 会话（Codex/Claude Code）
openclaw sessions_spawn --task "分析 Neo4j 知识图谱" --runtime acp --mode session
```

---

## Gateway 架构参考

### QQBot Gateway 流程

```
QQ 消息 → Gateway (50000 端口)
            ↓
    OpenClaw CLI 调用
            ↓
    sessions_send / sessions_spawn
            ↓
    Agent 处理 (GLM-5)
            ↓
    返回响应到 Gateway
            ↓
    Gateway 转发到 QQ
```

### Gateway 配置

**端口**: 50000  
**协议**: OpenAI 兼容格式  
**会话管理**: session_id 追踪  

### 请求格式

```json
{
  "model": "dashscope/glm-5",
  "messages": [
    {
      "role": "user",
      "content": "本周销售情况如何？"
    }
  ],
  "stream": false
}
```

### 响应格式

```json
{
  "id": "chatcmpl-123",
  "object": "chat.completion",
  "choices": [
    {
      "message": {
        "content": "【销售趋势深度分析】..."
      }
    }
  ]
}
```

---

## 智能问数 Gateway 集成方案

### 方案 1：直接 CLI 调用

```python
import subprocess
import json

def query_via_openclaw(query: str, session_id: str) -> Dict:
    """使用 OpenClaw CLI 调用 Agent"""
    try:
        result = subprocess.run(
            ['openclaw', 'sessions_send', 
             '--label', 'smart-query',
             '--message', query],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            response = json.loads(result.stdout)
            return {
                "success": True,
                "answer": response.get("response", ""),
                "data_type": "text"
            }
    except Exception as e:
        logger.error(f"OpenClaw CLI failed: {e}")
    
    return None
```

### 方案 2：HTTP Gateway 调用

```python
import requests

GATEWAY_URL = "http://localhost:50000/v1/chat/completions"

def query_via_gateway(query: str, session_id: str) -> Dict:
    """使用 Gateway HTTP API"""
    payload = {
        "model": "dashscope/glm-5",
        "messages": [{"role": "user", "content": query}],
        "stream": False
    }
    
    response = requests.post(GATEWAY_URL, json=payload, timeout=30)
    
    if response.status_code == 200:
        data = response.json()
        answer = data["choices"][0]["message"]["content"]
        return {
            "success": True,
            "answer": answer,
            "data_type": "text"
        }
    
    return None
```

### 方案 3：混合路由（推荐）

```python
@router.post("/query")
async def query(request: QueryRequest):
    # 检测查询复杂度
    COMPLEX_KEYWORDS = ['分析', '预测', '为什么', '如何', '评估', '建议', '深度']
    is_complex = any(kw in request.query for kw in COMPLEX_KEYWORDS)
    
    if is_complex:
        # 复杂查询：使用 OpenClaw Agent
        result = query_via_gateway(request.query, request.session_id)
        if result and result["success"]:
            return result
    
    # 简单查询：使用 NL2Cypher (v2)
    return await nl2cypher_query(request)
```

---

## 性能对比

| 方案 | 响应时间 | 成本 | 准确率 | 推荐场景 |
|------|---------|------|--------|---------|
| **v2 NL2Cypher** | 1-3 秒 | ¥0.01 | 85% | 简单数据查询 |
| **Gateway HTTP** | 3-8 秒 | ¥0.10 | 95% | 复杂分析 |
| **CLI 调用** | 5-10 秒 | ¥0.10 | 95% | 实验性 |
| **混合路由** | 1-5 秒 | ¥0.05 | 92% | **推荐** |

---

**文档更新时间**: 2026-04-12 09:50  
**参考**: QQBot Gateway + OpenClaw CLI
