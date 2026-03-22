/** 页面演示用：后续替换为 Neo4j / PostgreSQL API */

export const ontologyFromNeo4j = {
  source: "Neo4j",
  entities: [
    { type: "Supplier", label: "Supplier", description: "供应商主数据" },
    { type: "PurchaseOrder", label: "PO", description: "采购订单" },
    { type: "GoodsReceipt", label: "GoodsReceipt", description: "接收/入库" },
    { type: "Inspection", label: "Inspection", description: "验收/质检" },
    { type: "Invoice", label: "Invoice", description: "应付发票" },
    { type: "Payment", label: "Payment", description: "付款" },
    { type: "JournalEntry", label: "JournalEntry", description: "日记账分录" },
    { type: "GLAccount", label: "GLAccount", description: "总账科目" },
  ],
  relations: [
    { name: "SUPPLIES", from: "Supplier", to: "PurchaseOrder" },
    { name: "FULFILLED_BY", from: "PurchaseOrder", to: "GoodsReceipt" },
    { name: "INSPECTED_BY", from: "GoodsReceipt", to: "Inspection" },
    { name: "MATCHES", from: "Invoice", to: "PurchaseOrder" },
    { name: "BASED_ON", from: "Invoice", to: "GoodsReceipt" },
    { name: "SETTLED_BY", from: "Invoice", to: "Payment" },
    { name: "POSTS_TO", from: "Payment", to: "JournalEntry" },
    { name: "HITS", from: "JournalEntry", to: "GLAccount" },
  ],
};

export const ontologyFromPostgres = {
  source: "PostgreSQL 元数据",
  entities: [
    { type: "meta_entity", label: "entity_def", description: "实体定义表" },
    { type: "meta_relation", label: "relation_def", description: "关系定义表" },
    { type: "meta_version", label: "ontology_version", description: "本体版本" },
  ],
  relations: [
    { name: "defines", from: "ontology_version", to: "entity_def" },
    { name: "defines", from: "ontology_version", to: "relation_def" },
    { name: "maps_to_neo", from: "entity_def", to: "Neo4j Label" },
  ],
};
