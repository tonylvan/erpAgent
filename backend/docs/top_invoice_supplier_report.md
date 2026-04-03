# 最高金额发票的供应商报告

**查询时间**: 2026-04-03 09:07

---

## 🏆 最高金额发票

| 属性 | 值 |
|------|-----|
| **发票 ID** | 2004 |
| **发票号** | INV-TOO-LARGE |
| **金额** | **$15,000,000.00** |
| **类型** | 问题数据 (测试用) |
| **vendorId** | 4 |

---

## 🏭 供应商信息

| 属性 | 值 |
|------|-----|
| **供应商 ID** | 4 |
| **供应商名称** | Supplier E4 |
| **供应商代码** | V00004 |
| **供应商状态** | INACTIVE (非活跃) |

---

## 📊 Top 5 最高金额发票

| 排名 | ID | 发票号 | 金额 | vendorId |
|------|-----|--------|------|----------|
| 1 | 2004 | INV-TOO-LARGE | $15,000,000.00 | 4 |
| 2 | 186 | INV00000186 | $49,577.20 | 37 |
| 3 | 59 | INV00000059 | $49,501.52 | 10 |
| 4 | 47 | INV00000047 | $49,411.86 | 48 |
| 5 | 136 | INV00000136 | $49,398.53 | 37 |

---

## ⚠️ 重要说明

### 问题数据标识

**最高金额发票是问题数据！**

- **发票号**: INV-TOO-LARGE (明显异常命名)
- **金额**: $15,000,000.00 (超出正常范围 1000-10000)
- **供应商状态**: INACTIVE (非活跃供应商)
- **用途**: 数据质量规则测试

### 正常发票最高金额

| 属性 | 值 |
|------|-----|
| **发票 ID** | 186 |
| **发票号** | INV00000186 |
| **金额** | $49,577.20 |
| **供应商 ID** | 37 |

---

## 🔍 查询方法

### Cypher 查询

```cypher
// 查询最高金额发票及其供应商
MATCH (inv:Invoice)
WHERE inv.amount IS NOT NULL
RETURN inv.invoiceNum, inv.amount, inv.vendorId
ORDER BY inv.amount DESC
LIMIT 1

// 查询供应商详情
MATCH (sup:Supplier {id: 4})
RETURN sup.name, sup.code, sup.status
```

### Python 脚本

```bash
cd D:\erpAgent\scripts
python find_top_invoice_supplier.py
```

---

## 📈 业务洞察

### 异常检测

1. **金额异常**: $15M 远超正常范围 ($1K-$10K)
2. **供应商状态**: INACTIVE 非活跃供应商
3. **发票命名**: INV-TOO-LARGE 明显测试数据

### 风险警示

```
⚠️ 高额发票来自非活跃供应商
⚠️ 金额超出正常业务阈值 1500x
⚠️ 建议：触发人工审核流程
```

---

## 📁 相关文档

- **查询脚本**: `D:\erpAgent\scripts\find_top_invoice_supplier.py`
- **问题数据报告**: `D:\erpAgent\backend\docs\problematic_data_report.md`
- **Neo4j 事件报告**: `D:\erpAgent\backend\docs\neo4j_events_created.md`

---

**作者**: CodeMaster / 代码匠魂  
**日期**: 2026-04-03  
**版本**: V1.0
