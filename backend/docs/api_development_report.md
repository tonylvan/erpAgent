# GSD 后端 API 开发报告

**创建时间**: 2026-04-03 19:30  
**版本**: 1.0.0  
**框架**: FastAPI + WebSocket + JWT

---

## 📋 开发摘要

已完成 GSD 企业智能决策中枢平台后端 API 的核心框架开发，包括：

| 模块 | 状态 | 文件 |
|------|------|------|
| **RESTful API** | ✅ | `app/api/v1/*.py` |
| **Neo4j 图查询** | ✅ | `app/services/neo4j_*.py` |
| **PostgreSQL 数据** | ✅ | `app/services/postgres_service.py` |
| **WebSocket 推送** | ✅ | `app/websocket/server.py` |
| **JWT 认证授权** | ✅ | `app/auth/jwt.py` |

---

## 🏗️ 项目结构

```
backend/
├── app/
│   ├── api/
│   │   ├── v1/                    # API v1 路由
│   │   │   ├── __init__.py
│   │   │   ├── auth.py            # 认证授权
│   │   │   ├── data.py            # 数据查询
│   │   │   ├── graph.py           # 图查询
│   │   │   └── websocket.py       # WebSocket
│   │   ├── routes.py              # 旧版 API（兼容）
│   │   └── __init__.py
│   ├── auth/                      # 认证模块
│   │   ├── __init__.py
│   │   └── jwt.py                 # JWT 实现
│   ├── websocket/                 # WebSocket 模块
│   │   ├── __init__.py
│   │   └── server.py              # 连接管理
│   ├── services/                  # 业务服务
│   │   ├── neo4j_ontology.py      # Neo4j 本体
│   │   ├── neo4j_read.py          # Neo4j 只读查询
│   │   └── postgres_service.py    # PostgreSQL 服务
│   ├── schemas/                   # Pydantic 模型
│   │   └── intelligence.py
│   ├── models/                    # 数据模型
│   │   └── __init__.py
│   ├── intelligence/              # 智能查询
│   │   └── ...
│   ├── llm/                       # LLM 提供商
│   │   └── ...
│   ├── prompts/                   # Prompt 库
│   │   └── ...
│   └── main.py                    # 应用入口
├── docs/                          # 文档
│   └── api_development_report.md
├── .env.example                   # 环境变量模板
├── requirements.txt               # Python 依赖
└── README.md
```

---

## 🔌 API 端点

### 认证授权 (`/api/v1/auth`)

| 端点 | 方法 | 描述 | 认证 |
|------|------|------|------|
| `/login` | POST | 用户登录 | ❌ |
| `/refresh` | POST | 刷新 Token | ❌ |
| `/me` | GET | 获取当前用户 | ✅ |
| `/logout` | POST | 用户登出 | ✅ |

**测试账号**:
- 管理员：`admin` / `admin123` (roles: ["admin", "user"])
- 普通用户：`user` / `user123` (roles: ["user"])

### 数据查询 (`/api/v1/data`)

| 端点 | 方法 | 描述 | 认证 |
|------|------|------|------|
| `/tables` | GET | 获取所有表 | ✅ |
| `/tables/search` | GET | 搜索表名 | ✅ |
| `/tables/{table_name}/columns` | GET | 获取列信息 | ✅ |
| `/tables/{table_name}/data` | GET | 获取表数据 | ✅ |
| `/statistics` | GET | 数据库统计 | ✅ |

### 图查询 (`/api/v1/graph`)

| 端点 | 方法 | 描述 | 认证 |
|------|------|------|------|
| `/ontology` | GET | 获取本体图谱 | ✅ |
| `/query` | POST | 执行 Cypher 查询 | ✅ |
| `/stats` | GET | 图统计信息 | ✅ |

### WebSocket (`/api/v1/ws`)

| 端点 | 方法 | 描述 |
|------|------|------|
| `/ws` | WebSocket | 实时消息推送 |
| `/ws/stats` | GET | 连接统计 |

---

## 🔐 认证流程

### 1. 登录获取 Token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

响应:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 900
}
```

### 2. 使用 Token 访问 API

```bash
curl -X GET "http://localhost:8000/api/v1/data/tables" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

### 3. 刷新 Token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJhbGciOiJIUzI1NiIs..."}'
```

---

## 🔌 WebSocket 使用

### 连接

```javascript
const token = "eyJhbGciOiJIUzI1NiIs...";
const ws = new WebSocket(`ws://localhost:8000/api/v1/ws?token=${token}`);

ws.onopen = () => {
  console.log("WebSocket 已连接");
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log("收到消息:", message);
};
```

### 消息类型

```javascript
// 心跳
ws.send(JSON.stringify({ type: "ping" }));

// 加入房间
ws.send(JSON.stringify({
  type: "join_room",
  data: { room_id: "agent_status" }
}));

// 获取统计
ws.send(JSON.stringify({ type: "get_stats" }));
```

### 服务端推送

```python
from app.websocket.server import send_agent_status, send_notification

# 发送代理状态更新
await send_agent_status(
    user_id="admin",
    agent_name="InvoiceAgent",
    status="running",
    details={"progress": 50}
)

# 发送通知
await send_notification(
    user_id="admin",
    title="数据同步完成",
    content="已同步 150 张表",
    level="success"
)
```

---

## 📦 依赖安装

```bash
cd D:\erpAgent\backend

# 创建虚拟环境（如未创建）
python -m venv venv

# 激活虚拟环境
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

---

## 🚀 启动服务

### 1. 配置环境变量

```bash
# 复制 .env.example 为 .env
cp .env.example .env

# 编辑 .env，填写数据库密码等配置
```

### 2. 启动开发服务器

```bash
# 方式 1: 使用 uvicorn 直接启动
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 方式 2: 使用 Python 启动
python -m uvicorn app.main:app --reload
```

### 3. 访问 API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- 健康检查: http://localhost:8000/health

---

## 🧪 测试示例

### 使用 curl 测试

```bash
# 1. 登录
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'

# 2. 获取表列表（替换 TOKEN）
curl -X GET "http://localhost:8000/api/v1/data/tables" \
  -H "Authorization: Bearer TOKEN"

# 3. 获取图谱
curl -X GET "http://localhost:8000/api/v1/graph/ontology?mode=schema" \
  -H "Authorization: Bearer TOKEN"

# 4. 健康检查
curl -X GET "http://localhost:8000/health"
```

### 使用 Python 测试

```python
import httpx

# 登录
async with httpx.AsyncClient() as client:
    resp = await client.post(
        "http://localhost:8000/api/v1/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    token = resp.json()["access_token"]
    
    # 获取表列表
    resp = await client.get(
        "http://localhost:8000/api/v1/data/tables",
        headers={"Authorization": f"Bearer {token}"}
    )
    print(resp.json())
```

---

## 🔒 安全考虑

### JWT 配置

- **密钥**: 生产环境必须修改 `JWT_SECRET_KEY`
- **有效期**: Access Token 15 分钟，Refresh Token 7 天
- **算法**: HS256

### SQL 注入防护

- PostgreSQL 查询使用参数化
- WHERE 子句白名单验证
- 禁止危险关键字 (DROP, DELETE 等)

### CORS 配置

```python
allow_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
```

### 只读查询

- Neo4j 查询禁止 CREATE/DELETE/MERGE
- 默认禁止 CALL（可配置放开）

---

## 📊 性能优化

### 连接池

```python
# PostgreSQL 连接池
POSTGRES_POOL_MIN=1
POSTGRES_POOL_MAX=10

# 查询超时
timeout=30  # 秒
```

### 查询限制

```python
# Neo4j 关系限制
NEO4J_GRAPH_LIMIT=4000

# 全景节点限制
NEO4J_PANORAMA_NODE_LIMIT=8000

# 分页限制
limit: int = Query(100, ge=1, le=1000)
```

---

## 📝 待办事项

### 短期 (Week 1-2)

- [ ] PostgreSQL 表模型定义 (SQLAlchemy)
- [ ] 数据库迁移脚本 (Alembic)
- [ ] Redis Token 黑名单
- [ ] 角色权限细化 (RBAC)
- [ ] API 速率限制

### 中期 (Week 3-4)

- [ ] 财务代理 API 集成
- [ ] 异步任务队列 (Celery)
- [ ] 日志审计
- [ ] 监控告警 (Prometheus)

### 长期 (Week 5-8)

- [ ] 多租户支持
- [ ] 数据导出 (PDF/Excel)
- [ ] API 版本管理
- [ ] 灰度发布

---

## 🎯 下一步

1. **前端对接**: 前端团队可开始对接 API v1
2. **联调测试**: 前后端联调核心功能
3. **性能测试**: 压测关键接口
4. **文档完善**: 补充 API 使用示例

---

**文档路径**: `D:\erpAgent\backend\docs\api_development_report.md`

<qqfile>D:\erpAgent\backend\docs\api_development_report.md</qqfile>
