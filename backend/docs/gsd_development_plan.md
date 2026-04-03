# GSD 企业智能决策中枢平台 - 开发计划

**创建时间**: 2026-04-03 19:25  
**总周期**: 8 周 (2 个月)  
**Agent 数量**: 5 个并行开发

---

## 📋 项目概述

基于 erpAgent 现有成果 (150 张表 + Neo4j 图数据 + 5 大财务代理)，构建企业级智能决策中枢平台。

### 核心价值

| 能力 | 说明 |
|------|------|
| **数据整合** | PostgreSQL 150 张 Oracle EBS 表 + Neo4j 图数据 |
| **智能分析** | 5 大财务代理 (发票/付款/预测/合规/报告) |
| **实时决策** | WebSocket 推送 + 图查询加速 (8-12 倍) |
| **可视化** | 图谱浏览器 + 仪表盘 + 分析报告 |

---

## 🎯 开发计划 (P1-P4)

### Phase 1: 基础框架 (2 周)

**负责人**: Agent 1 - 基础框架  
**Session**: `agent:main:subagent:39827282-5ae6-4841-8600-e4ee912e415a`

| 任务 | 工期 | 状态 |
|------|------|------|
| 项目初始化 (Vite + React + TS) | 2 天 | ⏳ |
| UI 组件库集成 (Ant Design) | 2 天 | ⏳ |
| 路由配置 (React Router) | 1 天 | ⏳ |
| 状态管理 (Zustand) | 2 天 | ⏳ |
| API 客户端 (Axios) | 1 天 | ⏳ |
| 基础布局组件 | 2 天 | ⏳ |

**交付物**:
- `frontend-gsd/package.json`
- `frontend-gsd/src/main.tsx`
- `frontend-gsd/src/App.tsx`
- `frontend-gsd/src/router/index.tsx`
- `frontend-gsd/src/store/index.ts`
- `frontend-gsd/src/api/client.ts`

---

### Phase 2: 核心页面 (3 周)

**负责人**: Agent 2 - 核心页面  
**Session**: `agent:main:subagent:4fb5e884-d4bb-4612-b934-8b4809f418e7`

| 任务 | 工期 | 状态 |
|------|------|------|
| 仪表盘开发 (Dashboard) | 3 天 | ⏳ |
| 图谱浏览器 (集成 G6) | 5 天 | ⏳ |
| 代理中心 (Agent Hub) | 3 天 | ⏳ |
| 问题数据列表 | 2 天 | ⏳ |
| 页面联调 | 2 天 | ⏳ |

**交付物**:
- `frontend-gsd/src/pages/Dashboard.tsx`
- `frontend-gsd/src/pages/GraphBrowser.tsx`
- `frontend-gsd/src/pages/AgentHub.tsx`
- `frontend-gsd/src/pages/ProblemData.tsx`
- `frontend-gsd/src/components/graph/G6Viewer.tsx`

---

### Phase 3: 功能完善 (2 周)

**负责人**: Agent 3 - 功能完善  
**Session**: `agent:main:subagent:d498977c-39ee-44ef-8e04-f42bc35f9ae1`

| 任务 | 工期 | 状态 |
|------|------|------|
| 分析报告页 | 2 天 | ⏳ |
| 图表组件 (ECharts) | 3 天 | ⏳ |
| 实时推送 (WebSocket) | 2 天 | ⏳ |
| 导出功能 (PDF/Excel) | 2 天 | ⏳ |
| 性能优化 | 1 天 | ⏳ |

**交付物**:
- `frontend-gsd/src/pages/Reports.tsx`
- `frontend-gsd/src/components/charts/EChartsWrapper.tsx`
- `frontend-gsd/src/hooks/useWebSocket.ts`
- `frontend-gsd/src/utils/export.ts`

---

### Phase 4: 测试部署 (1 周)

**负责人**: Agent 4 - 测试部署  
**Session**: `agent:main:subagent:d62b1490-e548-4e9d-8202-2796e51bd4e0`

| 任务 | 工期 | 状态 |
|------|------|------|
| 单元测试 (Vitest) | 2 天 | ⏳ |
| E2E 测试 (Playwright) | 2 天 | ⏳ |
| Docker 容器化 | 1 天 | ⏳ |
| CI/CD 配置 | 1 天 | ⏳ |
| 生产环境部署 | 1 天 | ⏳ |

**交付物**:
- `frontend-gsd/vitest.config.ts`
- `frontend-gsd/tests/e2e/*.spec.ts`
- `Dockerfile`
- `docker-compose.yml`
- `.github/workflows/ci.yml`

---

### Backend API: 后端服务 (并行)

**负责人**: Agent 5 - 后端 API  
**Session**: `agent:main:subagent:a434f47f-7ff8-403a-8016-804b51492713`

| 任务 | 工期 | 状态 |
|------|------|------|
| RESTful API 设计 (FastAPI) | 2 天 | ⏳ |
| Neo4j 图查询接口 | 3 天 | ⏳ |
| PostgreSQL 数据接口 | 2 天 | ⏳ |
| WebSocket 实时推送 | 2 天 | ⏳ |
| JWT 认证授权 | 1 天 | ⏳ |

**交付物**:
- `backend-gsd/main.py`
- `backend-gsd/api/v1/*.py`
- `backend-gsd/services/neo4j_service.py`
- `backend-gsd/services/postgres_service.py`
- `backend-gsd/websocket/server.py`
- `backend-gsd/auth/jwt.py`

---

## 📊 技术架构

```
┌─────────────────────────────────────────────────┐
│              GSD 决策中枢平台                      │
├─────────────────────────────────────────────────┤
│  Frontend (React + TS + AntD)                   │
│  ├── Dashboard (仪表盘)                          │
│  ├── Graph Browser (图谱浏览器 - G6)              │
│  ├── Agent Hub (代理中心)                        │
│  ├── Reports (分析报告)                          │
│  └── Problem Data (问题数据)                     │
├─────────────────────────────────────────────────┤
│  Backend (FastAPI + WebSocket)                  │
│  ├── RESTful API (v1)                           │
│  ├── Neo4j Service (图查询)                      │
│  ├── PostgreSQL Service (关系型数据)              │
│  ├── Financial Agents (5 大财务代理)              │
│  └── Auth (JWT)                                 │
├─────────────────────────────────────────────────┤
│  Data Layer                                     │
│  ├── PostgreSQL (150 张 Oracle EBS 表)            │
│  └── Neo4j (5,654 节点 / 10,796 关系)             │
└─────────────────────────────────────────────────┘
```

---

## 🎯 性能指标

| 指标 | 目标 | 测量方法 |
|------|------|---------|
| 首屏加载 | < 2s | Lighthouse |
| 图表渲染 | < 500ms | Performance API |
| 图查询响应 | < 1s | Neo4j Query Log |
| 代理状态更新 | 实时 (<100ms) | WebSocket |
| Lighthouse 评分 | > 90 | Lighthouse CI |

---

## 🔐 安全考虑

### 认证授权
- JWT Token (15 分钟有效期)
- Refresh Token (7 天)
- RBAC 角色权限控制
- API 速率限制

### 数据安全
- HTTPS 强制
- SQL 注入防护
- XSS 防护
- CORS 配置

---

## 📅 里程碑

| 时间 | 里程碑 | 交付物 |
|------|--------|--------|
| **Week 2** | Phase 1 完成 | 基础框架可运行 |
| **Week 5** | Phase 2 完成 | 核心页面可用 |
| **Week 7** | Phase 3 完成 | 功能完善 |
| **Week 8** | Phase 4 完成 | 生产部署 |

---

## 👥 Agent 分工

| Agent | 职责 | Session Key |
|-------|------|-------------|
| **Agent 1** | 基础框架 | `39827282-5ae6-4841-8600-e4ee912e415a` |
| **Agent 2** | 核心页面 | `4fb5e884-d4bb-4612-b934-8b4809f418e7` |
| **Agent 3** | 功能完善 | `d498977c-39ee-44ef-8e04-f42bc35f9ae1` |
| **Agent 4** | 测试部署 | `d62b1490-e548-4e9d-8202-2796e51bd4e0` |
| **Agent 5** | 后端 API | `a434f47f-7ff8-403a-8016-804b51492713` |

---

**文档路径**: `D:\erpAgent\backend\docs\gsd_development_plan.md`

<qqfile>D:\erpAgent\backend\docs\gsd_development_plan.md</qqfile>
