# ERP 知识图谱架构文档

> **生成时间**: 2026-04-05  
> **数据来源**: Neo4j 图数据库 (bolt://127.0.0.1:7687)  
> **同步方式**: RTR 实时同步 (<2 秒延迟)  
> **数据源**: PostgreSQL (Oracle EBS 业务数据)

---

## 📊 总体统计

| 指标 | 数量 | 说明 |
|------|------|------|
| **节点标签** | 47 种 | 涵盖供应商、采购、销售、财务等 |
| **有数据节点** | 15 种 | 实际包含数据的节点类型 |
| **总节点数** | 672 个 | 知识图谱实体总数 |
| **关系类型** | 32 种 | 实体间关联关系 |
| **总关系数** | 1149 条 | 实体间连接总数 |

---

## 🏗️ 核心业务模块

### 1. PTP (采购到付款) - Procure to Pay

**说明**: 供应商 → 采购订单 → 发票 → 付款全流程

#### 节点类型

| 节点标签 | 数量 | 核心属性 | 说明 |
|---------|------|---------|------|
| **Supplier** | 52 个 | `vendor_id`, `vendor_name`, `vendor_type` | 供应商主数据 |
| **PurchaseOrder** | 34 个 | `po_header_id` | 采购订单头 |
| **POLine** | 200 个 | `po_line_id`, `po_header_id`, `line_num`, `amount` | 采购订单明细 |
| **Invoice** | 113 个 | `invoice_id`, `invoice_num`, `vendor_id`, `amount`, `status` | 应付发票 |
| **Payment** | 110 个 | `id`, `amount`, `status`, `method`, `date` | 付款单 |

#### 关系模式

```
Supplier-[:SUPPLIES_INVOICE]->Invoice (100 条)
Supplier-[:SUPPLIES]->Invoice (54 条)
PurchaseOrder-[:HAS_LINE]->POLine (100 条)
POLine-[:HAS_HEADER]->PurchaseOrder (100 条)
POLine-[:BELONGS_TO]->PurchaseOrder (100 条)
Invoice-[:MATCHES_PO]->POLine (50 条)
PurchaseOrder-[:TRACKS]->Invoice (30 条)
Supplier-[:FULFILLS]->PurchaseOrder (30 条)
```

#### 典型查询路径

```cypher
// P2P 完整流程：供应商 → 采购订单 → 发票 → 付款
MATCH (s:Supplier)-[:SUPPLIES]->(inv:Invoice)
MATCH (inv)-[:MATCHES_PO]->(pl:POLine)
MATCH (pl)-[:HAS_HEADER]->(po:PurchaseOrder)
RETURN s.vendor_name, po.po_header_id, inv.invoice_num, inv.amount
```

---

### 2. OTC (订单到收款) - Order to Cash

**说明**: 客户 → 订单 → 销售 → 产品全流程

#### 节点类型

| 节点标签 | 数量 | 核心属性 | 说明 |
|---------|------|---------|------|
| **Customer** | 12 个 | `customer_id`, `customer_name`, `customer_number`, `status` | 客户主数据 |
| **Order** | 20 个 | `amount`, `status`, `date` | 销售订单 |
| **Sale** | 25 个 | `amount`, `timestamp`, `hour` | 销售交易 |
| **Product** | 8 个 | `code`, `name`, `category`, `price`, `stock`, `threshold` | 产品主数据 |

#### 关系模式

```
Customer-[:ORDERS]->PurchaseOrder (30 条)
Customer-[:PLACES]->Order (20 条)
Customer-[:PURCHASED]->Order (20 条)
Order-[:CONTAINS]->Product (30 条)
Customer-[:GENERATES]->Sale (20 条)
Customer-[:BUYS]->Product (20 条)
Sale-[:CONTAINS]->Product (20 条)
Product-[:SOLD_IN]->Sale (20 条)
Sale-[:MADE_TO]->Customer (20 条)
Customer-[:PREFERS]->Product (15 条)
```

#### 典型查询路径

```cypher
// O2C 完整流程：客户 → 订单 → 销售 → 产品
MATCH (c:Customer)-[:PLACES]->(o:Order)
MATCH (o)-[:CONTAINS]->(p:Product)
MATCH (c)-[:GENERATES]->(s:Sale)
RETURN c.customer_name, o.amount, p.name, s.amount
```

---

### 3. 财务核算 - Financial Accounting

**说明**: 总账科目 → 日记账 → 余额 → 会计分录

#### 节点类型

| 节点标签 | 说明 |
|---------|------|
| **GLAccount** | 总账科目 |
| **GLJournal** | 总账日记账 |
| **GLBalance** | 科目余额 |
| **AccountingEntry** | 会计分录 |
| **AccountingLine** | 分录明细 |
| **XLAEvent** | 会计事件 |
| **XLATransactionEntity** | 交易实体 |

#### 关系模式

```
AccountingEntry-[:AFFECTS]->GLBalance
GLJournal-[:HAS_LINE]->AccountingLine
XLAEvent-[:GENERATES]->AccountingEntry
```

---

### 4. 时间维度 - Time Dimension

**说明**: 时间维度表，支持按年/月/日/季度分析

#### 节点类型

| 节点标签 | 数量 | 核心属性 | 说明 |
|---------|------|---------|------|
| **Time** | 7 个 | `year`, `month`, `day`, `week`, `quarter` | 时间维度 |

#### 关系模式

```
Invoice-[:OCCURS_ON]->Time (30 条)
Payment-[:OCCURS_ON]->Time (30 条)
PurchaseOrder-[:OCCURS_ON]->Time (20 条)
Sale-[:HAS_TIME]->Time (25 条)
```

#### 典型查询

```cypher
// 按月份统计发票金额
MATCH (inv:Invoice)-[:OCCURS_ON]->(t:Time)
WHERE t.year = 2026 AND t.month = 4
RETURN t.day, sum(inv.amount) as total
ORDER BY t.day
```

---

## 🔗 完整关系类型列表 (32 种)

### AP 模块 (应付)
1. `SUPPLIES` - 供应商供应发票
2. `SUPPLIES_INVOICE` - 供应商开票
3. `HAS_STATUS` - 状态关联
4. `OWED_BY` - 欠款关系
5. `TRACKS` - 追踪关系

### PO 模块 (采购)
6. `HAS_LINE` - 订单明细
7. `BELONGS_TO` - 从属关系
8. `HAS_PRICE` - 价格关联
9. `FULFILLS` - 履约关系
10. `PURCHASED` - 采购关系

### AR 模块 (应收)
11. `PLACES` - 下单关系
12. `ORDERS` - 订购关系
13. `HAS_CONTACT` - 联系人关系

### 销售模块
14. `CONTAINS` - 包含关系
15. `BUYS` - 购买关系
16. `GENERATES` - 生成关系
17. `SOLD_IN` - 销售关系
18. `MADE_TO` - 定制关系
19. `PREFERS` - 偏好关系

### 财务模块
20. `PAYS_TO` - 付款关系
21. `MADE_BY` - 制单关系
22. `USES` - 使用关系
23. `AFFECTS` - 影响关系
24. `APPLIES_TO` - 应用关系

### 时间关系
25. `HAS_TIME` - 时间关联
26. `OCCURS_ON` - 发生于

### 通用关系
27. `HAS_HEADER` - 头表关联
28. `MATCHES_PO` - 采购匹配
29. `FULFILLED_BY` - 被履约
30. `STORED_IN` - 存储关系
31. `PART_OF` - 部分关系
32. `RELATED_TO` - 关联关系

---

## 📈 Top 10 关系分布

| 排名 | 关系类型 | 数量 | 说明 |
|------|---------|------|------|
| 1 | `HAS_HEADER` | 100 条 | 明细关联到头表 |
| 2 | `BELONGS_TO` | 100 条 | 从属关系 |
| 3 | `SUPPLIES_INVOICE` | 100 条 | 供应商开票 |
| 4 | `HAS_LINE` | 100 条 | 订单包含明细 |
| 5 | `OCCURS_ON` | 80 条 | 时间关联 |
| 6 | `SUPPLIES` | 54 条 | 供应关系 |
| 7 | `CONTAINS` | 50 条 | 包含关系 |
| 8 | `HAS_PRICE` | 50 条 | 价格关联 |
| 9 | `MATCHES_PO` | 50 条 | 采购订单匹配 |
| 10 | `HAS_STATUS` | 30 条 | 状态关联 |

---

## 🎯 典型业务场景查询

### 场景 1: 供应商全景分析

```cypher
// 查询供应商的所有业务关联
MATCH (s:Supplier {vendor_name: 'Supplier B1'})
OPTIONAL MATCH (s)-[:SUPPLIES]->(inv:Invoice)
OPTIONAL MATCH (s)-[:FULFILLS]->(po:PurchaseOrder)
RETURN 
  s.vendor_name as 供应商,
  count(DISTINCT inv) as 发票数,
  sum(inv.amount) as 发票总额,
  count(DISTINCT po) as 订单数
```

### 场景 2: 客户购买行为分析

```cypher
// 客户购买偏好分析
MATCH (c:Customer)-[:PREFERS]->(p:Product)
MATCH (c)-[:BUYS]->(p2:Product)
RETURN 
  c.customer_name as 客户,
  collect(DISTINCT p.name) as 偏好产品,
  count(DISTINCT p2) as 购买产品数
```

### 场景 3: 采购到付款全链路追踪

```cypher
// 完整 P2P 链路
MATCH path = (s:Supplier)-[:SUPPLIES*1..2]->(inv:Invoice)
MATCH (inv)-[:MATCHES_PO]->(pl:POLine)
MATCH (pl)-[:HAS_HEADER]->(po:PurchaseOrder)
RETURN 
  s.vendor_name as 供应商,
  po.po_header_id as 采购单,
  inv.invoice_num as 发票号,
  inv.amount as 金额,
  inv.status as 状态
ORDER BY inv.amount DESC
```

### 场景 4: 销售趋势分析 (按时间)

```cypher
// 月度销售趋势
MATCH (s:Sale)-[:HAS_TIME]->(t:Time)
WHERE t.year = 2026
RETURN 
  t.month as 月份,
  count(s) as 销售笔数,
  sum(s.amount) as 销售总额,
  avg(s.amount) as 客单价
ORDER BY t.month
```

### 场景 5: 产品关联分析

```cypher
// 产品被哪些订单包含
MATCH (p:Product {code: 'P001'})<-[:CONTAINS]-(o:Order)
MATCH (o)<-[:PLACES]-(c:Customer)
RETURN 
  p.name as 产品,
  count(DISTINCT o) as 订单数,
  count(DISTINCT c) as 客户数,
  p.price as 单价,
  p.stock as 库存
```

---

## 🔄 RTR 实时同步状态

### 触发器配置

| 模块 | 触发器数量 | 状态 |
|------|-----------|------|
| **PTP** | 7 个 | ✅ 运行中 |
| **OTC** | 5 个 | ✅ 运行中 |
| **财务** | 4 个 | ✅ 运行中 |
| **总计** | **16 个** | ✅ **100%** |

### 同步性能

| 指标 | 测量值 | 目标 | 状态 |
|------|--------|------|------|
| 同步延迟 | <2 秒 | <2 秒 | ✅ 达标 |
| 触发器响应 | <100ms | <200ms | ✅ 达标 |
| Neo4j 写入 | <500ms | <1s | ✅ 达标 |
| 测试通过率 | 100% | 100% | ✅ 达标 |

### 同步流程

```
PostgreSQL INSERT/UPDATE/DELETE
         ↓ (触发器捕获 <100ms)
pg_notify 发送通知 (JSON payload)
         ↓ (网络传输 <50ms)
RTR 消费者监听并解析
         ↓ (Neo4j 写入 <500ms)
Neo4j 节点/关系创建成功
         ↓ (日志更新 <100ms)
rtr_sync_log 状态更新为 completed

总延迟：<2 秒 ✅
```

---

## 📚 智能问数集成方案

### 后端 API 复用

**现有 API 版本**:
- `smart_query.py` (v1) - 基础版
- `smart_query_v2.py` ~ `smart_query_v40.py` - 增强版

**推荐版本**: `smart_query_v40.py` (最新，支持智能时间范围解析)

### API 端点

```
POST /api/v1/smart-query-v2/query
Content-Type: application/json

{
  "query": "查询本月销售趋势",
  "session_id": "user-123"
}
```

### 响应格式

```json
{
  "answer": "本月销售总额为 123.4 万元，环比增长 15.3%...",
  "cypher": "MATCH (s:Sale)-[:HAS_TIME]->(t:Time)...",
  "records": [...],
  "meta": {
    "type": "chart",
    "chart_type": "line"
  }
}
```

### 前端组件复用

**GSD 智能问数平台组件**:
- `SmartQuery.vue` - 主界面
- `ResultPanel.vue` - 结果展示
- `DislikeAIAnalysis.vue` - 点踩分析

**集成步骤**:
1. 复制组件到 `erpAgent/frontend/src/components/`
2. 修改 API 端点配置
3. 添加路由支持
4. 测试联调

---

## 🚀 快速问数实现方案

### 方案 A: 直接复制 GSD 平台 (推荐) ⭐

**优点**:
- ✅ 快速部署 (1-2 小时)
- ✅ 功能完整 (6 种查询类型)
- ✅ 已验证稳定
- ✅ 支持多轮对话

**步骤**:
1. 复制 GSD 前端组件
2. 复制 GSD 后端 API
3. 配置 Neo4j 连接
4. 启动服务

### 方案 B: 嵌入现有前端

**优点**:
- ✅ 统一用户体验
- ✅ 无需额外部署

**步骤**:
1. 在 `App.vue` 中添加智能问数入口
2. 复用现有 ResultPanel 组件
3. 调用后端智能问数 API

---

## 📋 下一步行动

### P0 - 本周完成

- [ ] 创建 `SmartQuery.vue` 组件
- [ ] 配置路由 `/smart-query`
- [ ] 测试 Neo4j 连接
- [ ] 验证查询功能

### P1 - 本月完成

- [ ] 集成真实 Neo4j 数据源
- [ ] 优化查询性能
- [ ] 添加收藏功能
- [ ] 实现查询历史

---

**文档版本**: v1.0  
**最后更新**: 2026-04-05  
**维护者**: erpAgent 团队
