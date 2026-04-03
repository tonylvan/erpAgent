# 问题付款单查询报告

**查询时间**: 2026-04-03 09:25

---

## 📊 查询结果

### ❌ 未找到问题付款单

| 数据源 | 状态 | 说明 |
|--------|------|------|
| **Neo4j** | 无 ProblemData 标签 | 问题付款单未同步到图数据库 |
| **PostgreSQL** | 无问题数据表 | 问题数据可能已删除或未生成 |

---

## 📈 当前付款单状态

### PostgreSQL 统计

| 指标 | 值 |
|------|-----|
| **总数** | 150 条 |
| **ID 范围** | 1 - 150 |
| **最小金额** | $514.26 |
| **最大金额** | $29,751.96 |
| **平均金额** | $14,866.69 |

### Neo4j 统计

| 指标 | 值 |
|------|-----|
| **Payment 节点** | 150 个 |
| **ProblemPayment 节点** | 0 个 |
| **负数金额** | 0 条 |
| **超额金额 (>$50K)** | 0 条 |

---

## 🔍 问题数据类型 (Neo4j 中现有的)

| 类型 | 数量 | 标签 |
|------|------|------|
| 问题项目 | 6 | ProblemData:ProblemProject |
| 问题发票 | 8 | ProblemData:ProblemInvoice |
| 问题 PO | 4 | ProblemData:ProblemPurchaseOrder |
| 噪音员工 | 9 | ProblemData:ProblemEmployee |
| 噪音供应商 | 8 | ProblemData:ProblemSupplier |
| 噪音资产 | 4 | ProblemData:ProblemFixedAsset |
| **问题付款单** | **0** | ❌ 未找到 |

---

## 💡 可能原因

1. **问题付款单未生成**
   - 之前生成的问题数据可能只包含发票/PO/员工等
   - 付款单问题数据未包含在生成范围内

2. **数据已删除**
   - 问题数据可能被清理或删除

3. **未同步到 Neo4j**
   - PostgreSQL 中有问题数据但未同步到图数据库

---

## 🎯 建议操作

### 选项 1: 生成问题付款单数据

创建测试用的问题付款单：
- 负数金额付款单
- 超大金额付款单 (>$100K)
- 状态异常付款单

### 选项 2: 同步现有问题数据

将 PostgreSQL 中的问题数据同步到 Neo4j：
```bash
python D:\erpAgent\scripts\sync_problem_option3.py
```

### 选项 3: 使用现有问题数据测试

使用已有的问题发票/PO/项目进行测试，不专门生成付款单问题数据。

---

## 📁 查询脚本

**路径**: `D:\erpAgent\scripts\find_problem_payments.py`

包含：
- ✅ Neo4j 查询
- ✅ PostgreSQL 查询
- ✅ 字段检查
- ✅ 统计分析

---

**作者**: CodeMaster / 代码匠魂  
**日期**: 2026-04-03  
**版本**: V1.0
