# GSD 智能问数平台 - API 参考文档

**版本**: v3.5.0  
**最后更新**: 2026-04-05

---

## 📋 目录

1. [认证说明](#认证说明)
2. [智能问数 API](#智能问数-api)
3. [图谱查询 API](#图谱查询-api)
4. [数据同步 API](#数据同步-api)
5. [系统管理 API](#系统管理-api)
6. [错误码说明](#错误码说明)

---

## 认证说明

### JWT Token 认证（v4.0+）

**获取 Token**:
```http
POST /api/v4/auth/login
Content-Type: application/json

{
  "username": "admin",
  "password": "your_password"
}
```

**响应**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**使用 Token**:
```http
GET /api/v4/query
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

## 智能问数 API

### 1. 执行智能查询

**端点**: `POST /api/v4/query`

**请求**:
```json
{
  "question": "查询供应商 A 的所有未付款发票",
  "mode": "auto",  // auto | cypher | natural
  "limit": 100
}
```

**响应**:
```json
{
  "success": true,
  "data": {
    "query": "MATCH (s:Supplier {vendor_name: '供应商 A'})-[:SUPPLIES]->(i:Invoice) WHERE i.status = 'PENDING' RETURN i",
    "results": [
      {
        "invoice_id": 12345,
        "invoice_num": "INV-2026-001",
        "amount": 5000.00,
        "status": "PENDING"
      }
    ],
    "visualization": {
      "type": "table",  // table | graph | chart
      "config": {...}
    }
  },
  "execution_time": 0.234
}
```

**错误响应**:
```json
{
  "success": false,
  "error": {
    "code": "QUERY_FAILED",
    "message": "Cypher 语法错误",
    "details": "Invalid relationship type..."
  }
}
```

---

### 2. 获取追问建议

**端点**: `POST /api/v4/suggestions`

**请求**:
```json
{
  "history": [
    {"role": "user", "content": "查询供应商 A 的发票"},
    {"role": "assistant", "content": "找到 5 条记录..."}
  ]
}
```

**响应**:
```json
{
  "suggestions": [
    "查看这些发票的付款状态",
    "按金额排序",
    "查看关联的采购订单",
    "导出为 Excel"
  ]
}
```

---

### 3. 查询历史

**端点**: `GET /api/v4/history`

**参数**:
- `limit` (可选): 返回数量，默认 50
- `offset` (可选): 偏移量，默认 0

**响应**:
```json
{
  "total": 128,
  "items": [
    {
      "id": "uuid-123",
      "question": "查询供应商 A 的发票",
      "timestamp": "2026-04-05T10:30:00Z",
      "result_count": 5
    }
  ]
}
```

---

## 图谱查询 API

### 1. 获取节点列表

**端点**: `GET /api/graph/nodes`

**参数**:
- `label` (可选): 节点类型，如 `Supplier`, `Invoice`
- `limit` (可选): 返回数量，默认 100

**响应**:
```json
{
  "nodes": [
    {
      "id": "12345",
      "label": "Supplier",
      "properties": {
        "vendor_id": 1001,
        "vendor_name": "供应商 A",
        "status": "ACTIVE"
      }
    }
  ],
  "total": 5624
}
```

---

### 2. 获取关系列表

**端点**: `GET /api/graph/relationships`

**参数**:
- `type` (可选): 关系类型，如 `SUPPLIES`, `PURCHASES`
- `start_node` (可选): 起始节点 ID
- `end_node` (可选): 目标节点 ID

**响应**:
```json
{
  "relationships": [
    {
      "id": "rel-001",
      "type": "SUPPLIES",
      "start_node": "12345",
      "end_node": "67890",
      "properties": {
        "since": "2025-01-01",
        "total_amount": 50000.00
      }
    }
  ]
}
```

---

### 3. 执行 Cypher 查询

**端点**: `POST /api/graph/query`

**请求**:
```json
{
  "cypher": "MATCH (s:Supplier {vendor_id: 1001})-[:SUPPLIES]->(i:Invoice) RETURN s, i LIMIT 10",
  "include_visualization": true
}
```

**响应**:
```json
{
  "columns": ["s", "i"],
  "data": [
    {
      "s": {"id": "12345", "label": "Supplier", ...},
      "i": {"id": "67890", "label": "Invoice", ...}
    }
  ],
  "visualization": {
    "graph": {
      "nodes": [...],
      "relationships": [...]
    }
  }
}
```

---

### 4. 业务链路追踪

**端点**: `POST /api/graph/trace`

**请求**:
```json
{
  "start_node": {
    "label": "Supplier",
    "id": "1001"
  },
  "end_node": {
    "label": "Payment",
    "id": "5001"
  },
  "max_depth": 5
}
```

**响应**:
```json
{
  "paths": [
    {
      "nodes": [
        {"label": "Supplier", "id": "1001"},
        {"label": "PurchaseOrder", "id": "2001"},
        {"label": "Invoice", "id": "3001"},
        {"label": "Payment", "id": "5001"}
      ],
      "relationships": [
        {"type": "SUPPLIES"},
        {"type": "GENERATES"},
        {"type": "PAID_BY"}
      ]
    }
  ],
  "total_paths": 1
}
```

---

### 5. 获取节点详情

**端点**: `GET /api/graph/node/{node_id}`

**响应**:
```json
{
  "node": {
    "id": "12345",
    "label": "Supplier",
    "properties": {
      "vendor_id": 1001,
      "vendor_name": "供应商 A",
      "vendor_type": "制造商",
      "status": "ACTIVE",
      "credit_limit": 100000.00
    },
    "relationships": {
      "incoming": 5,
      "outgoing": 12
    },
    "statistics": {
      "total_invoices": 50,
      "total_amount": 250000.00,
      "avg_payment_days": 30
    }
  }
}
```

---

## 数据同步 API

### 1. 获取同步状态

**端点**: `GET /api/sync/status`

**响应**:
```json
{
  "rtr_status": "running",
  "last_sync": "2026-04-05T10:30:00Z",
  "pending_changes": 0,
  "sync_delay_ms": 1500,
  "statistics": {
    "total_synced": 1234,
    "today_synced": 56,
    "failed_today": 0
  }
}
```

---

### 2. 手动触发同步

**端点**: `POST /api/sync/trigger`

**请求**:
```json
{
  "table": "ap_invoices_all",
  "record_id": 12345
}
```

**响应**:
```json
{
  "success": true,
  "message": "同步任务已加入队列",
  "task_id": "task-uuid-123"
}
```

---

### 3. 获取同步日志

**端点**: `GET /api/sync/logs`

**参数**:
- `table` (可选): 表名
- `status` (可选): pending | completed | failed
- `limit` (可选): 默认 100

**响应**:
```json
{
  "logs": [
    {
      "id": 30,
      "table_name": "ap_suppliers",
      "operation": "INSERT",
      "record_id": 162063,
      "sync_time": "2026-04-05T10:02:14Z",
      "status": "completed"
    }
  ],
  "total": 156
}
```

---

## 系统管理 API

### 1. 健康检查

**端点**: `GET /api/health`

**响应**:
```json
{
  "status": "ok",
  "service": "gsd-backend",
  "version": "v3.5.0",
  "uptime": 86400,
  "dependencies": {
    "postgresql": "connected",
    "neo4j": "connected",
    "redis": "connected"
  }
}
```

---

### 2. 获取系统信息

**端点**: `GET /api/system/info`

**响应**:
```json
{
  "version": "v3.5.0",
  "build": "20260405",
  "python_version": "3.11.5",
  "node_version": "20.10.0",
  "database": {
    "postgresql": {
      "version": "15.2",
      "tables": 56,
      "records": 12000
    },
    "neo4j": {
      "version": "5.15",
      "nodes": 5624,
      "relationships": 10796
    }
  }
}
```

---

### 3. 清除缓存

**端点**: `POST /api/system/cache/clear`

**响应**:
```json
{
  "success": true,
  "message": "缓存已清除",
  "cleared_keys": 156
}
```

---

### 4. 导出配置

**端点**: `GET /api/system/config/export`

**响应**:
```json
{
  "config": {
    "database": {...},
    "rtr": {...},
    "features": {...}
  },
  "exported_at": "2026-04-05T10:30:00Z"
}
```

---

## 错误码说明

### 通用错误

| 错误码 | HTTP 状态码 | 说明 |
|--------|-----------|------|
| `SUCCESS` | 200 | 请求成功 |
| `INVALID_REQUEST` | 400 | 请求参数错误 |
| `UNAUTHORIZED` | 401 | 未授权访问 |
| `FORBIDDEN` | 403 | 权限不足 |
| `NOT_FOUND` | 404 | 资源不存在 |
| `INTERNAL_ERROR` | 500 | 服务器内部错误 |

### 查询相关错误

| 错误码 | HTTP 状态码 | 说明 |
|--------|-----------|------|
| `QUERY_FAILED` | 400 | 查询执行失败 |
| `CYPHER_SYNTAX_ERROR` | 400 | Cypher 语法错误 |
| `TIMEOUT` | 408 | 查询超时 |
| `NO_RESULTS` | 404 | 无匹配结果 |

### 同步相关错误

| 错误码 | HTTP 状态码 | 说明 |
|--------|-----------|------|
| `SYNC_FAILED` | 500 | 同步失败 |
| `CONNECTION_LOST` | 503 | 数据库连接断开 |
| `DUPLICATE_RECORD` | 409 | 重复记录 |

---

## 使用示例

### Python 示例

```python
import requests

# 认证
response = requests.post('http://localhost:8005/api/v4/auth/login', json={
    'username': 'admin',
    'password': 'password'
})
token = response.json()['access_token']

# 执行查询
headers = {'Authorization': f'Bearer {token}'}
response = requests.post('http://localhost:8005/api/v4/query', json={
    'question': '查询所有未付款的发票',
    'limit': 100
}, headers=headers)

results = response.json()['data']['results']
print(f"找到 {len(results)} 条记录")
```

### JavaScript 示例

```javascript
// 执行智能查询
const response = await fetch('http://localhost:8005/api/v4/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    question: '查询供应商 A 的发票',
    limit: 50
  })
});

const data = await response.json();
console.log(data.data.results);
```

### cURL 示例

```bash
# 健康检查
curl http://localhost:8005/api/health

# 执行查询
curl -X POST http://localhost:8005/api/v4/query \
  -H "Content-Type: application/json" \
  -d '{"question": "查询所有发票", "limit": 10}'

# 获取节点
curl "http://localhost:8005/api/graph/nodes?label=Supplier&limit=10"
```

---

## 速率限制

| 端点 | 限制 | 说明 |
|------|------|------|
| `/api/v4/query` | 100 次/分钟 | 智能查询 |
| `/api/graph/query` | 200 次/分钟 | 图谱查询 |
| `/api/sync/*` | 50 次/分钟 | 同步相关 |
| 其他端点 | 500 次/分钟 | 通用 API |

**超限响应**:
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "请求频率超限，请稍后重试",
    "retry_after": 60
  }
}
```

---

## 版本兼容性

| API 版本 | 状态 | 支持周期 |
|---------|------|---------|
| v1 | ❌ 已弃用 | 2026-06-30 |
| v2 | ⚠️ 维护中 | 2026-12-31 |
| v3 | ✅ 稳定版 | 长期支持 |
| v3.5 | ✅ 最新版 | 长期支持 |
| v4.0 | 🆕 Beta | 测试中 |

---

## 更新日志

### v3.5.0 (2026-04-05)
- ✅ 新增 RTR 同步状态 API
- ✅ 新增业务链路追踪 API
- ✅ 优化查询性能

### v3.0.0 (2026-03-25)
- ✅ 智能问数 v3 引擎
- ✅ 追问建议功能
- ✅ 查询历史功能

---

<div align="center">

**📚 API 文档完成！**

[返回 README](../README.md) | [查看部署指南](deployment.md) | [用户手册](user-guide.md)

</div>
