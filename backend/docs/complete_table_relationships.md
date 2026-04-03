# Oracle EBS 完整表关系与字段映射字典

**版本**: V2.0 - 完整版  
**生成时间**: 2026-04-03 04:35  
**数据源**: Oracle EBS → PostgreSQL → Neo4j

---

## 一、核心关系矩阵

### 1.1 跨模块关系总览

```
┌─────────────────────────────────────────────────────────────────┐
│                     Oracle EBS 模块关系图                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐               │
│  │ 供应商   │────▶│ 采购管理 │────▶│ 应付管理 │               │
│  │ (AP)     │     │ (PO)     │     │ (AP)     │               │
│  └──────────┘     └──────────┘     └──────────┘               │
│       │                  │                  │                  │
│       │                  │                  │                  │
│       ▼                  ▼                  ▼                  │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐               │
│  │ 银行账号 │     │ 库存管理 │     │ XLA 会计  │               │
│  │ (CE)     │     │ (INV)    │     │ (XLA)    │               │
│  └──────────┘     └──────────┘     └──────────┘               │
│                           │                  │                  │
│                           │                  │                  │
│       ┌───────────────────┴──────────────────┘                  │
│       │                                                         │
│       ▼                                                         │
│  ┌──────────┐     ┌──────────┐     ┌──────────┐               │
│  │ 销售管理 │────▶│ 应收管理 │────▶│ 总账管理 │               │
│  │ (OM)     │     │ (AR)     │     │ (GL)     │               │
│  └──────────┘     └──────────┘     └──────────┘               │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 二、详细表关系与字段映射

### 2.1 供应商模块 (AP_SUPPLIERS)

#### 主表：ap_suppliers

| 字段名 | 类型 | 长度 | 必填 | 说明 | 映射目标 |
|--------|------|------|------|------|----------|
| vendor_id | NUMBER | 15 | Y | 供应商 ID(主键) | Supplier.id |
| segment1 | VARCHAR2 | 30 | Y | 供应商编码 | Supplier.code |
| vendor_name | VARCHAR2 | 240 | Y | 供应商名称 | Supplier.name |
| vendor_type_lookup_code | VARCHAR2 | 25 | N | 供应商类型 | Supplier.type |
| status | VARCHAR2 | 20 | N | 状态 | Supplier.status |
| invoice_currency_code | VARCHAR2 | 15 | N | 发票币种 | Supplier.currencyCode → Currency |
| creation_date | DATE | - | Y | 创建日期 | Supplier.createdDate |
| created_by | NUMBER | 15 | Y | 创建人 | Supplier.createdBy → Employee |

#### 子表关系

```sql
-- 1. 供应商地点 (1 对多)
ap_suppliers.vendor_id ──(1:N)── ap_supplier_sites.vendor_id
  映射：Supplier ─[HAS_SITE]→ SupplierSite

-- 2. 供应商联系人 (1 对多)
ap_suppliers.vendor_id ──(1:N)── ap_supplier_contacts.vendor_id
  映射：Supplier ─[HAS_CONTACT]→ SupplierContact

-- 3. 供应商银行账户 (1 对多)
ap_suppliers.vendor_id ──(1:N)── ap_bank_accounts.vendor_id
  映射：Supplier ─[HAS_BANK_ACCOUNT]→ BankAccount

-- 4. 创建人关联 (多对 1)
ap_suppliers.created_by ──(N:1)── per_all_people_f.employee_id
  映射：Supplier ─[CREATED_BY]→ Employee
```

### 2.2 采购模块 (PO_HEADERS_ALL)

#### 主表：po_headers_all

| 字段名 | 类型 | 长度 | 必填 | 说明 | 映射目标 |
|--------|------|------|------|------|----------|
| po_header_id | NUMBER | 15 | Y | PO 头 ID(主键) | PurchaseOrder.id |
| segment1 | VARCHAR2 | 30 | Y | PO 号 | PurchaseOrder.poNumber |
| type_lookup_code | VARCHAR2 | 25 | N | PO 类型 | PurchaseOrder.type |
| status_lookup_code | VARCHAR2 | 25 | N | 状态 | PurchaseOrder.status |
| vendor_id | NUMBER | 15 | Y | 供应商 ID(外键) | PurchaseOrder.vendorId → Supplier |
| amount | NUMBER | - | N | 总金额 | PurchaseOrder.amount |
| currency_code | VARCHAR2 | 15 | N | 币种 | PurchaseOrder.currencyCode → Currency |
| approved_flag | VARCHAR2 | 1 | N | 审批标志 | PurchaseOrder.approvedFlag |
| creation_date | DATE | - | Y | 创建日期 | PurchaseOrder.createdDate |
| approved_date | DATE | - | N | 审批日期 | PurchaseOrder.approvedDate |
| created_by | NUMBER | 15 | Y | 创建人 | PurchaseOrder.createdBy → Employee |

#### 行表：po_lines_all

| 字段名 | 类型 | 长度 | 必填 | 说明 | 映射目标 |
|--------|------|------|------|------|----------|
| po_line_id | NUMBER | 15 | Y | PO 行 ID(主键) | POLine.id |
| po_header_id | NUMBER | 15 | Y | PO 头 ID(外键) | POLine.poHeaderId → PurchaseOrder |
| line_num | NUMBER | - | Y | 行号 | POLine.lineNumber |
| item_description | VARCHAR2 | 240 | N | 物料描述 | POLine.description |
| quantity | NUMBER | - | N | 数量 | POLine.quantity |
| unit_price | NUMBER | - | N | 单价 | POLine.unitPrice |
| amount | NUMBER | - | N | 行金额 | POLine.amount |

#### 分配表：po_distributions_all

| 字段名 | 类型 | 长度 | 必填 | 说明 | 映射目标 |
|--------|------|------|------|------|----------|
| distribution_id | NUMBER | 15 | Y | 分配 ID | PODistribution.id |
| po_line_id | NUMBER | 15 | Y | PO 行 ID | PODistribution.poLineId → POLine |
| po_header_id | NUMBER | 15 | Y | PO 头 ID | PODistribution.poHeaderId → PurchaseOrder |
| distribution_num | NUMBER | - | Y | 分配号 | PODistribution.distributionNum |
| quantity_ordered | NUMBER | - | N | 订购数量 | PODistribution.quantityOrdered |
| amount_ordered | NUMBER | - | N | 订购金额 | PODistribution.amountOrdered |

#### 完整关系链

```
PurchaseOrder (po_headers_all)
    │
    ├─[:HAS_LINE]→ POLine (po_lines_all)
    │                 │
    │                 ├─[:HAS_DISTRIBUTION]→ PODistribution
    │                 │
    │                 └─[:HAS_SHIPMENT]→ POShipment
    │
    ├─[:BELONGS_TO_SUPPLIER]→ Supplier
    │
    ├─[:CREATED_BY]→ Employee
    │
    └─[:APPROVED_BY]→ Employee
```

### 2.3 应付模块 (AP_INVOICES_ALL)

#### 主表：ap_invoices_all

| 字段名 | 类型 | 长度 | 必填 | 说明 | 映射目标 |
|--------|------|------|------|------|----------|
| invoice_id | NUMBER | 15 | Y | 发票 ID | Invoice.id |
| invoice_num | VARCHAR2 | 50 | Y | 发票号 | Invoice.invoiceNumber |
| invoice_type_lookup_code | VARCHAR2 | 25 | N | 发票类型 | Invoice.type |
| vendor_id | NUMBER | 15 | Y | 供应商 ID | Invoice.vendorId → Supplier |
| invoice_amount | NUMBER | - | Y | 发票金额 | Invoice.amount |
| payment_status | VARCHAR2 | 20 | N | 付款状态 | Invoice.paymentStatus |
| approval_status | VARCHAR2 | 20 | N | 审批状态 | Invoice.approvalStatus |
| invoice_date | DATE | - | Y | 发票日期 | Invoice.invoiceDate |
| due_date | DATE | - | N | 到期日 | Invoice.dueDate |
| creation_date | DATE | - | Y | 创建日期 | Invoice.createdDate |
| created_by | NUMBER | 15 | Y | 创建人 | Invoice.createdBy → Employee |

#### 行表：ap_invoice_lines_all

| 字段名 | 类型 | 长度 | 必填 | 说明 | 映射目标 |
|--------|------|------|------|------|----------|
| invoice_line_id | NUMBER | 15 | Y | 发票行 ID | InvoiceLine.id |
| invoice_id | NUMBER | 15 | Y | 发票 ID | InvoiceLine.invoiceId → Invoice |
| line_number | NUMBER | - | Y | 行号 | InvoiceLine.lineNumber |
| description | VARCHAR2 | 240 | N | 描述 | InvoiceLine.description |
| quantity | NUMBER | - | N | 数量 | InvoiceLine.quantity |
| unit_price | NUMBER | - | N | 单价 | InvoiceLine.unitPrice |
| amount | NUMBER | - | Y | 行金额 | InvoiceLine.amount |
| tax_amount | NUMBER | - | N | 税额 | InvoiceLine.taxAmount |
| po_header_id | NUMBER | 15 | N | 关联 PO | InvoiceLine.poHeaderId → PurchaseOrder |

#### 付款表：ap_payments_all

| 字段名 | 类型 | 长度 | 必填 | 说明 | 映射目标 |
|--------|------|------|------|------|----------|
| check_id | NUMBER | 15 | Y | 付款 ID | Payment.id |
| check_number | VARCHAR2 | 50 | Y | 付款号 | Payment.checkNumber |
| amount | NUMBER | - | Y | 付款金额 | Payment.amount |
| check_date | DATE | - | Y | 付款日期 | Payment.checkDate |
| status | VARCHAR2 | 20 | N | 状态 | Payment.status |
| vendor_id | NUMBER | 15 | Y | 供应商 ID | Payment.vendorId → Supplier |
| bank_account_id | NUMBER | 15 | N | 银行账户 | Payment.bankAccountId → BankAccount |

#### 发票付款关联表：ap_invoice_payments_all

| 字段名 | 类型 | 长度 | 必填 | 说明 | 映射目标 |
|--------|------|------|------|------|----------|
| invoice_payment_id | NUMBER | 15 | Y | 关联 ID | InvoicePayment.id |
| invoice_id | NUMBER | 15 | Y | 发票 ID | InvoicePayment.invoiceId → Invoice |
| check_id | NUMBER | 15 | Y | 付款 ID | InvoicePayment.checkId → Payment |
| amount | NUMBER | - | Y | 付款金额 | InvoicePayment.amount |

#### 完整关系链

```
Invoice (ap_invoices_all)
    │
    ├─[:HAS_LINE]→ InvoiceLine (ap_invoice_lines_all)
    │                 │
    │                 └─[:MATCHES_PO_LINE]→ POLine (通过 po_header_id)
    │
    ├─[:BELONGS_TO_SUPPLIER]→ Supplier
    │
    ├─[:HAS_PAYMENT]→ Payment (通过 ap_invoice_payments_all)
    │
    ├─[:CREATED_BY]→ Employee
    │
    └─[:APPROVED_BY]→ Employee
```

### 2.4 销售模块 (SO_HEADERS_ALL)

#### 主表：so_headers_all

| 字段名 | 类型 | 长度 | 必填 | 说明 | 映射目标 |
|--------|------|------|------|------|----------|
| header_id | NUMBER | 15 | Y | SO 头 ID | SalesOrder.id |
| segment1 | VARCHAR2 | 30 | Y | SO 号 | SalesOrder.orderNumber |
| order_type_id | NUMBER | 15 | N | 订单类型 | SalesOrder.typeId → OrderType |
| customer_id | NUMBER | 15 | Y | 客户 ID | SalesOrder.customerId → Customer |
| order_date | DATE | - | Y | 订单日期 | SalesOrder.orderDate |
| status | VARCHAR2 | 20 | N | 状态 | SalesOrder.status |
| sales_rep_id | NUMBER | 15 | N | 销售员 | SalesOrder.salesRepId → Employee |

#### 行表：so_lines_all

| 字段名 | 类型 | 长度 | 必填 | 说明 | 映射目标 |
|--------|------|------|------|------|----------|
| line_id | NUMBER | 15 | Y | SO 行 ID | SalesOrderLine.id |
| header_id | NUMBER | 15 | Y | SO 头 ID | SalesOrderLine.headerId → SalesOrder |
| line_number | NUMBER | - | Y | 行号 | SalesOrderLine.lineNumber |
| inventory_item_id | NUMBER | 15 | Y | 物料 ID | SalesOrderLine.inventoryItemId → InventoryItem |
| quantity | NUMBER | - | Y | 数量 | SalesOrderLine.quantity |
| price | NUMBER | - | Y | 单价 | SalesOrderLine.price |
| status | VARCHAR2 | 20 | N | 行状态 | SalesOrderLine.status |

#### 完整关系链

```
SalesOrder (so_headers_all)
    │
    ├─[:HAS_LINE]→ SalesOrderLine (so_lines_all)
    │                 │
    │                 └─[:ORDERS_ITEM]→ InventoryItem
    │
    ├─[:BELONGS_TO_CUSTOMER]→ Customer
    │
    ├─[:CREATED_BY]→ Employee
    │
    └─[:HANDLED_BY]→ Employee (sales_rep_id)
```

### 2.5 库存模块 (MTL_SYSTEM_ITEMS_B)

#### 主表：mtl_system_items_b

| 字段名 | 类型 | 长度 | 必填 | 说明 | 映射目标 |
|--------|------|------|------|------|----------|
| inventory_item_id | NUMBER | 15 | Y | 物料 ID | InventoryItem.id |
| organization_id | NUMBER | 15 | Y | 组织 ID | InventoryItem.organizationId → Organization |
| segment1 | VARCHAR2 | 30 | Y | 物料编码 | InventoryItem.code |
| description | VARCHAR2 | 240 | N | 描述 | InventoryItem.description |
| status | VARCHAR2 | 20 | N | 状态 | InventoryItem.status |
| uom_code | VARCHAR2 | 10 | N | 单位代码 | InventoryItem.uomCode → UOM |
| creation_date | DATE | - | Y | 创建日期 | InventoryItem.createdDate |

#### 库存交易：mtl_material_transactions

| 字段名 | 类型 | 长度 | 必填 | 说明 | 映射目标 |
|--------|------|------|------|------|----------|
| transaction_id | NUMBER | 15 | Y | 交易 ID | InventoryTransaction.id |
| inventory_item_id | NUMBER | 15 | Y | 物料 ID | InventoryTransaction.itemId → InventoryItem |
| transaction_type_id | NUMBER | 15 | Y | 交易类型 | InventoryTransaction.typeId → TransactionType |
| quantity | NUMBER | - | Y | 数量 | InventoryTransaction.quantity |
| transaction_date | DATE | - | Y | 交易日期 | InventoryTransaction.date |

### 2.6 总账模块 (GL_JE_HEADERS)

#### 日记账头表：gl_je_headers

| 字段名 | 类型 | 长度 | 必填 | 说明 | 映射目标 |
|--------|------|------|------|------|----------|
| je_header_id | NUMBER | 15 | Y | 日记账头 ID | GLJournal.id |
| je_batch_id | NUMBER | 15 | Y | 日记账批 ID | GLJournal.batchId → GLBatch |
| je_name | VARCHAR2 | 100 | Y | 日记账名称 | GLJournal.name |
| ledger_id | NUMBER | 15 | Y | 账簿 ID | GLJournal.ledgerId → GLLedger |
| period_name | VARCHAR2 | 30 | Y | 期间名称 | GLJournal.periodName → GLPeriod |
| currency_code | VARCHAR2 | 15 | Y | 币种 | GLJournal.currencyCode → Currency |
| status | VARCHAR2 | 20 | N | 状态 | GLJournal.status |
| effective_date | DATE | - | Y | 生效日期 | GLJournal.effectiveDate |
| posted_date | DATE | - | N | 过账日期 | GLJournal.postedDate |

#### 日记账行表：gl_je_lines

| 字段名 | 类型 | 长度 | 必填 | 说明 | 映射目标 |
|--------|------|------|------|------|----------|
| je_line_id | NUMBER | 15 | Y | 日记账行 ID | GLJournalLine.id |
| je_header_id | NUMBER | 15 | Y | 日记账头 ID | GLJournalLine.headerId → GLJournal |
| line_num | NUMBER | - | Y | 行号 | GLJournalLine.lineNumber |
| code_combination_id | NUMBER | 15 | Y | 科目组合 ID | GLJournalLine.codeCombinationId → GLAccount |
| segment3 | VARCHAR2 | 30 | Y | 科目段 3 | GLJournalLine.segment3 |
| entered_dr | NUMBER | - | N | 借方金额 | GLJournalLine.enteredDr |
| entered_cr | NUMBER | - | N | 贷方金额 | GLJournalLine.enteredCr |
| accounted_dr | NUMBER | - | N | 本位币借方 | GLJournalLine.accountedDr |
| accounted_cr | NUMBER | - | N | 本位币贷方 | GLJournalLine.accountedCr |

#### 完整关系链

```
GLLedger
    │
    ├─[:HAS_PERIOD]→ GLPeriod
    │
    └─[:HAS_BATCH]→ GLBatch
                      │
                      └─[:HAS_JOURNAL]→ GLJournal
                                          │
                                          └─[:HAS_LINE]→ GLJournalLine
                                                            │
                                                            └─[:POSTS_TO]→ GLAccount
```

---

## 三、跨模块隐式关系

### 3.1 采购到付款链路 (P2P)

```
ap_suppliers (供应商)
    │
    │ vendor_id
    ▼
po_headers_all (采购订单)
    │
    │ po_header_id
    ▼
po_lines_all (采购订单行)
    │
    │ po_line_id
    ▼
po_distributions_all (采购分配)
    │
    │ 接收匹配
    ▼
ap_invoices_all (发票) ←─── ap_invoice_lines_all (发票行)
    │                           │
    │ invoice_id                │ po_header_id (隐式关联)
    ▼                           ▼
ap_invoice_payments_all (发票付款) ←── 匹配检查
    │
    │ check_id
    ▼
ap_payments_all (付款)
```

**关键字段关联**:
- `ap_invoice_lines_all.po_header_id` → `po_headers_all.po_header_id`
- `ap_invoice_lines_all.po_line_id` → `po_lines_all.po_line_id`

### 3.2 订单到收款链路 (O2C)

```
ar_customers (客户)
    │
    │ customer_id
    ▼
ar_transactions_all (应收交易)
    │
    │ transaction_id
    ▼
ar_transaction_lines_all (应收交易行)
    │
    │ 收款匹配
    ▼
ar_cash_receipts_all (收款)
    │
    │ receipt_id
    ▼
ar_receivable_applications_all (收款应用)
```

### 3.3 记录到报告链路 (R2R)

```
po_headers_all / ap_invoices_all / ar_transactions_all
    │
    │ 事务 ID
    ▼
xla_transaction_entities (XLA 事务实体)
    │
    │ entity_id
    ▼
xla_events (XLA 事件)
    │
    │ event_id
    ▼
xla_ae_headers (会计分录头)
    │
    │ ae_header_id
    ▼
xla_ae_lines (会计分录行)
    │
    │ code_combination_id
    ▼
gl_code_combinations (科目)
    │
    │ 过账
    ▼
gl_je_headers / gl_je_lines (总账日记账)
    │
    │ 汇总
    ▼
gl_balances (科目余额)
```

---

## 四、字段级验证规则

### 4.1 必填字段规则

| 表名 | 必填字段 | 验证 SQL |
|------|---------|---------|
| ap_suppliers | vendor_id, segment1, vendor_name | WHERE vendor_id IS NULL OR segment1 IS NULL |
| po_headers_all | po_header_id, segment1, vendor_id | WHERE vendor_id IS NULL |
| ap_invoices_all | invoice_id, invoice_num, vendor_id, invoice_amount | WHERE invoice_amount IS NULL |
| so_headers_all | header_id, segment1, customer_id | WHERE customer_id IS NULL |
| gl_je_headers | je_header_id, je_name, ledger_id | WHERE ledger_id IS NULL |

### 4.2 金额一致性规则

```sql
-- PO 头表金额 = 所有行金额之和
SELECT po_header_id, 
       amount as header_amount,
       (SELECT SUM(amount) FROM po_lines_all WHERE po_header_id = po.po_header_id) as line_total
FROM po_headers_all po
WHERE ABS(amount - (SELECT SUM(amount) FROM po_lines_all WHERE po_header_id = po.po_header_id)) > 0.01;

-- 发票头表金额 = 所有行金额之和
SELECT invoice_id,
       invoice_amount as header_amount,
       (SELECT SUM(amount) FROM ap_invoice_lines_all WHERE invoice_id = inv.invoice_id) as line_total
FROM ap_invoices_all inv
WHERE ABS(invoice_amount - (SELECT SUM(amount) FROM ap_invoice_lines_all WHERE invoice_id = inv.invoice_id)) > 0.01;
```

### 4.3 日期范围规则

```sql
-- 发票日期不能早于 PO 日期
SELECT inv.invoice_id, inv.invoice_date, po.creation_date
FROM ap_invoices_all inv
JOIN po_headers_all po ON inv.vendor_id = po.vendor_id
WHERE inv.invoice_date < po.creation_date;

-- 付款日期不能早于发票到期日
SELECT pay.check_id, pay.check_date, inv.due_date
FROM ap_payments_all pay
JOIN ap_invoice_payments_all ip ON pay.check_id = ip.check_id
JOIN ap_invoices_all inv ON ip.invoice_id = inv.invoice_id
WHERE pay.check_date < inv.due_date;
```

### 4.4 状态流转规则

```
PO 状态流转:
INCOMPLETE → APPROVED → CLOSED

发票状态流转:
NEEDS_REVAL → VALIDATED → APPROVED → PAID

SO 状态流转:
ENTERED → BOOKED → PICKED → SHIPPED → CLOSED
```

---

## 五、索引策略

### 5.1 外键索引

```sql
-- 供应商相关
CREATE INDEX idx_po_vendor_id ON po_headers_all(vendor_id);
CREATE INDEX idx_inv_vendor_id ON ap_invoices_all(vendor_id);
CREATE INDEX idx_pay_vendor_id ON ap_payments_all(vendor_id);

-- PO 相关
CREATE INDEX idx_pol_header_id ON po_lines_all(po_header_id);
CREATE INDEX idx_pod_line_id ON po_distributions_all(po_line_id);

-- 发票相关
CREATE INDEX idx_inl_invoice_id ON ap_invoice_lines_all(invoice_id);
CREATE INDEX idx_ip_invoice_id ON ap_invoice_payments_all(invoice_id);

-- SO 相关
CREATE INDEX idx_sol_header_id ON so_lines_all(header_id);

-- GL 相关
CREATE INDEX idx_glj_batch_id ON gl_je_headers(je_batch_id);
CREATE INDEX idx_gll_header_id ON gl_je_lines(je_header_id);
```

### 5.2 查询优化索引

```sql
-- 常用查询字段
CREATE INDEX idx_po_status ON po_headers_all(status_lookup_code);
CREATE INDEX idx_inv_payment_status ON ap_invoices_all(payment_status);
CREATE INDEX idx_so_status ON so_headers_all(status);
CREATE INDEX idx_glj_status ON gl_je_headers(status);

-- 日期范围查询
CREATE INDEX idx_po_creation_date ON po_headers_all(creation_date);
CREATE INDEX idx_inv_date ON ap_invoices_all(invoice_date);
CREATE INDEX idx_glj_effective_date ON gl_je_headers(effective_date);
```

---

## 六、Neo4j 图模型优化建议

### 6.1 补充缺失的关系

当前已同步 7 种关系，建议补充：

| 关系类型 | 源节点 | 目标节点 | 数量估算 |
|---------|--------|---------|---------|
| HAS_DISTRIBUTION | POLine | PODistribution | ~300 |
| HAS_SHIPMENT | POLine | POShipment | ~300 |
| HAS_PAYMENT | Invoice | Payment | ~150 |
| CREATED_BY | 所有实体 | Employee | ~1000 |
| APPROVED_BY | PO/Invoice | Employee | ~300 |
| USES_CURRENCY | 所有实体 | Currency | ~1500 |
| MATCHES_PO_LINE | InvoiceLine | POLine | ~300 |

### 6.2 添加关系属性

```cypher
// HAS_LINE 关系添加金额属性
MATCH (po:PurchaseOrder)-[r:HAS_LINE]->(line:POLine)
SET r.amount = line.amount,
    r.quantity = line.quantity

// SENDS_INVOICE 关系添加发票号
MATCH (sup:Supplier)-[r:SENDS_INVOICE]->(inv:Invoice)
SET r.invoiceNumber = inv.invoiceNumber
```

### 6.3 创建复合索引

```cypher
// 供应商查询优化
CREATE INDEX supplier_code_idx FOR (s:Supplier) ON (s.code, s.status)

// PO 查询优化
CREATE INDEX po_status_date_idx FOR (po:PurchaseOrder) ON (po.status, po.creationDate)

// 发票查询优化
CREATE INDEX invoice_vendor_date_idx FOR (inv:Invoice) ON (inv.vendorId, inv.invoiceDate)
```

---

## 七、数据质量检查清单

### 7.1 完整性检查

- [ ] 所有必填字段非空
- [ ] 所有外键引用存在
- [ ] 所有头表有对应行表记录
- [ ] 所有金额字段非负

### 7.2 一致性检查

- [ ] 头表金额 = 行表金额之和
- [ ] 借贷方金额平衡
- [ ] 日期逻辑正确 (订单日期 ≤ 发票日期 ≤ 付款日期)
- [ ] 状态流转合规

### 7.3 准确性检查

- [ ] 三单匹配差异 < 5%
- [ ] 物料编码格式正确
- [ ] 币种代码有效
- [ ] 员工 ID 有效

---

**文档版本**: V2.0  
**最后更新**: 2026-04-03  
**维护者**: CodeMaster / 代码匠魂
