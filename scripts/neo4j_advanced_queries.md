# Neo4j 常用关系查询

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
