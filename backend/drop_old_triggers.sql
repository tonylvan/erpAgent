-- 删除旧的知识图谱触发器（有问题的）
DROP TRIGGER IF EXISTS kg_sync_ap_checks ON ap_checks;
DROP TRIGGER IF EXISTS kg_sync_ap_invoice_lines_all ON ap_invoice_lines_all;
DROP TRIGGER IF EXISTS kg_sync_ap_invoices_all ON ap_invoices_all;
DROP TRIGGER IF EXISTS kg_sync_ap_suppliers ON ap_suppliers;
DROP TRIGGER IF EXISTS kg_sync_ar_receipts ON ar_receipts;
DROP TRIGGER IF EXISTS kg_sync_gl_balances ON gl_balances;
DROP TRIGGER IF EXISTS kg_sync_gl_je_headers ON gl_je_headers;
DROP TRIGGER IF EXISTS kg_sync_gl_je_lines ON gl_je_lines;
DROP TRIGGER IF EXISTS kg_sync_mtl_material_transactions ON mtl_material_transactions;
DROP TRIGGER IF EXISTS kg_sync_mtl_system_items_b ON mtl_system_items_b;
DROP TRIGGER IF EXISTS kg_sync_oe_order_headers_all ON oe_order_headers_all;
DROP TRIGGER IF EXISTS kg_sync_oe_order_lines_all ON oe_order_lines_all;
DROP TRIGGER IF EXISTS kg_sync_po_headers_all ON po_headers_all;
DROP TRIGGER IF EXISTS kg_sync_po_lines_all ON po_lines_all;
DROP TRIGGER IF EXISTS kg_sync_po_requisitions_all ON po_requisitions_all;
DROP TRIGGER IF EXISTS kg_sync_rcv_transactions ON rcv_transactions;

-- 删除旧函数
DROP FUNCTION IF EXISTS notify_kg_change() CASCADE;

-- 验证
SELECT COUNT(*) AS remaining_kg_triggers FROM pg_trigger WHERE tgname LIKE '%kg%';
