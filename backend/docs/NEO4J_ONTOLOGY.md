# Neo4j 本体知识库

## 📊 数据库概览

**连接信息**:
- URI: `bolt://127.0.0.1:7687`
- 用户：`neo4j`
- 总节点数：**80 个**
- 总关系数：**45 个**
- 节点标签：**42 种**
- 关系类型：**2 种**

---

## 🏷️ 节点标签分类 (42 种)

### 核心业务实体 (GSD 智能问数)

| 标签 | 数量 | 说明 | 属性 |
|------|------|------|------|
| **Sale** | 25 | 销售记录 | amount, hour, timestamp |
| **Order** | 20 | 订单 | date, amount, status |
| **Payment** | 10 | 付款记录 | date, amount, method, id, status, customer |
| **Customer** | 10 | 客户 | level, name, industry, region |
| **Product** | 8 | 产品 | code, price, name, threshold, category, stock |
| **Time** | 7 | 时间维度 | week, month, year, day, quarter |

### Oracle EBS 核心模块

#### 应付账款 (AP)
| 标签 | 说明 |
|------|------|
| Supplier | 供应商 |
| SupplierSite | 供应商地点 |
| SupplierContact | 供应商联系人 |
| BankAccount | 银行账户 |
| Invoice | 发票 |
| InvoiceLine | 发票行 |
| InvoiceDistribution | 发票分配 |
| Payment | 付款 |
| InvoicePayment | 发票付款 |
| PaymentSchedule | 付款计划 |

#### 采购 (PO)
| 标签 | 说明 |
|------|------|
| PurchaseOrder | 采购订单 |
| POLine | 采购订单行 |
| PODistribution | 采购分配 |
| POShipment | 采购发货 |

#### 应收账款 (AR)
| 标签 | 说明 |
|------|------|
| Customer | 客户 |
| ARTransaction | 应收交易 |
| ARTransactionLine | 应收交易行 |

#### 总账 (GL)
| 标签 | 说明 |
|------|------|
| GLLedger | 总账账套 |
| GLPeriod | 会计期间 |
| GLAccount | 会计科目 |
| GLBatch | 总账批次 |
| GLJournal | 总账日记账 |
| GLJournalLine | 总账日记账行 |
| GLBalance | 总账余额 |

#### 子账会计 (XLA)
| 标签 | 说明 |
|------|------|
| XLATransactionEntity | XLA 交易实体 |
| XLAEvent | XLA 事件 |
| XLAEventTrace | XLA 事件追踪 |
| AccountingEntry | 会计分录 |
| AccountingLine | 会计分录行 |
| DistributionLink | 分配链接 |

#### 人力资源 (HR)
| 标签 | 说明 |
|------|------|
| Employee | 员工 |

#### 基础数据
| 标签 | 说明 |
|------|------|
| Currency | 币种 |
| TaxCode | 税率代码 |
| ValidationRule | 验证规则 |
| MatchingRule | 匹配规则 |
| ApprovalMatrix | 审批矩阵 |
| ProblemData | 问题数据 |
| Event | 事件 |

---

## 🔗 关系类型 (2 种)

| 关系 | 数量 | 说明 | 示例 |
|------|------|------|------|
| **HAS_TIME** | 25 | 时间关联 | Sale -[:HAS_TIME]-> Time |
| **PURCHASED** | 20 | 购买关系 | Customer -[:PURCHASED]-> Order |

---

## 📈 数据分布

### 节点数量分布
```
Sale (销售记录):     25 个  ████████████████████████
Order (订单):        20 个  ████████████████████
Payment (付款):      10 个  ██████████
Customer (客户):     10 个  ██████████
Product (产品):       8 个  ████████
Time (时间):          7 个  ███████
其他 EBS 实体：        0 个  (待导入)
```

### 关系分布
```
HAS_TIME (时间关联):  25 个  █████████████████████████
PURCHASED (购买):     20 个  ████████████████████
```

---

## 🎯 支持的查询场景

### 1. 销售分析
```cypher
// 查询销售趋势
MATCH (s:Sale)-[:HAS_TIME]->(t:Time)
RETURN t.day, sum(s.amount) as total
ORDER BY t.day

// 查询最高销售记录
MATCH (s:Sale)
RETURN s.timestamp, s.amount
ORDER BY s.amount DESC
LIMIT 10
```

### 2. 客户分析
```cypher
// 客户订单统计
MATCH (c:Customer)-[:PURCHASED]->(o:Order)
RETURN c.name, count(o) as orderCount, sum(o.amount) as totalAmount
ORDER BY totalAmount DESC

// 客户区域分布
MATCH (c:Customer)
RETURN c.region, count(c) as customerCount
```

### 3. 产品分析
```cypher
// 库存预警
MATCH (p:Product)
WHERE p.stock < p.threshold
RETURN p.code, p.name, p.stock, p.threshold
ORDER BY p.stock

// 产品类别统计
MATCH (p:Product)
RETURN p.category, count(p) as productCount, avg(p.price) as avgPrice
```

### 4. 付款分析
```cypher
// 付款状态统计
MATCH (p:Payment)
RETURN p.status, count(p) as count, sum(p.amount) as total
GROUP BY p.status

// 付款方式分析
MATCH (p:Payment)
RETURN p.method, count(p) as count
ORDER BY count DESC
```

### 5. 时间维度分析
```cypher
// 按周统计销售
MATCH (s:Sale)-[:HAS_TIME]->(t:Time)
RETURN t.week, sum(s.amount) as weeklySales
ORDER BY t.week

// 按月统计
MATCH (s:Sale)-[:HAS_TIME]->(t:Time)
RETURN t.month, t.year, sum(s.amount) as monthlySales
ORDER BY t.year, t.month
```

---

## 🔧 常用 Cypher 模板

### 统计查询
```cypher
// 节点总数
MATCH (n) RETURN count(n) as total

// 标签统计
MATCH (n)
UNWIND labels(n) as label
RETURN label, count(*) as count
ORDER BY count DESC

// 关系总数
MATCH ()-[r]->() RETURN count(r) as total

// 关系统计
MATCH ()-[r]->()
RETURN type(r) as type, count(*) as count
ORDER BY count DESC
```

### 数据探索
```cypher
// 查看节点属性
MATCH (n:Label) RETURN properties(n) as props LIMIT 10

// 查看关系模式
MATCH (n)-[r]->(m)
RETURN labels(n) as from, type(r) as rel, labels(m) as to
LIMIT 10

// 查找孤立节点
MATCH (n)
WHERE NOT (n)-->()
RETURN labels(n) as label, count(n) as count
```

---

## 📝 智能问数集成

### 关键词映射表

| 用户查询 | Cypher 模板 | 数据源 |
|---------|------------|--------|
| "销售趋势" | `MATCH (s:Sale)-[:HAS_TIME]->(t:Time) RETURN t.day, sum(s.amount)` | Sale, Time |
| "客户排行" | `MATCH (c:Customer)-[:PURCHASED]->(o:Order) RETURN c.name, sum(o.amount)` | Customer, Order |
| "库存预警" | `MATCH (p:Product) WHERE p.stock < p.threshold RETURN p` | Product |
| "付款统计" | `MATCH (p:Payment) RETURN p.status, count(p), sum(p.amount)` | Payment |
| "员工数量" | `MATCH (e:Employee) RETURN count(e)` | Employee |

### 响应类型

| 查询类型 | 返回格式 | 说明 |
|---------|---------|------|
| 趋势分析 | chart (折线图) | 时间序列数据 |
| 排行榜 | table (表格) | Top N 列表 |
| 统计概览 | stats (统计卡) | 关键指标 |
| 明细查询 | table (表格) | 详细记录 |

---

## 🚀 后续扩展

### 待导入数据
- [ ] AP 模块完整数据（供应商、发票、付款）
- [ ] PO 模块完整数据（采购订单、行、分配）
- [ ] AR 模块完整数据（客户、应收交易）
- [ ] GL 模块完整数据（总账、科目、余额）
- [ ] HR 模块完整数据（员工、部门）

### 待添加关系
- [ ] Supplier -[:SUPPLIES]-> Product
- [ ] Invoice -[:PAID_BY]-> Payment
- [ ] Order -[:CONTAINS]-> POLine
- [ ] Employee -[:WORKS_IN]-> Department
- [ ] GLJournal -[:HAS_LINE]-> GLJournalLine

---

**最后更新**: 2026-04-04  
**数据状态**: GSD 演示数据（80 节点，45 关系）  
**下次同步**: 待导入完整 EBS 数据
