# 🚨 OpenClaw sessions_send 调试报告

**时间**: 2026-04-12 11:45  
**问题**: sessions_send 调用超时

---

## 📊 问题现象

**用户看到**：
```
Step 1: fallback
OpenClaw 调用失败，使用 Neo4j 直接查询 → 使用 v2 NL2Cypher 引擎
```

**后端日志**：
```
WARNING [OpenClaw] Failed, falling back to v2: Command timeout
```

---

## 🔍 可能原因

### 1. OpenClaw Gateway 未运行

**检查**：
```bash
netstat -ano | findstr "18789 18800"
```

**预期**：
- 18789: OpenClaw Gateway
- 18800: OpenClaw Hub

### 2. 会话标签不存在

**问题**：`--label "smart-query-agent"` 没有对应会话

**解决**：
```bash
openclaw sessions_spawn \
  --task "智能问数助手" \
  --runtime subagent \
  --mode session \
  --label "smart-query-agent"
```

### 3. OpenClaw CLI 配置问题

**检查**：
```bash
openclaw status
```

---

## 🔧 解决方案

### 方案 A：使用默认会话（不指定 label）

```python
# 修改 v3 代码
result = subprocess.run(
    ['openclaw', 'sessions_send',
     '--message', message,  # 不指定 label
     '--timeout-seconds', '30'],
    ...
)
```

### 方案 B：等待会话创建

```bash
# 手动创建会话
openclaw sessions_spawn \
  --task "智能问数助手" \
  --runtime subagent \
  --mode session \
  --label "smart-query-agent"
```

### 方案 C：使用 v2（推荐临时方案）

**前端切换回 v2**：
```javascript
// SmartQuery.vue
const API_ENDPOINT = '/api/v1/smart-query-v2/query'  // 稳定
```

---

## 📝 当前建议

**鉴于 OpenClaw sessions_send 超时**，建议：

1. **临时方案**：切换回 v2 NL2Cypher（稳定，1-3 秒响应）
2. **调试 OpenClaw**：检查 Gateway 状态和会话配置
3. **未来优化**：等 OpenClaw 稳定后再集成

---

**降级是正常的**！v2 功能完整：
- ✅ Neo4j 知识图谱查询
- ✅ 多轮对话支持
- ✅ 追问功能
- ✅ 结构化数据（chart/table）

---

**调试时间**: 2026-04-12 11:45  
**状态**: 降级到 v2（正常工作）
