-- ============================================
-- RTR 实时同步 - PostgreSQL 触发器脚本
-- 方案 B: 触发器 + Redis + Neo4j 消费者
-- ============================================

-- 1. 创建同步日志表
CREATE TABLE IF NOT EXISTS rtr_sync_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    operation VARCHAR(20) NOT NULL,
    record_id INTEGER,
    old_data JSONB,
    new_data JSONB,
    sync_time TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'pending'
);

CREATE INDEX idx_sync_log_time ON rtr_sync_log(sync_time);
CREATE INDEX idx_sync_log_table ON rtr_sync_log(table_name);
CREATE INDEX idx_sync_log_status ON rtr_sync_log(status);

-- 2. 创建通知函数
CREATE OR REPLACE FUNCTION notify_neo4j_sync() 
RETURNS TRIGGER AS $$
DECLARE
    payload JSON;
    v_record_id INTEGER;
    v_old_data JSONB;
    v_new_data JSONB;
BEGIN
    -- 获取记录 ID 和数据
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        v_record_id := COALESCE(NEW.id, NEW.invoice_id, NEW.payment_id, 
                                NEW.po_header_id, NEW.po_line_id, 
                                NEW.transaction_id, NEW.order_id,
                                NEW.vendor_id, NEW.customer_id);
        v_new_data := to_jsonb(NEW);
    END IF;
    
    IF TG_OP = 'DELETE' OR TG_OP = 'UPDATE' THEN
        v_old_data := to_jsonb(OLD);
    END IF;
    
    -- 构建变更数据
    payload := json_build_object(
        'table', TG_TABLE_NAME,
        'operation', TG_OP,
        'record_id', v_record_id,
        'old', v_old_data,
        'new', v_new_data,
        'timestamp', clock_timestamp()
    );
    
    -- 发送到 Redis 频道
    PERFORM pg_notify('neo4j_rtr_sync', payload::text);
    
    -- 记录同步日志
    INSERT INTO rtr_sync_log (table_name, operation, record_id, old_data, new_data, status)
    VALUES (TG_TABLE_NAME, TG_OP, v_record_id, v_old_data, v_new_data, 'pending');
    
    RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
END;
$$ LANGUAGE plpgsql;

-- 3. AP 模块触发器
DROP TRIGGER IF EXISTS ap_invoices_rtr ON ap_invoices_all;
CREATE TRIGGER ap_invoices_rtr
AFTER INSERT OR UPDATE OR DELETE ON ap_invoices_all
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

DROP TRIGGER IF EXISTS ap_payments_rtr ON ap_payments_all;
CREATE TRIGGER ap_payments_rtr
AFTER INSERT OR UPDATE OR DELETE ON ap_payments_all
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

DROP TRIGGER IF EXISTS ap_invoice_po_matches_rtr ON ap_invoice_po_matches;
CREATE TRIGGER ap_invoice_po_matches_rtr
AFTER INSERT OR UPDATE OR DELETE ON ap_invoice_po_matches
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

-- 4. PO 模块触发器
DROP TRIGGER IF EXISTS po_headers_rtr ON po_headers_all;
CREATE TRIGGER po_headers_rtr
AFTER INSERT OR UPDATE OR DELETE ON po_headers_all
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

DROP TRIGGER IF EXISTS po_lines_rtr ON po_lines_all;
CREATE TRIGGER po_lines_rtr
AFTER INSERT OR UPDATE OR DELETE ON po_lines_all
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

DROP TRIGGER IF EXISTS po_distributions_rtr ON po_distributions_all;
CREATE TRIGGER po_distributions_rtr
AFTER INSERT OR UPDATE OR DELETE ON po_distributions_all
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

-- 5. AR 模块触发器
DROP TRIGGER IF EXISTS ar_transactions_rtr ON ar_transactions_all;
CREATE TRIGGER ar_transactions_rtr
AFTER INSERT OR UPDATE OR DELETE ON ar_transactions_all
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

DROP TRIGGER IF EXISTS ar_payments_rtr ON ar_payments_all;
CREATE TRIGGER ar_payments_rtr
AFTER INSERT OR UPDATE OR DELETE ON ar_payments_all
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

-- 6. 供应商/客户触发器
DROP TRIGGER IF EXISTS suppliers_rtr ON suppliers;
CREATE TRIGGER suppliers_rtr
AFTER INSERT OR UPDATE OR DELETE ON suppliers
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

DROP TRIGGER IF EXISTS customers_rtr ON customers;
CREATE TRIGGER customers_rtr
AFTER INSERT OR UPDATE OR DELETE ON customers
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

-- 7. 销售模块触发器
DROP TRIGGER IF EXISTS sales_orders_rtr ON sales_orders_all;
CREATE TRIGGER sales_orders_rtr
AFTER INSERT OR UPDATE OR DELETE ON sales_orders_all
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

DROP TRIGGER IF EXISTS sales_order_lines_rtr ON sales_order_lines_all;
CREATE TRIGGER sales_order_lines_rtr
AFTER INSERT OR UPDATE OR DELETE ON sales_order_lines_all
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

-- 8. 库存模块触发器
DROP TRIGGER IF EXISTS items_rtr ON items;
CREATE TRIGGER items_rtr
AFTER INSERT OR UPDATE OR DELETE ON items
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

DROP TRIGGER IF EXISTS item_organizations_rtr ON item_organizations;
CREATE TRIGGER item_organizations_rtr
AFTER INSERT OR UPDATE OR DELETE ON item_organizations
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

-- ============================================
-- 验证触发器创建
-- ============================================
SELECT 
    tgname AS trigger_name,
    tgrelid::regclass AS table_name,
    tgenabled AS enabled
FROM pg_trigger 
WHERE tgname LIKE '%_rtr'
ORDER BY tgrelid::regclass::text, tgname;

-- 输出：已创建的触发器数量
SELECT COUNT(*) AS total_triggers FROM pg_trigger WHERE tgname LIKE '%_rtr';
