# GSD 企业智能决策中枢平台 - 后端 API

**版本**: 1.0.0  
**框架**: FastAPI + WebSocket + JWT  
**Python**: 3.10+

---

## 🚀 快速开始

### 1. 安装依赖

```bash
cd D:\erpAgent\backend
pip install -r requirements.txt
```

### 2. 配置环境

```bash
# 复制配置模板
cp .env.example .env

# 编辑 .env，填写数据库配置
```

### 3. 启动服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 访问文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## 📚 API 文档

### 认证授权 (`/api/v1/auth`)

| 端点 | 方法 | 描述 |
|------|------|------|
| `/login` | POST | 用户登录 |
| `/refresh` | POST | 刷新 Token |
| `/me` | GET | 获取当前用户 |
| `/logout` | POST | 用户登出 |

**测试账号**:
- 管理员：`admin` / `admin123`
- 普通用户：`user` / `user123`

### 数据查询 (`/api/v1/data`)

| 端点 | 方法 | 描述 |
|------|------|------|
| `/tables` | GET | 获取所有表 |
| `/tables/search` | GET | 搜索表名 |
| `/tables/{table_name}/columns` | GET | 获取列信息 |
| `/tables/{table_name}/data` | GET | 获取表数据 |
| `/statistics` | GET | 数据库统计 |

### 图查询 (`/api/v1/graph`)

| 端点 | 方法 | 描述 |
|------|------|------|
| `/ontology` | GET | 获取本体图谱 |
| `/query` | POST | 执行 Cypher 查询 |
| `/stats` | GET | 图统计信息 |

### WebSocket (`/api/v1/ws`)

| 端点 | 方法 | 描述 |
|------|------|------|
| `/ws` | WebSocket | 实时消息推送 |
| `/ws/stats` | GET | 连接统计 |

---

## 🔐 认证流程

### 1. 登录

```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### 2. 使用 Token

```bash
curl -X GET "http://localhost:8000/api/v1/data/tables" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 3. 刷新 Token

```bash
curl -X POST "http://localhost:8000/api/v1/auth/refresh" \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

---

## 🔌 WebSocket 使用

### JavaScript 示例

```javascript
const ws = new WebSocket("ws://localhost:8000/api/v1/ws?token=YOUR_TOKEN");

ws.onopen = () => {
  console.log("已连接");
  // 加入房间
  ws.send(JSON.stringify({
    type: "join_room",
    data: { room_id: "agent_status" }
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log("收到:", message);
};
```

### Python 示例

```python
import asyncio
import websockets

async def connect():
    async with websockets.connect(
        "ws://localhost:8000/api/v1/ws?token=YOUR_TOKEN"
    ) as ws:
        await ws.send('{"type": "ping"}')
        response = await ws.recv()
        print(f"收到：{response}")

asyncio.run(connect())
```

---

## 📦 项目结构

```
backend/
├── app/
│   ├── api/
│   │   ├── v1/           # API v1 路由
│   │   └── routes.py     # 旧版 API
│   ├── auth/             # 认证模块
│   ├── websocket/        # WebSocket 模块
│   ├── services/         # 业务服务
│   ├── schemas/          # Pydantic 模型
│   └── main.py           # 应用入口
├── docs/                 # 文档
├── .env.example          # 环境变量模板
├── requirements.txt      # Python 依赖
└── README.md
```

---

## 🧪 测试

### 运行测试脚本

```bash
python test_api.py
```

### 手动测试

```bash
# 健康检查
curl http://localhost:8000/health

# 登录
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'

# 获取表列表
curl http://localhost:8000/api/v1/data/tables \
  -H "Authorization: Bearer YOUR_TOKEN"
```

---

## 🔒 安全配置

### JWT 密钥

生产环境务必修改 `.env` 中的 `JWT_SECRET_KEY`:

```bash
# 生成随机密钥
openssl rand -hex 32
```

### CORS 配置

```env
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### 数据库连接

```env
# Neo4j
NEO4J_URI=bolt://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# PostgreSQL
POSTGRES_HOST=127.0.0.1
POSTGRES_PORT=5432
POSTGRES_DB=erpagent
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
```

---

## 📊 性能优化

### 连接池

```env
POSTGRES_POOL_MIN=1
POSTGRES_POOL_MAX=10
```

### 查询限制

```env
NEO4J_GRAPH_LIMIT=4000
NEO4J_PANORAMA_NODE_LIMIT=8000
```

---

## 📝 开发日志

### 2026-04-03

**完成内容**:
- ✅ RESTful API 设计 (FastAPI)
- ✅ Neo4j 图查询接口
- ✅ PostgreSQL 数据接口
- ✅ WebSocket 实时推送
- ✅ JWT 认证授权

**新增文件**:
- `app/api/v1/*.py` - API v1 路由
- `app/auth/jwt.py` - JWT 认证
- `app/websocket/server.py` - WebSocket 服务
- `app/services/postgres_service.py` - PostgreSQL 服务
- `docs/api_development_report.md` - 开发报告
- `docs/QUICKSTART.md` - 快速启动指南
- `test_api.py` - 测试脚本

**依赖更新**:
- `psycopg2-binary>=2.9.9` - PostgreSQL 驱动
- `PyJWT>=2.8.0` - JWT 实现

---

## 🤝 贡献

1. Fork 项目
2. 创建特性分支
3. 提交变更
4. 推送到分支
5. 创建 Pull Request

---

## 📄 许可证

MIT License

---

**项目路径**: `D:\erpAgent\backend`  
**文档**: `docs/README.md`
