# ERP 图模型 Schema（供生成 Cypher）

> 依据《ERP 关系型模型到图模型的映射设计》：PostgreSQL 表 → Neo4j 标签；外键 → 关系；字段 → 属性。

## 数据库

- **图库**：Neo4j（逻辑库名可由环境配置，如 `erpgraph`）
- **源系统**：PostgreSQL ERP（Oracle EBS 风格表名）

## 节点标签与源表（唯一约束多为 `id` 或文档所列业务键）

| 标签 | 典型源表 | 查询常用属性 |
|------|----------|--------------|
| `Supplier` | ap_suppliers | code, name, type, status, currencyCode |
| `SupplierSite` | ap_supplier_sites | vendorId, code, city, country |
| `SupplierContact` | ap_supplier_contacts | vendorId, email, firstName, lastName |
| `BankAccount` | ap_bank_accounts | vendorId, accountNum, bankName, currencyCode |
| `PurchaseOrder` | po_headers_all | id（或 poNumber）, type, status, amount, currencyCode, creationDate |
| `POLine` | po_lines_all | poHeaderId, lineNum, itemDescription, quantity, amount |
| `PODistribution` | po_distributions_all | poLineId, poHeaderId, distributionNum, quantityOrdered |
| `POShipment` | po_shipments_all | poLineId, shipmentNum, quantity, needByDate |
| `Invoice` | ap_invoices_all | id（或 invoiceNum）, vendorId, amount, paymentStatus, approvalStatus, invoiceDate, dueDate |
| `InvoiceLine` | ap_invoice_lines_all | invoiceId, lineNumber, amount, poHeaderId |
| `InvoiceDistribution` | ap_invoice_distributions_all | invoiceId, distributionNum, amount, accountingDate |
| `Payment` | ap_payments_all | id, amount, checkDate, status, vendorId |
| `InvoicePayment` | ap_invoice_payments_all | invoiceId, checkId, amount |
| `PaymentSchedule` | ap_payment_schedules_all | invoiceId, paymentNum, dueDate, amountDue, amountPaid |
| `Customer` | ar_customers | customerNumber, name, type, status, creditLimit |
| `ARTransaction` | ar_transactions_all | transactionNumber, customerId, amount, status, transactionDate |
| `ARTransactionLine` | ar_transaction_lines_all | transactionId, lineNumber, amount |
| `XLATransactionEntity` | xla_transaction_entities | entityCode, sourceId, sourceType, transactionNumber |
| `XLAEvent` | xla_events | entityId, eventNumber, eventTypeCode, eventDate, processStatus |
| `AccountingEntry` | xla_ae_headers | eventId, ledgerId, accountingDate, periodName, accountingStatus, transferStatus |
| `AccountingLine` | xla_ae_lines | aeHeaderId, segment1–3, enteredDr/Cr, accountedDr/Cr |
| `DistributionLink` | xla_distribution_links | aeHeaderId, aeLineId, sourceType, sourceId |
| `XLAEventTrace` | xla_event_traces | eventId, actionType, actionDate |
| `GLLedger` | gl_ledgers | ledgerName, currencyCode, ledgerType |
| `GLPeriod` | gl_periods | ledgerId, periodName, startDate, endDate, status |
| `GLAccount` | gl_accounts | segment1–4, enabledFlag |
| `GLBatch` | gl_je_batches | batchName, ledgerId, periodName, status |
| `GLJournal` | gl_je_headers | jeName, ledgerId, periodName, status, effectiveDate, postedDate |
| `GLJournalLine` | gl_je_lines | jeHeaderId, lineNum, codeCombinationId, segment3, enteredDr/Cr |
| `GLBalance` | gl_balances | ledgerId, codeCombinationId, periodName, endBalanceDr/Cr |

扩展/主数据类（若库中存在）：`Employee`、`Currency`、`TaxCode`、`ValidationRule`、`MatchingRule` 等，见完整映射文档。

## 关系类型（方向：`(源)-[:类型]->(目标)`）

| 关系 | 源标签 | 目标标签 | 说明 |
|------|--------|----------|------|
| `HAS_SITE` | Supplier | SupplierSite | |
| `HAS_CONTACT` | Supplier | SupplierContact | |
| `HAS_BANK_ACCOUNT` | Supplier | BankAccount | |
| `SUPPLIES_VIA` / `BELONGS_TO_SUPPLIER` | Supplier ↔ PurchaseOrder | 采购路径 | |
| `HAS_LINE` | PurchaseOrder | POLine | |
| `HAS_DISTRIBUTION` | POLine | PODistribution | |
| `HAS_SHIPMENT` | POLine | POShipment | |
| `SENDS_INVOICE` / `BELONGS_TO_SUPPLIER` | Supplier ↔ Invoice | 应付发票 | |
| `HAS_LINE` | Invoice | InvoiceLine | |
| `HAS_DISTRIBUTION` | Invoice | InvoiceDistribution | |
| `HAS_PAYMENT` | Invoice | InvoicePayment | |
| `USES_PAYMENT` | InvoicePayment | Payment | |
| `HAS_SCHEDULE` | Invoice | PaymentSchedule | |
| `HAS_TRANSACTION` | Customer | ARTransaction | |
| `HAS_LINE` | ARTransaction | ARTransactionLine | |
| `GENERATES_EVENT` | Invoice / ARTransaction | XLATransactionEntity | 业务事件进 XLA |
| `HAS_EVENT` | XLATransactionEntity | XLAEvent | |
| `GENERATES` | XLAEvent | AccountingEntry | |
| `HAS_LINE` | AccountingEntry | AccountingLine | |
| `HAS_DISTRIBUTION` | AccountingEntry | DistributionLink | |
| `HAS_TRACE` | XLAEvent | XLAEventTrace | |
| `TRANSFERRED_TO` | AccountingEntry | GLJournal | 过账到总账 |
| `HAS_PERIOD` | GLLedger | GLPeriod | |
| `HAS_BATCH` | GLLedger | GLBatch | |
| `HAS_JOURNAL` | GLBatch | GLJournal | |
| `HAS_LINE` | GLJournal | GLJournalLine | |
| `POSTS_TO` | GLJournalLine | GLAccount | |
| `HAS_BALANCE` | GLAccount | GLBalance | |
| `CREATED_BY` / `APPROVED_BY` | PurchaseOrder, Invoice 等 | Employee | 若存在 |

## 业务链（用于理解路径，不要臆造未列关系）

**采购到付款 P2P（节选）**  
`Supplier` →`SUPPLIES_VIA`→ `PurchaseOrder` →`HAS_LINE`→ `POLine`；`Supplier` →`SENDS_INVOICE`→ `Invoice` →`HAS_LINE`→ `InvoiceLine`；`Invoice` →`GENERATES_EVENT`→ `XLATransactionEntity` →`HAS_EVENT`→ `XLAEvent` →`GENERATES`→ `AccountingEntry` →`TRANSFERRED_TO`→ `GLJournal` …

**订单到收款 O2C**  
`Customer` →`HAS_TRANSACTION`→ `ARTransaction` →`HAS_LINE`→ `ARTransactionLine`；可 `GENERATES_EVENT`→ XLA 链。

**总账 R2R**  
`GLLedger` →`HAS_PERIOD`→ `GLPeriod`；`GLLedger` →`HAS_BATCH`→ `GLBatch` →`HAS_JOURNAL`→ `GLJournal` →`HAS_LINE`→ `GLJournalLine` →`POSTS_TO`→ `GLAccount` →`HAS_BALANCE`→ `GLBalance`。

## 索引与查询建议（优先用下列字段做起点或过滤）

- `Supplier`: code, name, status  
- `PurchaseOrder`: poNumber（或 segment 对应属性）, status, creationDate  
- `Invoice`: invoiceNum, vendorId, invoiceDate, paymentStatus  
- `ARTransaction`: transactionNumber, customerId, transactionDate  
- `XLAEvent`: entityId, eventDate, processStatus  
- `AccountingEntry`: eventId, accountingDate, transferStatus  
- `GLJournal`: jeName, ledgerId, periodName, status  
- `GLAccount`: segment3, combinedSegments  

## 事件类型（理解语义，非独立标签）

| 代码 | 含义 |
|------|------|
| PO_CREATED / PO_APPROVED | 采购订单 |
| INVOICE_CREATED / AP_INVOICE_* | 应付发票 |
| AR_INVOICE_CREATED 等 | 应收 |
