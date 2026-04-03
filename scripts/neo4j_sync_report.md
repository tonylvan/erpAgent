# Neo4j 图数据库同步完成报告

**同步时间**: 2026-04-03 04:30  
**数据库**: Neo4j (bolt://localhost:7687)  
**源系统**: PostgreSQL ERP (localhost:5432/erp)

---

## 📊 同步统计

### 节点数据（18 种实体，共 1,917 个节点）

| 序号 | 实体标签 | 数量 | 说明 |
|------|----------|------|------|
| 1 | InvoiceLine | 338 | 发票行项目 |
| 2 | POLine | 313 | 采购订单行 |
| 3 | Invoice | 200 | 采购发票 |
| 4 | SalesOrderLine | 160 | 销售订单行 |
| 5 | Payment | 150 | 付款记录 |
| 6 | Employee | 107 | 员工信息 |
| 7 | SupplierSite | 101 | 供应商地点 |
| 8 | SupplierContact | 101 | 供应商联系人 |
| 9 | PurchaseOrder | 100 | 采购订单 |
| 10 | InventoryItem | 100 | 库存物料 |
| 11 | BankAccount | 61 | 银行账户 |
| 12 | Supplier | 51 | 供应商 |
| 13 | SalesOrder | 50 | 销售订单 |
| 14 | FixedAsset | 50 | 固定资产 |
| 15 | Customer | 21 | 客户 |
| 16 | GLAccount | 7 | 总账科目 |
| 17 | Currency | 5 | 币种 |
| 18 | GLLedger | 2 | 总账账簿 |

### 关系数据（7 种关系，共 1,524 条关系）

| 序号 | 关系类型 | 数量 | 源节点 | 目标节点 |
|------|----------|------|--------|----------|
| 1 | HAS_LINE | 811 | Invoice/PurchaseOrder/SalesOrder | 各类行项目 |
| 2 | SENDS_INVOICE | 200 | Supplier | Invoice |
| 3 | ORDERS_ITEM | 160 | SalesOrderLine | InventoryItem |
| 4 | HAS_SITE | 101 | Supplier | SupplierSite |
| 5 | HAS_CONTACT | 101 | Supplier | SupplierContact |
| 6 | SUPPLIES_VIA | 100 | Supplier | PurchaseOrder |
| 7 | HAS_BANK_ACCOUNT | 51 | Supplier | BankAccount |

---

## 🔗 完整业务关系链

### 1. 采购到付款 (P2P)

```
(Supplier)
    ├─[:SUPPLIES_VIA]→(PurchaseOrder)
    │                     └─[:HAS_LINE]→(POLine)
    │
    └─[:SENDS_INVOICE]→(Invoice)
                          └─[:HAS_LINE]→(InvoiceLine)
```

### 2. 订单到收款 (O2C)

```
(Customer)
    └─[:HAS_TRANSACTION]→(SalesOrder)
                            └─[:HAS_LINE]→(SalesOrderLine)
                                            └─[:ORDERS_ITEM]→(InventoryItem)
```

### 3. 供应商管理

```
(Supplier)
    ├─[:HAS_SITE]→(SupplierSite)
    ├─[:HAS_CONTACT]→(SupplierContact)
    └─[:HAS_BANK_ACCOUNT]→(BankAccount)
```

---

## 💡 常用查询示例

### 1. 查询供应商的完整供应链

```cypher
MATCH (sup:Supplier {segment1: 'SUP001'})-[:SUPPLIES_VIA]->(po:PurchaseOrder)
RETURN sup.vendor_name, po.segment1 as po_number, po.amount, po.status;
```

### 2. 查询发票及其行项目

```cypher
MATCH (inv:Invoice {invoice_num: 'INV001'})-[:HAS_LINE]->(line:InvoiceLine)
RETURN inv.invoice_num, inv.invoice_amount, line.description, line.amount;
```

### 3. 查询销售订单的物料明细

```cypher
MATCH (so:SalesOrder)-[:HAS_LINE]->(line:SalesOrderLine)-[:ORDERS_ITEM]->(item:InventoryItem)
WHERE so.segment1 = 'SO001'
RETURN so.segment1 as order_number, line.line_number, item.segment1 as item_code, item.description;
```

### 4. 查询供应商的所有联系信息

```cypher
MATCH (sup:Supplier {segment1: 'SUP001'})-[:HAS_SITE|HAS_CONTACT|HAS_BANK_ACCOUNT]->(info)
RETURN labels(info)[0] as type, info;
```

### 5. 统计各状态采购订单数量

```cypher
MATCH (po:PurchaseOrder)
RETURN po.status_lookup_code as status, count(*) as count
ORDER BY count DESC;
```

### 6. 查询金额前 10 的发票

```cypher
MATCH (inv:Invoice)
RETURN inv.invoice_num, inv.vendor_id, inv.invoice_amount
ORDER BY inv.invoice_amount DESC
LIMIT 10;
```

---

## 🛠️ 访问方式

### Neo4j Browser
- **URL**: http://localhost:7474
- **用户名**: neo4j
- **密码**: Tony1985

### 连接字符串
```
bolt://localhost:7687
```

### Python 连接示例
```python
from neo4j import GraphDatabase

driver = GraphDatabase.driver('bolt://localhost:7687', 
                              auth=('neo4j', 'Tony1985'))

with driver.session() as session:
    result = session.run("MATCH (n) RETURN count(n) as total")
    print(f"总节点数：{result.single()['total']}")
```

---

## 📁 相关脚本

| 脚本名称 | 功能 | 路径 |
|----------|------|------|
| import_oracle_ebs_tables.py | 导入 Oracle 表到 PostgreSQL | D:\erpAgent\scripts\ |
| sync_oracle_to_neo4j.py | 同步节点数据到 Neo4j | D:\erpAgent\scripts\ |
| sync_relationships_to_neo4j.py | 同步关系到 Neo4j | D:\erpAgent\scripts\ |
| verify_neo4j.py | 验证 Neo4j 数据 | D:\erpAgent\scripts\ |

---

## ✅ 同步状态

- [x] PostgreSQL 服务运行正常
- [x] Neo4j 服务运行正常
- [x] 32 张 Oracle EBS 表导入 PostgreSQL
- [x] 18 种实体节点同步到 Neo4j (1,917 个节点)
- [x] 7 种业务关系同步到 Neo4j (1,524 条关系)
- [x] 数据验证通过

---

**下一步建议**:
1. 在 Neo4j Browser 中运行查询示例
2. 根据业务需求创建更多索引和约束
3. 开发 erpAgent 前端应用展示图数据
4. 实现复杂业务场景的图分析功能
