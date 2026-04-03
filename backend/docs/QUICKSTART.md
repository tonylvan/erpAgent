# GSD 后端 API 快速启动指南

## 1. 环境准备

```powershell
# 进入后端目录
cd D:\erpAgent\backend

# 激活虚拟环境
.\venv\Scripts\Activate.ps1
```

## 2. 配置环境变量

```powershell
# 复制配置模板
cp .env.example .env

# 编辑 .env 文件，填写以下必填项:
# - NEO4J_PASSWORD (Neo4j 数据库密码)
# - POSTGRES_PASSWORD (PostgreSQL 数据库密码)
# - JWT_SECRET_KEY (生产环境务必修改)
```

## 3. 启动开发服务器

```powershell
# 方式 1: 使用 uvicorn (推荐)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 方式 2: 使用 Python
python -m uvicorn app.main:app --reload
```

## 4. 验证服务

打开浏览器访问:
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

## 5. 测试 API

### 登录获取 Token

```powershell
curl -X POST "http://localhost:8000/api/v1/auth/login" `
  -H "Content-Type: application/json" `
  -d '{"username": "admin", "password": "admin123"}'
```

### 获取表列表

```powershell
# 替换 YOUR_TOKEN 为实际 Token
curl -X GET "http://localhost:8000/api/v1/data/tables" `
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 获取图谱

```powershell
curl -X GET "http://localhost:8000/api/v1/graph/ontology?mode=schema" `
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 6. WebSocket 测试

使用浏览器控制台或 WebSocket 客户端:

```javascript
const ws = new WebSocket("ws://localhost:8000/api/v1/ws?user_id=test");

ws.onopen = () => console.log("已连接");
ws.onmessage = (e) => console.log("收到:", JSON.parse(e.data));
ws.send(JSON.stringify({ type: "ping" }));
```

## 7. 常见问题

### PostgreSQL 连接失败

确保 PostgreSQL 服务已启动:
```powershell
# Windows 服务
net start postgresql-x64-15
```

### Neo4j 连接失败

确保 Neo4j 服务已启动:
```powershell
# Neo4j 命令行
neo4j start
```

### 端口被占用

修改端口:
```powershell
uvicorn app.main:app --reload --port 8001
```

## 8. 生产部署

```powershell
# 使用 gunicorn + uvicorn workers
pip install gunicorn

gunicorn app.main:app \
  -w 4 \
  -k uvicorn.workers.UvicornWorker \
  --bind 0.0.0.0:8000 \
  --access-logfile access.log \
  --error-logfile error.log
```

---

**文档**: `D:\erpAgent\backend\docs\QUICKSTART.md`
