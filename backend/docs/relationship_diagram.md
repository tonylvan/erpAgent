# Oracle EBS 完整表关系图 (ER Diagram)

## 供应商与采购模块

```mermaid
erDiagram
    SUPPLIER ||--o{ PURCHASE_ORDER : "SUPPLIES_VIA"
    SUPPLIER ||--o{ INVOICE : "SENDS_INVOICE"
    SUPPLIER ||--o{ SUPPLIER_SITE : "HAS_SITE"
    SUPPLIER ||--o{ SUPPLIER_CONTACT : "HAS_CONTACT"
    SUPPLIER ||--o{ BANK_ACCOUNT : "HAS_BANK_ACCOUNT"
    
    PURCHASE_ORDER ||--|{ PO_LINE : "HAS_LINE"
    PO_LINE ||--o{ PO_DISTRIBUTION : "HAS_DISTRIBUTION"
    PO_LINE ||--o{ PO_SHIPMENT : "HAS_SHIPMENT"
    
    INVOICE ||--|{ INVOICE_LINE : "HAS_LINE"
    INVOICE ||--o{ INVOICE_PAYMENT : "HAS_PAYMENT"
    INVOICE ||--o{ PAYMENT_SCHEDULE : "HAS_SCHEDULE"
    
    INVOICE_PAYMENT }|--|| PAYMENT : "USES_PAYMENT"
    
    SUPPLIER {
        number id PK
        string code
        string name
        string type
        string status
    }
    
    PURCHASE_ORDER {
        number id PK
        string poNumber
        string type
        string status
        number amount
        date creationDate
    }
    
    PO_LINE {
        number id PK
        number poHeaderId FK
        number lineNumber
        string description
        number quantity
        number unitPrice
        number amount
    }
    
    INVOICE {
        number id PK
        string invoiceNumber
        string type
        number vendorId FK
        number amount
        date invoiceDate
        date dueDate
        string paymentStatus
    }
    
    INVOICE_LINE {
        number id PK
        number invoiceId FK
        number lineNumber
        string description
        number quantity
        number unitPrice
        number amount
        number poHeaderId FK
    }
```

## 销售与库存模块

```mermaid
erDiagram
    CUSTOMER ||--o{ SALES_ORDER : "HAS_TRANSACTION"
    SALES_ORDER ||--|{ SALES_ORDER_LINE : "HAS_LINE"
    SALES_ORDER_LINE }|--|| INVENTORY_ITEM : "ORDERS_ITEM"
    
    INVENTORY_ITEM ||--o{ INVENTORY_TRANSACTION : "HAS_TRANSACTION"
    INVENTORY_ITEM ||--o{ SALES_ORDER_LINE : "ORDERED_IN"
    
    CUSTOMER {
        number id PK
        string customerNumber
        string name
        string type
        string status
        number creditLimit
    }
    
    SALES_ORDER {
        number id PK
        string orderNumber
        number customerId FK
        date orderDate
        string status
        number salesRepId FK
    }
    
    SALES_ORDER_LINE {
        number id PK
        number headerId FK
        number lineNumber
        number inventoryItemId FK
        number quantity
        number price
        string status
    }
    
    INVENTORY_ITEM {
        number id PK
        string code
        string description
        string status
        string uomCode
        number organizationId FK
    }
```

## 总账与会计模块

```mermaid
erDiagram
    GL_LEDGER ||--o{ GL_PERIOD : "HAS_PERIOD"
    GL_LEDGER ||--o{ GL_BATCH : "HAS_BATCH"
    GL_BATCH ||--|{ GL_JOURNAL : "HAS_JOURNAL"
    GL_JOURNAL ||--|{ GL_JOURNAL_LINE : "HAS_LINE"
    GL_JOURNAL_LINE }|--|| GL_ACCOUNT : "POSTS_TO"
    GL_ACCOUNT ||--o{ GL_BALANCE : "HAS_BALANCE"
    
    GL_LEDGER {
        number id PK
        string ledgerName
        string currencyCode
        number chartOfAccountsId FK
    }
    
    GL_BATCH {
        number id PK
        string batchName
        number ledgerId FK
        string periodName FK
        string status
        number totalDr
        number totalCr
    }
    
    GL_JOURNAL {
        number id PK
        number batchId FK
        string jeName
        number ledgerId FK
        string periodName FK
        string currencyCode
        date effectiveDate
        date postedDate
    }
    
    GL_JOURNAL_LINE {
        number id PK
        number headerId FK
        number lineNumber
        number codeCombinationId FK
        string segment3
        number enteredDr
        number enteredCr
        number accountedDr
        number accountedCr
    }
    
    GL_ACCOUNT {
        number id PK
        string segment1
        string segment2
        string segment3
        string segment4
        string enabledFlag
    }
```

## 完整业务流程图 (P2P + O2C + R2R)

```mermaid
graph TD
    subgraph P2P[采购到付款]
        SUPPLIER[供应商] -->|SUPPLIES_VIA| PO[采购订单]
        PO -->|HAS_LINE| POL[PO 行]
        SUPPLIER -->|SENDS_INVOICE| INV[发票]
        INV -->|HAS_LINE| INL[发票行]
        INL -.MATCHES_PO_LINE.-> POL
        INV -->|HAS_PAYMENT| PAY[付款]
    end
    
    subgraph O2C[订单到收款]
        CUST[客户] -->|HAS_TRANSACTION| SO[销售订单]
        SO -->|HAS_LINE| SOL[SO 行]
        SOL -->|ORDERS_ITEM| ITEM[物料]
        SO -->|GENERATES| AR[应收交易]
        AR -->|HAS_PAYMENT| RECEIPT[收款]
    end
    
    subgraph R2R[记录到报告]
        PO -->|GENERATES_EVENT| XTE1[XLA 事务]
        INV -->|GENERATES_EVENT| XTE2[XLA 事务]
        AR -->|GENERATES_EVENT| XTE3[XLA 事务]
        XTE1 -->|HAS_EVENT| XEV1[XLA 事件]
        XTE2 -->|HAS_EVENT| XEV2[XLA 事件]
        XTE3 -->|HAS_EVENT| XEV3[XLA 事件]
        XEV1 -->|GENERATES| AE1[会计分录]
        XEV2 -->|GENERATES| AE2[会计分录]
        XEV3 -->|GENERATES| AE3[会计分录]
        AE1 -->|HAS_LINE| AEL1[分录行]
        AE2 -->|HAS_LINE| AEL2[分录行]
        AE3 -->|HAS_LINE| AEL3[分录行]
        AEL1 -->|POSTS_TO| GLA[总账科目]
        AEL2 -->|POSTS_TO| GLA
        AEL3 -->|POSTS_TO| GLA
        GLA -->|HAS_BALANCE| GLB[科目余额]
    end
    
    style P2P fill:#e1f5ff
    style O2C fill:#fff4e1
    style R2R fill:#e8f5e9
```

## 字段级关系详情

### ap_suppliers (供应商主表)

| 字段 | 类型 | 关联表 | 关联字段 | 关系类型 |
|------|------|--------|---------|---------|
| vendor_id | NUMBER | - | - | 主键 |
| segment1 | VARCHAR2 | - | - | 业务键 |
| created_by | NUMBER | per_all_people_f | employee_id | 外键 |
| invoice_currency_code | VARCHAR2 | fnd_currencies | currency_code | 外键 |

### po_headers_all (采购订单头表)

| 字段 | 类型 | 关联表 | 关联字段 | 关系类型 |
|------|------|--------|---------|---------|
| po_header_id | NUMBER | - | - | 主键 |
| segment1 | VARCHAR2 | - | - | 业务键 |
| vendor_id | NUMBER | ap_suppliers | vendor_id | 外键 |
| created_by | NUMBER | per_all_people_f | employee_id | 外键 |
| approved_by | NUMBER | per_all_people_f | employee_id | 外键 |

### ap_invoices_all (发票头表)

| 字段 | 类型 | 关联表 | 关联字段 | 关系类型 |
|------|------|--------|---------|---------|
| invoice_id | NUMBER | - | - | 主键 |
| invoice_num | VARCHAR2 | - | - | 业务键 |
| vendor_id | NUMBER | ap_suppliers | vendor_id | 外键 |
| created_by | NUMBER | per_all_people_f | employee_id | 外键 |

### ap_invoice_lines_all (发票行表)

| 字段 | 类型 | 关联表 | 关联字段 | 关系类型 |
|------|------|--------|---------|---------|
| invoice_line_id | NUMBER | - | - | 主键 |
| invoice_id | NUMBER | ap_invoices_all | invoice_id | 外键 |
| po_header_id | NUMBER | po_headers_all | po_header_id | 外键 (隐式) |
| po_line_id | NUMBER | po_lines_all | po_line_id | 外键 (隐式) |

---

**生成时间**: 2026-04-03  
**工具**: generate_relationship_map.py
