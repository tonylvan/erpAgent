-- ============================================
-- OTC/PTP 模块 RTR 实时同步触发器
-- ============================================

-- 创建通知函数（已存在则跳过）
CREATE OR REPLACE FUNCTION notify_neo4j_sync() 
RETURNS TRIGGER AS $func$
DECLARE
    payload TEXT;
    record_id BIGINT;
    record_data JSONB;
BEGIN
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        -- 根据表名获取主键
        IF TG_TABLE_NAME LIKE 'ar_%' OR TG_TABLE_NAME LIKE 'oe_%' OR TG_TABLE_NAME LIKE 'om_%' THEN
            -- OTC 模块
            IF TG_TABLE_NAME = 'ar_transactions_all' THEN
                record_id := NEW.transaction_id;
            ELSIF TG_TABLE_NAME = 'ar_receipts' THEN
                record_id := NEW.receipt_id;
            ELSIF TG_TABLE_NAME = 'ar_customers' THEN
                record_id := NEW.customer_id;
            ELSIF TG_TABLE_NAME = 'oe_order_headers_all' THEN
                record_id := NEW.header_id;
            ELSIF TG_TABLE_NAME = 'oe_order_lines_all' THEN
                record_id := NEW.line_id;
            ELSE
                record_id := COALESCE(NEW.id, NEW.transaction_id, NEW.receipt_id, NEW.customer_id, NEW.header_id, 0);
            END IF;
        ELSIF TG_TABLE_NAME LIKE 'ap_%' OR TG_TABLE_NAME LIKE 'po_%' THEN
            -- PTP 模块
            IF TG_TABLE_NAME = 'ap_invoices_all' THEN
                record_id := NEW.invoice_id;
            ELSIF TG_TABLE_NAME = 'ap_payments_all' THEN
                record_id := NEW.payment_id;
            ELSIF TG_TABLE_NAME = 'po_headers_all' THEN
                record_id := NEW.po_header_id;
            ELSIF TG_TABLE_NAME = 'po_lines_all' THEN
                record_id := NEW.po_line_id;
            ELSIF TG_TABLE_NAME = 'ap_suppliers' THEN
                record_id := NEW.vendor_id;
            ELSE
                record_id := COALESCE(NEW.id, NEW.invoice_id, NEW.payment_id, NEW.po_header_id, NEW.po_line_id, NEW.vendor_id, 0);
            END IF;
        ELSE
            record_id := COALESCE(NEW.id, 0);
        END IF;
        
        record_data := to_jsonb(NEW);
    ELSE
        -- DELETE
        IF TG_TABLE_NAME LIKE 'ar_%' OR TG_TABLE_NAME LIKE 'oe_%' OR TG_TABLE_NAME LIKE 'om_%' THEN
            IF TG_TABLE_NAME = 'ar_transactions_all' THEN
                record_id := OLD.transaction_id;
            ELSIF TG_TABLE_NAME = 'ar_receipts' THEN
                record_id := OLD.receipt_id;
            ELSIF TG_TABLE_NAME = 'ar_customers' THEN
                record_id := OLD.customer_id;
            ELSIF TG_TABLE_NAME = 'oe_order_headers_all' THEN
                record_id := OLD.header_id;
            ELSIF TG_TABLE_NAME = 'oe_order_lines_all' THEN
                record_id := OLD.line_id;
            ELSE
                record_id := COALESCE(OLD.id, OLD.transaction_id, OLD.receipt_id, OLD.customer_id, OLD.header_id, 0);
            END IF;
        ELSIF TG_TABLE_NAME LIKE 'ap_%' OR TG_TABLE_NAME LIKE 'po_%' THEN
            IF TG_TABLE_NAME = 'ap_invoices_all' THEN
                record_id := OLD.invoice_id;
            ELSIF TG_TABLE_NAME = 'ap_payments_all' THEN
                record_id := OLD.payment_id;
            ELSIF TG_TABLE_NAME = 'po_headers_all' THEN
                record_id := OLD.po_header_id;
            ELSIF TG_TABLE_NAME = 'po_lines_all' THEN
                record_id := OLD.po_line_id;
            ELSIF TG_TABLE_NAME = 'ap_suppliers' THEN
                record_id := OLD.vendor_id;
            ELSE
                record_id := COALESCE(OLD.id, OLD.invoice_id, OLD.payment_id, OLD.po_header_id, OLD.po_line_id, OLD.vendor_id, 0);
            END IF;
        ELSE
            record_id := COALESCE(OLD.id, 0);
        END IF;
        
        record_data := to_jsonb(OLD);
    END IF;
    
    payload := json_build_object(
        'table', TG_TABLE_NAME,
        'operation', TG_OP,
        'record_id', record_id,
        'data', record_data
    )::text;
    
    PERFORM pg_notify('neo4j_rtr_sync', payload);
    
    INSERT INTO rtr_sync_log (table_name, operation, record_id, status) 
    VALUES (TG_TABLE_NAME, TG_OP, record_id, 'pending');
    
    RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END;
$func$ LANGUAGE plpgsql;

-- ============================================
-- OTC 模块触发器 (Order to Cash)
-- ============================================

-- 客户主数据
DROP TRIGGER IF EXISTS ar_customers_rtr ON ar_customers;
CREATE TRIGGER ar_customers_rtr
AFTER INSERT OR UPDATE OR DELETE ON ar_customers
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

-- 应收交易
DROP TRIGGER IF EXISTS ar_transactions_rtr ON ar_transactions_all;
CREATE TRIGGER ar_transactions_rtr
AFTER INSERT OR UPDATE OR DELETE ON ar_transactions_all
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

-- 应收收款
DROP TRIGGER IF EXISTS ar_receipts_rtr ON ar_receipts;
CREATE TRIGGER ar_receipts_rtr
AFTER INSERT OR UPDATE OR DELETE ON ar_receipts
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

-- 销售订单头
DROP TRIGGER IF EXISTS oe_order_headers_rtr ON oe_order_headers_all;
CREATE TRIGGER oe_order_headers_rtr
AFTER INSERT OR UPDATE OR DELETE ON oe_order_headers_all
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

-- 销售订单行
DROP TRIGGER IF EXISTS oe_order_lines_rtr ON oe_order_lines_all;
CREATE TRIGGER oe_order_lines_rtr
AFTER INSERT OR UPDATE OR DELETE ON oe_order_lines_all
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

-- ============================================
-- PTP 模块触发器 (Procure to Pay)
-- ============================================

-- 供应商主数据
DROP TRIGGER IF EXISTS ap_suppliers_rtr ON ap_suppliers;
CREATE TRIGGER ap_suppliers_rtr
AFTER INSERT OR UPDATE OR DELETE ON ap_suppliers
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

-- 采购订单头（已存在）
DROP TRIGGER IF EXISTS po_headers_rtr ON po_headers_all;
CREATE TRIGGER po_headers_rtr
AFTER INSERT OR UPDATE OR DELETE ON po_headers_all
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

-- 采购订单行（已存在）
DROP TRIGGER IF EXISTS po_lines_rtr ON po_lines_all;
CREATE TRIGGER po_lines_rtr
AFTER INSERT OR UPDATE OR DELETE ON po_lines_all
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

-- 应付发票（已存在）
DROP TRIGGER IF EXISTS ap_invoices_rtr ON ap_invoices_all;
CREATE TRIGGER ap_invoices_rtr
AFTER INSERT OR UPDATE OR DELETE ON ap_invoices_all
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

-- 应付付款
DROP TRIGGER IF EXISTS ap_payments_rtr ON ap_payments_all;
CREATE TRIGGER ap_payments_rtr
AFTER INSERT OR UPDATE OR DELETE ON ap_payments_all
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

-- 采购分配
DROP TRIGGER IF EXISTS po_distributions_rtr ON po_distributions_all;
CREATE TRIGGER po_distributions_rtr
AFTER INSERT OR UPDATE OR DELETE ON po_distributions_all
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

-- 发票 PO 匹配
DROP TRIGGER IF EXISTS ap_invoice_po_matches_rtr ON ap_invoice_po_matches;
CREATE TRIGGER ap_invoice_po_matches_rtr
AFTER INSERT OR UPDATE OR DELETE ON ap_invoice_po_matches
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

-- ============================================
-- 验证
-- ============================================
SELECT COUNT(*) AS total_rtr_triggers FROM pg_trigger WHERE tgname LIKE '%_rtr';

SELECT tgname, tgrelid::regclass AS table_name
FROM pg_trigger 
WHERE tgname LIKE '%_rtr'
ORDER BY tgrelid::regclass::text;
