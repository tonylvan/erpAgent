# Neo4j 问题数据测试图报告

**同步时间**: 2026-04-03 08:15  
**同步方式**: 独立标签 (ProblemData)  
**数据用途**: 测试数据质量规则和异常检测  
**问题节点**: 39 个

---

## ✅ 同步成果

### 问题节点统计

| 节点类型 | 数量 | 问题类型 |
|---------|------|---------|
| **ProblemInvoice** | 8 | 必填字段缺失/金额异常/日期错误 |
| **ProblemPurchaseOrder** | 4 | 金额不一致/无审批人/零金额 |
| **ProblemEmployee** | 9 | 重复记录/姓名异常/部门不存在 |
| **ProblemSupplier** | 8 | 相似名称/状态异常 |
| **ProblemProject** | 6 | 预算异常/日期错误/名称异常 |
| **ProblemFixedAsset** | 4 | 折旧异常/净值负数/状态异常 |
| **总计** | **39** | **6 大类** |

---

## 🎯 测试图特点

### 1. 独立标签标记

```cypher
// 所有问题数据都有 ProblemData 标签
(:ProblemData:ProblemInvoice {isProblematic: true})
(:ProblemData:ProblemEmployee {isProblematic: true})
(:ProblemData:ProblemSupplier {isProblematic: true})
```

### 2. 与正常数据隔离

```
主图：正常业务数据
- :Invoice (200 条正常发票)
- :Employee (540 个正常员工)
- :Supplier (59 个正常供应商)

测试图：问题数据
- :ProblemInvoice (8 条问题发票)
- :ProblemEmployee (9 个问题员工)
- :ProblemSupplier (8 个问题供应商)
```

### 3. 易于过滤查询

```cypher
// 只查询问题数据
MATCH (n:ProblemData) RETURN n

// 排除问题数据
MATCH (n) WHERE NOT n:ProblemData RETURN n

// 对比分析
MATCH (n:Invoice) RETURN count(n) as normal
UNION ALL
MATCH (n:ProblemInvoice) RETURN count(n) as problematic
```

---

## 📊 问题数据详情

### 问题发票 (8 条)

| ID | 发票号 | 问题描述 |
|----|--------|---------|
| 2001 | INV-NO-AMOUNT | 金额为 NULL |
| 2002 | INV-NO-DATE | 日期为 NULL |
| 2003 | INV-NEGATIVE | 负数金额 |
| 2004 | INV-TOO-LARGE | 超过 1000 万 |
| 2005 | INV-MISMATCH-1 | 头表≠行表 |
| 2006 | INV-DATE-ERROR | 日期早于 PO |
| 2007 | PO-0000001 | 重复发票号 |
| 2008 | PO-0000001 | 重复发票号 |

### 问题员工 (9 个)

| ID | 姓名 | 问题描述 |
|----|------|---------|
| 1501-1503 | John Smith | 重复 3 次 |
| 1504 | (空) | 空姓名 |
| 1505 | NULL | 姓名为 NULL |
| 1506-1507 | Test/999999 | 无效姓名 |
| 1508-1509 | Valid Name | 部门不存在 |

---

## 🚀 使用场景

### 1. 数据质量规则测试

```cypher
// 测试必填字段验证
MATCH (inv:ProblemInvoice)
WHERE inv.amount IS NULL OR inv.invoiceDate IS NULL
RETURN inv

// 测试金额范围验证
MATCH (inv:ProblemInvoice)
WHERE inv.amount < 0 OR inv.amount > 10000000
RETURN inv
```

### 2. 重复检测算法

```cypher
// 检测相似供应商名称
MATCH (sup:ProblemSupplier)
RETURN sup.name, count(*) as count
GROUP BY sup.name
HAVING count(*) > 1
```

### 3. 异常值检测

```cypher
// 检测负数金额
MATCH (inv:ProblemInvoice)
WHERE inv.amount < 0
RETURN inv

// 检测超预算项目
MATCH (proj:ProblemProject)
WHERE proj.actual > proj.budget
RETURN proj
```

### 4. 数据清洗验证

```cypher
// 标准化姓名格式
MATCH (emp:ProblemEmployee)
SET emp.cleanName = replace(trim(emp.name), '  ', ' ')
RETURN emp
```

---

## 📈 查询示例

### 统计问题数据

```cypher
// 按类型统计
MATCH (n:ProblemData)
RETURN labels(n)[1] as type, count(n) as count
ORDER BY count DESC
```

### 对比分析

```cypher
// 正常 vs 问题发票对比
MATCH (n:Invoice)
WITH count(n) as normal
MATCH (p:ProblemInvoice)
RETURN normal, count(p) as problematic
```

### 查找特定问题

```cypher
// 查找所有金额异常
MATCH (n:ProblemData)
WHERE n.amount < 0 OR n.amount > 1000000
RETURN n
```

---

## ✅ 总结

**同步方式**: 独立标签 (ProblemData)  
**节点总数**: 39 个  
**节点类型**: 6 种  
**隔离方式**: 标签隔离，易于过滤  

**用途**:
- ✅ 数据质量规则验证
- ✅ 异常检测算法测试
- ✅ 数据清洗流程验证
- ✅ 重复检测算法测试
- ✅ 不影响正常业务数据

**访问方式**:
```cypher
MATCH (n:ProblemData) RETURN n
```

---

**作者**: CodeMaster / 代码匠魂  
**日期**: 2026-04-03  
**版本**: V1.0
