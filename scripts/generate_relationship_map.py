# -*- coding: utf-8 -*-
"""
Generate Visual Relationship Map for Oracle EBS
输出 Mermaid 格式的 ER 图和关系图
"""

def generate_mermaid_er_diagram():
    """生成 Mermaid ER 图"""
    
    mermaid = '''# Oracle EBS 完整表关系图 (ER Diagram)

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
'''
    
    return mermaid


def generate_neo4j_queries():
    """生成常用 Neo4j 查询"""
    
    queries = '''# Neo4j 常用关系查询

## 1. 查询供应商完整供应链

```cypher
MATCH path = (sup:Supplier {segment1: "SUP001"})
      -[:SUPPLIES_VIA]->(po:PurchaseOrder)
      -[:HAS_LINE]->(pol:POLine)
MATCH (sup)-[:SENDS_INVOICE]->(inv:Invoice)
      -[:HAS_LINE]->(inl:InvoiceLine)
RETURN sup, po, pol, inv, inl
ORDER BY po.creationDate DESC
LIMIT 10
```

## 2. 三单匹配检查

```cypher
MATCH (sup:Supplier)-[:SUPPLIES_VIA]->(po:PurchaseOrder)
      -[:HAS_LINE]->(pol:POLine)
MATCH (sup)-[:SENDS_INVOICE]->(inv:Invoice)
      -[:HAS_LINE]->(inl:InvoiceLine)
WHERE pol.poHeaderId = inl.poHeaderId
WITH po, inv, pol, inl,
     abs(pol.amount - inl.amount) / pol.amount as diff
WHERE diff > 0.05
RETURN po.id as po_id, inv.id as inv_id, 
       pol.amount as po_amount, inl.amount as inv_amount,
       diff * 100 as diff_percent
ORDER BY diff DESC
```

## 3. PO 金额一致性检查

```cypher
MATCH (po:PurchaseOrder)-[:HAS_LINE]->(pol:POLine)
WITH po, sum(pol.amount) as total_line_amount
WHERE po.amount IS NOT NULL
WITH po, total_line_amount,
     abs(po.amount - total_line_amount) / po.amount as diff
WHERE diff > 0.01
RETURN po.id as po_id, po.segment1 as po_number,
       po.amount as header_amount, total_line_amount,
       diff * 100 as diff_percent
ORDER BY diff DESC
```

## 4. 销售订单完整链路

```cypher
MATCH path = (cust:Customer)
      -[:HAS_TRANSACTION]->(so:SalesOrder)
      -[:HAS_LINE]->(sol:SalesOrderLine)
      -[:ORDERS_ITEM]->(item:InventoryItem)
WHERE so.segment1 = "SO001"
RETURN cust, so, sol, item
```

## 5. 总账借贷平衡检查

```cypher
MATCH (journal:GLJournal)-[:HAS_LINE]->(line:GLJournalLine)
WITH journal,
     sum(line.enteredDr) as total_dr,
     sum(line.enteredCr) as total_cr
WHERE total_dr <> total_cr
RETURN journal.id as journal_id, journal.jeName,
       total_dr, total_cr,
       abs(total_dr - total_cr) as difference
```

## 6. 完整 P2P 链路追踪

```cypher
MATCH path = (sup:Supplier)
      -[:SUPPLIES_VIA]->(po:PurchaseOrder)
      -[:HAS_LINE]->(pol:POLine)
      <-[:MATCHES_PO_LINE]-(inl:InvoiceLine)
      <-[:HAS_LINE]-(inv:Invoice)
      -[:HAS_PAYMENT]->(pay:Payment)
RETURN sup.segment1 as supplier,
       po.segment1 as po_number,
       pol.lineNumber as po_line,
       inv.invoiceNum as invoice,
       inl.lineNumber as invoice_line,
       pay.checkNumber as payment
ORDER BY po.creationDate DESC
LIMIT 10
```

## 7. 客户交易完整视图

```cypher
MATCH (cust:Customer {segment1: "CUST001"})
OPTIONAL MATCH (cust)-[:HAS_TRANSACTION]->(so:SalesOrder)
OPTIONAL MATCH (so)-[:HAS_LINE]->(sol:SalesOrderLine)
OPTIONAL MATCH (sol)-[:ORDERS_ITEM]->(item:InventoryItem)
RETURN cust, so, sol, item
ORDER BY so.orderDate DESC
```

## 8. 员工创建的所有单据

```cypher
MATCH (emp:Employee {id: 123})
      <-[:CREATED_BY]-(doc)
WHERE doc:PurchaseOrder OR doc:Invoice OR doc:SalesOrder
RETURN labels(doc)[0] as doc_type, count(doc) as count,
       collect(doc.segment1)[..5] as examples
```

## 9. 物料需求分析

```cypher
MATCH (item:InventoryItem {segment1: "ITEM001"})
      <-[:ORDERS_ITEM]-(sol:SalesOrderLine)
      <-[:HAS_LINE]-(so:SalesOrder)
WHERE so.orderDate >= date("2026-01-01")
RETURN item,
       sum(sol.quantity) as total_qty,
       count(DISTINCT so) as order_count,
       collect(DISTINCT so.segment1)[..10] as orders
```

## 10. 供应商绩效分析

```cypher
MATCH (sup:Supplier)
      -[:SUPPLIES_VIA]->(po:PurchaseOrder)
      -[:HAS_LINE]->(pol:POLine)
MATCH (sup)-[:SENDS_INVOICE]->(inv:Invoice)
WITH sup,
     count(DISTINCT po) as po_count,
     count(DISTINCT inv) as inv_count,
     sum(pol.amount) as total_po_amount,
     sum(inv.amount) as total_inv_amount
RETURN sup.segment1 as supplier_code,
       sup.vendor_name as supplier_name,
       po_count, inv_count,
       total_po_amount, total_inv_amount,
       inv_count * 1.0 / po_count as invoice_ratio
ORDER BY total_po_amount DESC
LIMIT 20
```
'''
    
    return queries


def main():
    print("="*70)
    print("Oracle EBS 关系图谱生成器")
    print("="*70)
    
    # 生成 Mermaid ER 图
    print("\n生成 Mermaid ER 图...")
    mermaid_content = generate_mermaid_er_diagram()
    
    with open('D:\\erpAgent\\backend\\docs\\relationship_diagram.md', 'w', encoding='utf-8') as f:
        f.write(mermaid_content)
    print("  已保存：relationship_diagram.md")
    
    # 生成 Neo4j 查询
    print("\n生成 Neo4j 查询示例...")
    queries_content = generate_neo4j_queries()
    
    with open('D:\\erpAgent\\scripts\\neo4j_advanced_queries.md', 'w', encoding='utf-8') as f:
        f.write(queries_content)
    print("  已保存：neo4j_advanced_queries.md")
    
    print("\n" + "="*70)
    print("关系图谱生成完成!")
    print("="*70)
    print("\n生成的文件:")
    print("  1. D:\\erpAgent\\backend\\docs\\relationship_diagram.md")
    print("     - Mermaid ER 图")
    print("     - 完整业务流程图")
    print("     - 字段级关系详情")
    print("\n  2. D:\\erpAgent\\scripts\\neo4j_advanced_queries.md")
    print("     - 10 个高级 Neo4j 查询示例")
    print("     - 涵盖 P2P、O2C、R2R 完整链路")
    print("="*70)


if __name__ == '__main__':
    main()
