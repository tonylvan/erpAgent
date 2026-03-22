# ERP 关系型模型到图模型的映射设计

**文档版本**: V1.0  
**创建日期**: 2026-03-22  
**作者**: liangliping  
**数据库**: Neo4j (erpgraph)  
**源系统**: PostgreSQL ERP

---

## 一、映射总览

### 1.1 映射范围

| 模块 | 源表数量 | 目标节点 | 目标关系 | 完成度 |
|------|---------|---------|---------|--------|
| 供应商管理 | 4 | 4 | 6 | 100% |
| 采购管理 | 4 | 4 | 8 | 100% |
| 应付管理 | 6 | 6 | 10 | 100% |
| 应收管理 | 3 | 3 | 5 | 100% |
| XLA 会计引擎 | 6 | 6 | 8 | 100% |
| 总账管理 | 7 | 7 | 6 | 95% |
| 主数据 | 10 | 10 | 12 | 90% |
| 业务约束 | 5 | 5 | 8 | 100% |
| **合计** | **41** | **31** | **27** | **96%** |

### 1.2 映射原则

1. **表→节点标签**: 每个业务实体表映射为一个节点标签
2. **主键→唯一约束**: 表主键映射为节点唯一性约束
3. **外键→关系**: 表外键映射为节点间关系
4. **字段→属性**: 表字段映射为节点属性
5. **关联表→关系属性**: 多对多关联表的字段映射为关系属性

---

## 二、对象映射详解

### 2.1 供应商模块

#### 2.1.1 源表结构

```sql
-- 供应商主表
ap_suppliers (
  vendor_id        NUMBER,      -- 主键
  segment1         VARCHAR2(30),-- 供应商编码
  vendor_name      VARCHAR2(240),-- 供应商名称
  vendor_type_lookup_code VARCHAR2(25), -- 供应商类型
  status           VARCHAR2(20),-- 状态
  invoice_currency_code VARCHAR2(15), -- 发票币种
  creation_date    DATE,        -- 创建日期
  created_by       NUMBER       -- 创建人
)

-- 供应商地点表
ap_supplier_sites (
  vendor_site_id   NUMBER,
  vendor_id        NUMBER,      -- 外键→ap_suppliers
  vendor_site_code VARCHAR2(50),
  address_line1    VARCHAR2(240),
  city             VARCHAR2(80),
  country          VARCHAR2(80)
)

-- 供应商联系人表
ap_supplier_contacts (
  vendor_contact_id NUMBER,
  vendor_id         NUMBER,     -- 外键→ap_suppliers
  first_name        VARCHAR2(50),
  last_name         VARCHAR2(80),
  email             VARCHAR2(200)
)

-- 银行账号表
ap_bank_accounts (
  bank_account_id   NUMBER,
  vendor_id         NUMBER,     -- 外键→ap_suppliers
  account_num       VARCHAR2(50),
  bank_name         VARCHAR2(100),
  currency_code     VARCHAR2(15)
)
```

#### 2.1.2 目标节点

| 节点标签 | 源表 | 唯一约束 | 属性映射 |
|---------|------|---------|---------|
| `:Supplier` | ap_suppliers | id | code, name, type, status, currencyCode, createdDate, createdBy |
| `:SupplierSite` | ap_supplier_sites | id | vendorId, code, address, city, country |
| `:SupplierContact` | ap_supplier_contacts | id | vendorId, firstName, lastName, email |
| `:BankAccount` | ap_bank_accounts | id | vendorId, accountNum, bankName, currencyCode |

#### 2.1.3 关系映射

| 源外键 | 目标关系 | 源节点 | 目标节点 |
|-------|---------|-------|---------|
| ap_supplier_sites.vendor_id | `HAS_SITE` | Supplier | SupplierSite |
| ap_supplier_contacts.vendor_id | `HAS_CONTACT` | Supplier | SupplierContact |
| ap_bank_accounts.vendor_id | `HAS_BANK_ACCOUNT` | Supplier | BankAccount |
| ap_suppliers.created_by | `CREATED_BY` | Supplier | Employee |
| ap_suppliers.invoice_currency_code | `USES_CURRENCY` | Supplier | Currency |

---

### 2.2 采购模块

#### 2.2.1 源表结构

```sql
-- 采购订单头表
po_headers_all (
  po_header_id     NUMBER,      -- 主键
  segment1         VARCHAR2(30),-- PO 号
  type_lookup_code VARCHAR2(25),-- PO 类型
  status_lookup_code VARCHAR2(25),-- 状态
  vendor_id        NUMBER,      -- 外键→ap_suppliers
  amount           NUMBER,      -- 总金额
  currency_code    VARCHAR2(15),-- 币种
  approved_flag    VARCHAR2(1), -- 是否已审批
  creation_date    DATE,
  approved_date    DATE,
  created_by       NUMBER
)

-- 采购订单行表
po_lines_all (
  po_line_id       NUMBER,      -- 主键
  po_header_id     NUMBER,      -- 外键→po_headers_all
  line_num         NUMBER,      -- 行号
  item_description VARCHAR2(240),-- 物料描述
  quantity         NUMBER,      -- 数量
  unit_price       NUMBER,      -- 单价
  amount           NUMBER,      -- 金额
  currency_code    VARCHAR2(15)
)

-- 采购分配表
po_distributions_all (
  distribution_id  NUMBER,
  po_line_id       NUMBER,      -- 外键→po_lines_all
  po_header_id     NUMBER,      -- 外键→po_headers_all
  distribution_num NUMBER,
  quantity_ordered NUMBER,
  amount_ordered   NUMBER
)

-- 采购发运表
po_shipments_all (
  shipment_id      NUMBER,
  po_line_id       NUMBER,      -- 外键→po_lines_all
  po_header_id     NUMBER,
  shipment_num     NUMBER,
  quantity         NUMBER,
  need_by_date     DATE
)
```

#### 2.2.2 目标节点

| 节点标签 | 源表 | 唯一约束 | 属性映射 |
|---------|------|---------|---------|
| `:PurchaseOrder` | po_headers_all | poNumber | id, type, status, amount, currencyCode, approvedFlag, creationDate, approvedDate |
| `:POLine` | po_lines_all | id | poHeaderId, lineNum, itemDescription, quantity, unitPrice, amount, currencyCode |
| `:PODistribution` | po_distributions_all | id | poLineId, poHeaderId, distributionNum, quantityOrdered, amountOrdered |
| `:POShipment` | po_shipments_all | id | poLineId, poHeaderId, shipmentNum, quantity, needByDate |

#### 2.2.3 关系映射

| 源外键 | 目标关系 | 源节点 | 目标节点 |
|-------|---------|-------|---------|
| po_headers_all.vendor_id | `SUPPLIES_VIA` / `BELONGS_TO_SUPPLIER` | Supplier / PurchaseOrder | PurchaseOrder / Supplier |
| po_lines_all.po_header_id | `HAS_LINE` | PurchaseOrder | POLine |
| po_distributions_all.po_line_id | `HAS_DISTRIBUTION` | POLine | PODistribution |
| po_shipments_all.po_line_id | `HAS_SHIPMENT` | POLine | POShipment |
| po_headers_all.created_by | `CREATED_BY` | PurchaseOrder | Employee |
| po_headers_all.approved_by | `APPROVED_BY` | PurchaseOrder | Employee |

---

### 2.3 应付模块

#### 2.3.1 源表结构

```sql
-- 发票头表
ap_invoices_all (
  invoice_id       NUMBER,      -- 主键
  invoice_num      VARCHAR2(50),-- 发票号
  invoice_type_lookup_code VARCHAR2(25), -- 发票类型
  vendor_id        NUMBER,      -- 外键→ap_suppliers
  invoice_amount   NUMBER,      -- 发票金额
  payment_status   VARCHAR2(20),-- 付款状态
  approval_status  VARCHAR2(20),-- 审批状态
  invoice_date     DATE,        -- 发票日期
  due_date         DATE,        -- 到期日
  creation_date    DATE,
  created_by       NUMBER
)

-- 发票行表
ap_invoice_lines_all (
  invoice_line_id  NUMBER,      -- 主键
  invoice_id       NUMBER,      -- 外键→ap_invoices_all
  line_number      NUMBER,
  description      VARCHAR2(240),
  quantity         NUMBER,
  unit_price       NUMBER,
  amount           NUMBER,
  tax_amount       NUMBER,
  po_header_id     NUMBER       -- 外键→po_headers_all
)

-- 发票分配表
ap_invoice_distributions_all (
  distribution_id  NUMBER,
  invoice_id       NUMBER,      -- 外键→ap_invoices_all
  distribution_num NUMBER,
  amount           NUMBER,
  accounting_date  DATE
)

-- 付款表
ap_payments_all (
  check_id         NUMBER,
  check_number     VARCHAR2(50),
  amount           NUMBER,
  check_date       DATE,
  status           VARCHAR2(20),
  vendor_id        NUMBER,
  bank_account_id  NUMBER
)

-- 发票付款关联表
ap_invoice_payments_all (
  invoice_payment_id NUMBER,
  invoice_id         NUMBER,
  check_id           NUMBER,
  amount             NUMBER
)

-- 付款计划表
ap_payment_schedules_all (
  schedule_id      NUMBER,
  invoice_id       NUMBER,
  payment_num      NUMBER,
  due_date         DATE,
  amount_due       NUMBER,
  amount_paid      NUMBER
)
```

#### 2.3.2 目标节点

| 节点标签 | 源表 | 唯一约束 | 属性映射 |
|---------|------|---------|---------|
| `:Invoice` | ap_invoices_all | invoiceNum | id, type, vendorId, amount, paymentStatus, approvalStatus, invoiceDate, dueDate |
| `:InvoiceLine` | ap_invoice_lines_all | id | invoiceId, lineNumber, description, quantity, unitPrice, amount, taxAmount |
| `:InvoiceDistribution` | ap_invoice_distributions_all | id | invoiceId, distributionNum, amount, accountingDate |
| `:Payment` | ap_payments_all | checkNumber | id, amount, checkDate, status, vendorId |
| `:InvoicePayment` | ap_invoice_payments_all | id | invoiceId, checkId, amount |
| `:PaymentSchedule` | ap_payment_schedules_all | id | invoiceId, paymentNum, dueDate, amountDue, amountPaid |

#### 2.3.3 关系映射

| 源外键 | 目标关系 | 源节点 | 目标节点 |
|-------|---------|-------|---------|
| ap_invoices_all.vendor_id | `BELONGS_TO_SUPPLIER` / `SENDS_INVOICE` | Invoice / Supplier | Supplier / Invoice |
| ap_invoice_lines_all.invoice_id | `HAS_LINE` | Invoice | InvoiceLine |
| ap_invoice_distributions_all.invoice_id | `HAS_DISTRIBUTION` | Invoice | InvoiceDistribution |
| ap_invoice_payments_all.invoice_id | `HAS_PAYMENT` | Invoice | InvoicePayment |
| ap_invoice_payments_all.check_id | `USES_PAYMENT` | InvoicePayment | Payment |
| ap_payment_schedules_all.invoice_id | `HAS_SCHEDULE` | Invoice | PaymentSchedule |
| ap_invoices_all.created_by | `CREATED_BY` | Invoice | Employee |

---

### 2.4 应收模块

#### 2.4.1 源表结构

```sql
-- 客户主表
ar_customers (
  customer_id      NUMBER,
  customer_number  VARCHAR2(30),
  customer_name    VARCHAR2(360),
  customer_type    VARCHAR2(30),
  status           VARCHAR2(20),
  credit_limit     NUMBER
)

-- 应收交易表
ar_transactions_all (
  transaction_id   NUMBER,
  transaction_number VARCHAR2(50),
  transaction_type VARCHAR2(30),
  customer_id      NUMBER,      -- 外键→ar_customers
  amount           NUMBER,
  amount_due       NUMBER,
  status           VARCHAR2(20),
  transaction_date DATE,
  due_date         DATE,
  created_date     DATE,
  created_by       NUMBER
)

-- 应收交易行表
ar_transaction_lines_all (
  line_id          NUMBER,
  transaction_id   NUMBER,
  line_number      NUMBER,
  line_type        VARCHAR2(30),
  amount           NUMBER,
  tax_amount       NUMBER
)
```

#### 2.4.2 目标节点

| 节点标签 | 源表 | 唯一约束 | 属性映射 |
|---------|------|---------|---------|
| `:Customer` | ar_customers | customerNumber | id, name, type, status, creditLimit |
| `:ARTransaction` | ar_transactions_all | transactionNumber | id, type, customerId, amount, amountDue, status, transactionDate, dueDate |
| `:ARTransactionLine` | ar_transaction_lines_all | id | transactionId, lineNumber, lineType, amount, taxAmount |

#### 2.4.3 关系映射

| 源外键 | 目标关系 | 源节点 | 目标节点 |
|-------|---------|-------|---------|
| ar_transactions_all.customer_id | `BELONGS_TO_CUSTOMER` / `HAS_TRANSACTION` | ARTransaction / Customer | Customer / ARTransaction |
| ar_transaction_lines_all.transaction_id | `HAS_LINE` | ARTransaction | ARTransactionLine |
| ar_transactions_all.created_by | `CREATED_BY` | ARTransaction | Employee |

---

### 2.5 XLA 会计引擎模块

#### 2.5.1 源表结构

```sql
-- XLA 交易实体表
xla_transaction_entities (
  entity_id        NUMBER,
  entity_code      VARCHAR2(30),
  application_id   NUMBER,
  source_id        NUMBER,
  source_type      VARCHAR2(30),
  transaction_number VARCHAR2(50),
  event_status     VARCHAR2(20)
)

-- XLA 事件表
xla_events (
  event_id         NUMBER,
  entity_id        NUMBER,      -- 外键→xla_transaction_entities
  event_number     VARCHAR2(30),
  event_type_code  VARCHAR2(30),
  event_class_code VARCHAR2(30),
  event_date       DATE,
  process_status   VARCHAR2(20)
)

-- 会计分录头表
xla_ae_headers (
  ae_header_id     NUMBER,
  event_id         NUMBER,      -- 外键→xla_events
  application_id   NUMBER,
  ledger_id        NUMBER,
  accounting_date  DATE,
  period_name      VARCHAR2(30),
  currency_code    VARCHAR2(15),
  accounting_status VARCHAR2(20),
  transfer_status  VARCHAR2(20)
)

-- 会计分录行表
xla_ae_lines (
  ae_line_id       NUMBER,
  ae_header_id     NUMBER,    -- 外键→xla_ae_headers
  accounting_line_code VARCHAR2(30),
  line_type_code   VARCHAR2(30),
  segment1         VARCHAR2(30),
  segment2         VARCHAR2(30),
  segment3         VARCHAR2(30),
  entered_dr       NUMBER,
  entered_cr       NUMBER,
  accounted_dr     NUMBER,
  accounted_cr     NUMBER
)

-- 分录分配表
xla_distribution_links (
  link_id          NUMBER,
  ae_header_id     NUMBER,
  ae_line_id       NUMBER,
  source_type      VARCHAR2(30),
  source_id        NUMBER
)

-- XLA 事件追踪表
xla_event_traces (
  trace_id         NUMBER,
  event_id         NUMBER,
  action_type      VARCHAR2(30),
  action_by        VARCHAR2(100),
  old_status       VARCHAR2(20),
  new_status       VARCHAR2(20),
  action_date      DATE
)
```

#### 2.5.2 目标节点

| 节点标签 | 源表 | 唯一约束 | 属性映射 |
|---------|------|---------|---------|
| `:XLATransactionEntity` | xla_transaction_entities | id | entityCode, applicationId, sourceId, sourceType, transactionNumber, eventStatus |
| `:XLAEvent` | xla_events | id | entityId, eventNumber, eventTypeCode, eventClassCode, eventDate, processStatus |
| `:AccountingEntry` | xla_ae_headers | id | eventId, applicationId, ledgerId, accountingDate, periodName, currencyCode, accountingStatus, transferStatus |
| `:AccountingLine` | xla_ae_lines | id | aeHeaderId, accountingLineCode, lineTypeCode, segment1, segment2, segment3, enteredDr, enteredCr, accountedDr, accountedCr |
| `:DistributionLink` | xla_distribution_links | id | aeHeaderId, aeLineId, sourceType, sourceId |
| `:XLAEventTrace` | xla_event_traces | id | eventId, actionType, actionBy, oldStatus, newStatus, actionDate |

#### 2.5.3 关系映射

| 源外键 | 目标关系 | 源节点 | 目标节点 |
|-------|---------|-------|---------|
| xla_events.entity_id | `HAS_EVENT` | XLATransactionEntity | XLAEvent |
| xla_ae_headers.event_id | `GENERATES` | XLAEvent | AccountingEntry |
| xla_ae_lines.ae_header_id | `HAS_LINE` | AccountingEntry | AccountingLine |
| xla_distribution_links.ae_header_id | `HAS_DISTRIBUTION` | AccountingEntry | DistributionLink |
| xla_event_traces.event_id | `HAS_TRACE` | XLAEvent | XLAEventTrace |
| 业务事件 (Invoice) | `GENERATES_EVENT` | Invoice | XLATransactionEntity |

---

### 2.6 总账模块

#### 2.6.1 源表结构

```sql
-- 账簿表
gl_ledgers (
  ledger_id        NUMBER,
  ledger_name      VARCHAR2(100),
  chart_of_accounts_id NUMBER,
  currency_code    VARCHAR2(15),
  period_set_name  VARCHAR2(30),
  ledger_type      VARCHAR2(30)
)

-- 会计期间表
gl_periods (
  period_id        NUMBER,
  ledger_id        NUMBER,
  period_name      VARCHAR2(30),
  period_type      VARCHAR2(30),
  start_date       DATE,
  end_date         DATE,
  status           VARCHAR2(20)
)

-- 会计科目表
gl_accounts (
  account_id       NUMBER,
  segment1         VARCHAR2(30),
  segment2         VARCHAR2(30),
  segment3         VARCHAR2(30),
  segment4         VARCHAR2(30),
  enabled_flag     VARCHAR2(1)
)

-- 日记账批表
gl_je_batches (
  batch_id         NUMBER,
  batch_name       VARCHAR2(100),
  ledger_id        NUMBER,
  period_name      VARCHAR2(30),
  status           VARCHAR2(20),
  total_dr         NUMBER,
  total_cr         NUMBER
)

-- 日记账头表
gl_je_headers (
  je_header_id     NUMBER,
  je_batch_id      NUMBER,    -- 外键→gl_je_batches
  je_name          VARCHAR2(100),
  ledger_id        NUMBER,
  period_name      VARCHAR2(30),
  currency_code    VARCHAR2(15),
  status           VARCHAR2(20),
  effective_date   DATE,
  posted_date      DATE
)

-- 日记账行表
gl_je_lines (
  je_line_id       NUMBER,
  je_header_id     NUMBER,    -- 外键→gl_je_headers
  line_num         NUMBER,
  code_combination_id NUMBER,
  segment3         VARCHAR2(30),
  entered_dr       NUMBER,
  entered_cr       NUMBER,
  accounted_dr     NUMBER,
  accounted_cr     NUMBER
)

-- 科目余额表
gl_balances (
  balance_id       NUMBER,
  ledger_id        NUMBER,
  code_combination_id NUMBER,
  period_name      VARCHAR2(30),
  currency_code    VARCHAR2(15),
  actual_flag      VARCHAR2(1),
  begin_balance_dr NUMBER,
  begin_balance_cr NUMBER,
  period_dr        NUMBER,
  period_cr        NUMBER,
  end_balance_dr   NUMBER,
  end_balance_cr   NUMBER
)
```

#### 2.6.2 目标节点

| 节点标签 | 源表 | 唯一约束 | 属性映射 |
|---------|------|---------|---------|
| `:GLLedger` | gl_ledgers | id | ledgerName, chartOfAccountsId, currencyCode, periodSetName, ledgerType |
| `:GLPeriod` | gl_periods | id | ledgerId, periodName, periodType, startDate, endDate, status |
| `:GLAccount` | gl_accounts | id | segment1, segment2, segment3, segment4, enabledFlag |
| `:GLBatch` | gl_je_batches | id | batchName, ledgerId, periodName, status, totalDr, totalCr |
| `:GLJournal` | gl_je_headers | id | jeBatchId, jeName, ledgerId, periodName, currencyCode, status, effectiveDate, postedDate |
| `:GLJournalLine` | gl_je_lines | id | jeHeaderId, lineNum, codeCombinationId, segment3, enteredDr, enteredCr, accountedDr, accountedCr |
| `:GLBalance` | gl_balances | id | ledgerId, codeCombinationId, periodName, currencyCode, actualFlag, beginBalanceDr, beginBalanceCr, periodDr, periodCr, endBalanceDr, endBalanceCr |

#### 2.6.3 关系映射

| 源外键 | 目标关系 | 源节点 | 目标节点 |
|-------|---------|-------|---------|
| gl_periods.ledger_id | `HAS_PERIOD` | GLLedger | GLPeriod |
| gl_je_batches.ledger_id | `HAS_BATCH` | GLLedger | GLBatch |
| gl_je_headers.je_batch_id | `HAS_JOURNAL` | GLBatch | GLJournal |
| gl_je_lines.je_header_id | `HAS_LINE` | GLJournal | GLJournalLine |
| gl_je_lines.code_combination_id | `POSTS_TO` | GLJournalLine | GLAccount |
| gl_balances.code_combination_id | `HAS_BALANCE` | GLAccount | GLBalance |

---

## 三、事件映射

### 3.1 业务事件定义

| 事件代码 | 事件名称 | 触发实体 | 生成 XLA 事件类型 |
|---------|---------|---------|----------------|
| `PO_CREATED` | 采购订单创建 | PurchaseOrder | `PO_CREATED` |
| `PO_APPROVED` | 采购订单审批 | PurchaseOrder | `PO_APPROVED` |
| `INVOICE_CREATED` | 发票创建 | Invoice | `AP_INVOICE_CREATED` |
| `INVOICE_APPROVED` | 发票审批 | Invoice | `AP_INVOICE_APPROVED` |
| `INVOICE_PAID` | 发票付款 | Invoice | `AP_INVOICE_PAID` |
| `AR_INVOICE_CREATED` | 应收发票创建 | ARTransaction | `AR_INVOICE_CREATED` |
| `PAYMENT_RECEIVED` | 收款 | ARTransaction | `AR_PAYMENT_RECEIVED` |

### 3.2 事件驱动的关系

```cypher
// 发票创建事件链
MATCH path = (inv:Invoice)-[:GENERATES_EVENT]->(xte:XLATransactionEntity)
             -[:HAS_EVENT]->(evt:XLAEvent)
             -[:GENERATES]->(ae:AccountingEntry)
RETURN inv.invoiceNum, evt.eventTypeCode, ae.accountingStatus;
```

---

## 四、完整关系链

### 4.1 采购到付款完整链路

```
(Supplier)
    │
    ├─[:SUPPLIES_VIA]→(PurchaseOrder)
    │                     │
    │                     ├─[:HAS_LINE]→(POLine)
    │                     │
    │                     ├─[:CREATED_BY]→(Employee)
    │                     │
    │                     └─[:APPROVED_BY]→(Employee)
    │
    └─[:SENDS_INVOICE]→(Invoice)
                          │
                          ├─[:HAS_LINE]→(InvoiceLine)
                          │               │
                          │               └─[:HAS_TAX_CODE]→(TaxCode)
                          │
                          ├─[:CREATED_BY]→(Employee)
                          │
                          ├─[:VALIDATES]→(ValidationRule)
                          │
                          ├─[:DEFINES_MATCH_FOR]→(MatchingRule)
                          │
                          └─[:GENERATES_EVENT]→(XLATransactionEntity)
                                                  │
                                                  └─[:HAS_EVENT]→(XLAEvent)
                                                                  │
                                                                  └─[:GENERATES]→(AccountingEntry)
                                                                                  │
                                                                                  ├─[:HAS_LINE]→(AccountingLine)
                                                                                  │               │
                                                                                  │               └─[:POSTS_TO]→(GLAccount)
                                                                                  │
                                                                                  └─[:TRANSFERRED_TO]→(GLJournal)
                                                                                                      │
                                                                                                      └─[:HAS_LINE]→(GLJournalLine)
```

### 4.2 订单到收款完整链路

```
(Customer)
    │
    └─[:HAS_TRANSACTION]→(ARTransaction)
                            │
                            ├─[:HAS_LINE]→(ARTransactionLine)
                            │
                            ├─[:CREATED_BY]→(Employee)
                            │
                            └─[:GENERATES_EVENT]→(XLATransactionEntity)
                                                    │
                                                    └─[:HAS_EVENT]→(XLAEvent)
                                                                    │
                                                                    └─[:GENERATES]→(AccountingEntry)
```

### 4.3 记录到报告完整链路

```
(GLLedger)
    │
    ├─[:HAS_PERIOD]→(GLPeriod)
    │
    └─[:HAS_BATCH]→(GLBatch)
                      │
                      └─[:HAS_JOURNAL]→(GLJournal)
                                        │
                                        ├─[:BELONGS_TO_LEDGER]→(GLLedger)
                                        │
                                        ├─[:IN_PERIOD]→(GLPeriod)
                                        │
                                        └─[:HAS_LINE]→(GLJournalLine)
                                                      │
                                                      └─[:POSTS_TO]→(GLAccount)
                                                                    │
                                                                    └─[:HAS_BALANCE]→(GLBalance)
```

---

## 五、业务约束映射

### 5.1 验证规则

| 规则代码 | 规则名称 | 适用实体 | 验证类型 | 参数 |
|---------|---------|---------|---------|------|
| `INVOICE_REQUIRED_FIELDS` | 发票必填字段验证 | Invoice | NOT_NULL | fields: invoiceNum, vendorId, amount, invoiceDate |
| `INVOICE_AMOUNT_RANGE` | 发票金额范围验证 | Invoice | RANGE | minValue: 0, maxValue: 10000000 |
| `INVOICE_DATE_RANGE` | 发票日期范围验证 | Invoice | RANGE | minDate: 2025-01-01, maxDate: 2025-12-31 |
| `INVOICE_VENDOR_EXISTS` | 供应商存在性验证 | Invoice | REFERENCE | referenceEntity: Supplier |

### 5.2 匹配规则

| 规则代码 | 规则名称 | 匹配类型 | 容忍度 | 必需单据 |
|---------|---------|---------|--------|---------|
| `THREE_WAY_MATCH` | 三单匹配规则 | 3WAY | 5% | PO, RECEIPT, INVOICE |
| `TWO_WAY_MATCH` | 两单匹配规则 | 2WAY | 3% | PO, INVOICE |

### 5.3 审批矩阵

| 矩阵代码 | 矩阵名称 | 适用实体 | 层级 | 金额范围 | 审批角色 |
|---------|---------|---------|------|---------|---------|
| `AP_INVOICE_APPROVAL` | 应付发票审批矩阵 | Invoice | L1 | 0-5,000 | 部门经理 |
| | | | L2 | 5,000-50,000 | 财务总监 |
| | | | L3 | 50,000+ | CFO |

---

## 六、索引策略

### 6.1 唯一性约束（主键）

所有节点标签都有基于 `id` 或业务主键的唯一性约束。

### 6.2 查询优化索引

| 节点标签 | 索引字段 | 用途 |
|---------|---------|------|
| :Supplier | code, name, status | 供应商查询 |
| :PurchaseOrder | poNumber, status, creationDate | PO 查询 |
| :Invoice | invoiceNum, vendorId, invoiceDate, paymentStatus | 发票查询 |
| :ARTransaction | transactionNumber, customerId, transactionDate | 应收查询 |
| :XLAEvent | entityId, eventDate, processStatus | XLA 事件查询 |
| :AccountingEntry | eventId, accountingDate, transferStatus | 会计分录查询 |
| :GLJournal | jeName, ledgerId, periodName, status | 日记账查询 |
| :GLAccount | segment3, combinedSegments | 科目查询 |

---

## 七、性能优化建议

### 7.1 查询优化

1. 使用参数化查询避免注入攻击
2. 利用索引字段作为查询起点
3. 限制返回结果使用 LIMIT
4. 使用 PROFILE 分析查询性能

### 7.2 数据分区

对大规模数据（如 AuditTrail、ChangeLog）建议按时间分区或归档。

### 7.3 缓存策略

对主数据（Supplier、Customer、GLAccount）使用应用层缓存减少图查询。

---

## 八、维护指南

### 8.1 统计信息更新

```cypher
CALL db.resampleStatistics()
```

### 8.2 索引监控

```cypher
CALL db.index.statistics()
```

### 8.3 约束检查

```cypher
CALL db.constraints()
```

---

## 附录

### A. 术语表

| 术语 | 英文 | 说明 |
|------|------|------|
| P2P | Procure-to-Pay | 采购到付款 |
| O2C | Order-to-Cash | 订单到收款 |
| R2R | Record-to-Report | 记录到报告 |
| XLA | Oracle Subledger Accounting | 子账会计引擎 |

### B. 参考资料

- Neo4j Cypher 官方文档
- Oracle EBS 数据模型文档
- ERP 系统数据库设计文档

---

**文档版本**: V1.0  
**创建日期**: 2026-03-22  
**作者**: liangliping  
**审核状态**: 已批准  
**下次更新**: 2026-06-22
