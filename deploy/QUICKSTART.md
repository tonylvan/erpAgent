# GSD 快速启动指南

## 🚀 一键启动所有服务

### 方法 1: PowerShell 脚本 (推荐)

```powershell
# 打开 PowerShell，执行：
cd D:\erpAgent\deploy
.\deploy.ps1
```

### 方法 2: 手动启动

```bash
# 1. 初始化 Neo4j 数据 (首次运行需要)
cd D:\erpAgent
python scripts\init_financial_risk_data.py

# 2. 启动后端 (终端 1)
cd D:\erpAgent\backend
uvicorn app.main:app --reload --port 8005

# 3. 启动前端 (终端 2)
cd D:\erpAgent\frontend
npm run dev
```

### 方法 3: 批处理脚本

```bash
# 双击运行
D:\erpAgent\deploy\deploy.bat
```

---

## 📊 访问地址

启动后访问：

| 服务 | 地址 | 说明 |
|------|------|------|
| **前端** | http://localhost:5177 | 主界面 |
| **后端 API** | http://localhost:8005 | API 服务 |
| **Swagger UI** | http://localhost:8005/docs | API 文档 |
| **预警中心** | http://localhost:5177 | 预警看板 |
| **财务风险** | http://localhost:5177 | 财务风险看板 |

---

## 🧪 运行测试

```bash
# 后端测试
cd D:\erpAgent\backend
pytest tests/ -v --cov=app --cov-report=html

# 前端测试
cd D:\erpAgent\frontend
npm run test:unit

# E2E 测试
npm run test:e2e

# 性能测试
locust -f tests/performance/locustfile.py --host=http://localhost:8005
```

---

## 📁 项目结构

```
D:\erpAgent/
├── backend/              # 后端服务
│   ├── app/
│   │   ├── services/     # 业务服务
│   │   ├── api/v1/       # API 路由
│   │   └── models/       # 数据模型
│   └── tests/            # 测试文件
├── frontend/             # 前端服务
│   ├── src/
│   │   ├── views/        # 页面组件
│   │   └── api/          # API 模块
│   └── tests/            # 测试文件
├── deploy/               # 部署脚本
│   ├── deploy.ps1        # PowerShell 部署
│   ├── deploy.bat        # 批处理部署
│   └── init_neo4j.bat    # Neo4j 初始化
├── docs/                 # 文档
└── scripts/              # 工具脚本
```

---

## ⚠️ 常见问题

### Q: 端口被占用怎么办？
A: 修改端口号
```bash
# 后端改用 8006 端口
uvicorn app.main:app --reload --port 8006

# 前端改用 5178 端口
npm run dev -- --port 5178
```

### Q: Neo4j 连接失败？
A: 检查 Neo4j 服务是否运行
```bash
# Windows 服务
net start neo4j

# 或者重启 Neo4j
net stop neo4j
net start neo4j
```

### Q: 前端依赖缺失？
A: 重新安装依赖
```bash
cd D:\erpAgent\frontend
npm install
```

### Q: 后端依赖缺失？
A: 重新安装依赖
```bash
cd D:\erpAgent\backend
pip install -r requirements.txt
```

---

## 📝 测试账号

| 角色 | 用户名 | 密码 | 权限 |
|------|--------|------|------|
| 管理员 | admin | admin123 | 全部权限 |
| 普通用户 | user | user123 | 查询权限 |

---

## 🎯 功能模块

1. **预警中心** - 企业风险预警和监控
2. **问题追踪** - 问题发现到闭环全流程
3. **决策支持** - 5 大决策场景分析
4. **财务风险** - 财务健康度评估和预测

---

**部署完成后，访问 http://localhost:5177 开始使用！** 🚀
