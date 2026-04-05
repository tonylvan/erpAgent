# GSD 智能问数集成指南

> **完成时间**: 2026-04-05  
> **集成方式**: 直接复制 GSD 平台组件 + 本地适配

---

## 📊 已完成的工作

### 1. ERP 知识图谱文档 ✅

**文件**: `docs/ERP 知识图谱.md`

**内容**:
- Neo4j 节点统计 (672 个节点，47 种标签)
- 关系类型 (32 种，1149 条关系)
- 核心业务模块 (PTP/OTC/财务/时间)
- 典型查询示例
- RTR 实时同步状态

### 2. SmartQuery 组件复制 ✅

**源文件**: 
- `C:\Users\Administrator\.openclaw\workspace\gsd-platform\frontend\src\views\SmartQuery.vue`

**目标文件**:
- `D:\erpAgent\frontend\src\views\SmartQuery.vue` (完整版)
- `D:\erpAgent\frontend\src\views\SmartQueryView.vue` (简化版)

### 3. 后端 API 就绪 ✅

**已有 API 版本**:
- `/api/v1/smart-query/query` (v1)
- `/api/v1/smart-query-v2/query` (v2)
- `/api/v1/smart-query-v40/query` (v4.0 - 推荐)

**后端位置**: `D:\erpAgent\backend\app\api\v1\smart_query*.py`

---

## 🚀 快速集成方案（2 种）

### 方案 A: 使用简化版 SmartQueryView（推荐）⭐

**特点**: 
- ✅ 简单快速 (5 分钟完成)
- ✅ 使用现有 ResultPanel 组件
- ✅ 独立页面，不影响现有功能

**步骤**:

1. **添加路由** - 编辑 `D:\erpAgent\frontend\src\App.vue`

```vue
<script setup>
import { ref } from "vue";
import SmartQueryView from "./views/SmartQueryView.vue";

const showSmartQuery = ref(false);
</script>

<template>
  <div v-if="showSmartQuery">
    <SmartQueryView />
  </div>
  <div v-else>
    <!-- 原有内容 -->
  </div>
</template>
```

2. **添加入口按钮** - 在现有界面添加导航

```vue
<el-button type="primary" @click="showSmartQuery = true">
  📊 智能问数
</el-button>
```

3. **重启前端**

```bash
cd D:\erpAgent\frontend
npm run dev
```

4. **访问**: `http://localhost:5176/smart-query`

---

### 方案 B: 使用完整版 SmartQuery + 路由

**特点**:
- ✅ 功能完整 (包含收藏/历史/点踩)
- ✅ 独立路由导航
- ⚠️ 需要配置 Vue Router

**步骤**:

1. **安装 Vue Router** (如果未安装)

```bash
cd D:\erpAgent\frontend
npm install vue-router@4
```

2. **创建路由配置**

文件：`src/router/index.js`

```javascript
import { createRouter, createWebHistory } from 'vue-router'
import SmartQuery from '../views/SmartQuery.vue'
import App from '../App.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: App
  },
  {
    path: '/smart-query',
    name: 'SmartQuery',
    component: SmartQuery
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
```

3. **修改 main.js**

```javascript
import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";

const app = createApp(App);
app.use(router);
app.mount("#app");
```

4. **重启前端**

```bash
npm run dev
```

5. **访问**: `http://localhost:5176/smart-query`

---

## 📋 API 配置说明

### 后端 API 端点

**推荐版本**: `smart_query_v40.py`

**端点**: `POST /api/v1/smart-query-v40/query`

**请求格式**:
```json
{
  "query": "查询本月销售趋势",
  "session_id": "user-123"
}
```

**响应格式**:
```json
{
  "answer": "本月销售总额为 123.4 万元...",
  "cypher": "MATCH (s:Sale)...",
  "records": [...],
  "process": [
    {"title": "解析查询", "detail": "..."},
    {"title": "生成 Cypher", "detail": "..."}
  ],
  "meta": {
    "type": "chart",
    "chart_type": "line"
  }
}
```

### 前端 API 调用

文件：`src/api/smartQuery.js`

```javascript
export async function postSmartQuery(query, sessionId) {
  const response = await fetch('http://localhost:8005/api/v1/smart-query-v40/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query,
      session_id: sessionId
    })
  })
  
  if (!response.ok) {
    throw new Error(`HTTP ${response.status}: ${response.statusText}`)
  }
  
  return await response.json()
}
```

---

## 🎯 功能对比

| 功能 | GSD 平台 | erpAgent 集成 |
|------|---------|--------------|
| **智能问数** | ✅ 6 种查询类型 | ✅ 已集成 |
| **多轮对话** | ✅ 支持 | ✅ 支持 |
| **查询历史** | ✅ localStorage | ✅ 已实现 |
| **收藏功能** | ✅ 支持 | ✅ 已实现 |
| **点踩分析** | ✅ AI 分析 | ✅ 组件已复制 |
| **推荐问题** | ✅ 支持 | ✅ 已实现 |
| **图表展示** | ✅ ECharts | ✅ ResultPanel 支持 |

---

## ⚠️ 注意事项

### 1. CORS 配置

确保后端已配置 CORS：

文件：`D:\erpAgent\backend\app\main.py`

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应指定具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 2. Neo4j 连接

确认 Neo4j 认证信息正确：

文件：`D:\erpAgent\backend\.env`

```ini
NEO4J_URI=bolt://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=Tony1985
NEO4J_DATABASE=neo4j
```

### 3. 端口冲突

- 前端：5176 (Vite)
- 后端：8005 (FastAPI)
- Neo4j: 7687 (Bolt)

---

## 🧪 测试步骤

### 1. 启动后端

```bash
cd D:\erpAgent\backend
python -m uvicorn app.main:app --reload --port 8005
```

### 2. 启动前端

```bash
cd D:\erpAgent\frontend
npm run dev
```

### 3. 访问智能问数页面

浏览器打开：`http://localhost:5176/smart-query`

### 4. 测试查询

输入测试问题：
- "查询本月销售趋势"
- "显示 Top 10 客户排行"
- "库存预警商品有哪些"

### 5. 验证结果

- ✅ 后端 API 返回 200
- ✅ 前端显示分析过程
- ✅ 结果面板展示数据
- ✅ 历史记录保存成功

---

## 📁 文件清单

### 新增文件

| 文件 | 说明 | 大小 |
|------|------|------|
| `views/SmartQuery.vue` | 完整版智能问数组件 | 15.4KB |
| `views/SmartQueryView.vue` | 简化版智能问数组件 | 5.7KB |
| `router-smartquery.js` | 路由配置示例 | 0.4KB |
| `docs/ERP 知识图谱.md` | 知识图谱架构文档 | 8.1KB |
| `docs/SMARTQUERY_INTEGRATION.md` | 本集成文档 | - |

### 后端文件（已有）

| 文件 | 说明 |
|------|------|
| `app/api/v1/smart_query_v40.py` | 智能问数 v4.0 API |
| `app/api/v1/smart_query_v35.py` | 智能问数 v3.5 API |
| `app/services/neo4j_smart_query.py` | Neo4j 查询服务 |

---

## 🎉 完成状态

| 任务 | 状态 | 说明 |
|------|------|------|
| **ERP 知识图谱文档** | ✅ 完成 | 8.1KB 完整架构文档 |
| **SmartQuery 组件复制** | ✅ 完成 | 完整版 + 简化版 |
| **后端 API 就绪** | ✅ 完成 | 8 个版本可用 |
| **路由配置** | ⏳ 待配置 | 2 种方案可选 |
| **联调测试** | ⏳ 待执行 | 启动服务后测试 |

---

## 🚀 下一步行动

### 立即执行 (5 分钟)

1. ✅ 选择集成方案 (A 或 B)
2. ⏳ 配置路由
3. ⏳ 重启前端服务
4. ⏳ 测试查询功能

### 本周完成

- [ ] 完善 UI 样式适配
- [ ] 添加 JWT 认证集成
- [ ] 优化查询性能
- [ ] 添加更多示例问题

---

**集成完成时间**: 预计 10-15 分钟  
**难度**: ⭐⭐☆☆☆ (简单)  
**推荐方案**: 方案 A (简化版)

---

**文档版本**: v1.0  
**最后更新**: 2026-04-05  
**维护者**: erpAgent 团队
