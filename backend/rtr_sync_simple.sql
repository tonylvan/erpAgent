-- RTR 实时同步 - 简化版 SQL 脚本
-- 只创建核心表的触发器

-- 1. 创建同步日志表
CREATE TABLE IF NOT EXISTS rtr_sync_log (
    id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,
    operation VARCHAR(20) NOT NULL,
    record_id INTEGER,
    sync_time TIMESTAMP DEFAULT NOW(),
    status VARCHAR(20) DEFAULT 'pending'
);

CREATE INDEX IF NOT EXISTS idx_sync_log_time ON rtr_sync_log(sync_time);
CREATE INDEX IF NOT EXISTS idx_sync_log_table ON rtr_sync_log(table_name);

-- 2. 创建通知函数（简化版）
CREATE OR REPLACE FUNCTION notify_neo4j_sync() 
RETURNS TRIGGER AS $func$
DECLARE
    payload TEXT;
    record_id BIGINT;
BEGIN
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        -- 根据表名获取主键
        IF TG_TABLE_NAME = 'ap_invoices_all' THEN
            record_id := NEW.invoice_id;
        ELSIF TG_TABLE_NAME = 'ap_payments_all' THEN
            record_id := NEW.payment_id;
        ELSIF TG_TABLE_NAME = 'po_headers_all' THEN
            record_id := NEW.po_header_id;
        ELSIF TG_TABLE_NAME = 'po_lines_all' THEN
            record_id := NEW.po_line_id;
        ELSE
            record_id := NEW.id;
        END IF;
        
        payload := '{"table":"' || TG_TABLE_NAME || '","operation":"' || TG_OP || '","record_id":"' || COALESCE(record_id::text, 'null') || '"}';
        PERFORM pg_notify('neo4j_rtr_sync', payload);
        INSERT INTO rtr_sync_log (table_name, operation, record_id, status) 
        VALUES (TG_TABLE_NAME, TG_OP, record_id, 'pending');
        RETURN NEW;
    ELSE
        IF TG_TABLE_NAME = 'ap_invoices_all' THEN
            record_id := OLD.invoice_id;
        ELSIF TG_TABLE_NAME = 'ap_payments_all' THEN
            record_id := OLD.payment_id;
        ELSIF TG_TABLE_NAME = 'po_headers_all' THEN
            record_id := OLD.po_header_id;
        ELSIF TG_TABLE_NAME = 'po_lines_all' THEN
            record_id := OLD.po_line_id;
        ELSE
            record_id := OLD.id;
        END IF;
        
        payload := '{"table":"' || TG_TABLE_NAME || '","operation":"' || TG_OP || '","record_id":"' || COALESCE(record_id::text, 'null') || '"}';
        PERFORM pg_notify('neo4j_rtr_sync', payload);
        INSERT INTO rtr_sync_log (table_name, operation, record_id, status) 
        VALUES (TG_TABLE_NAME, TG_OP, record_id, 'pending');
        RETURN OLD;
    END IF;
END;
$func$ LANGUAGE plpgsql;

-- 3. AP 模块触发器（只针对存在的表）
DROP TRIGGER IF EXISTS ap_invoices_rtr ON ap_invoices_all;
CREATE TRIGGER ap_invoices_rtr
AFTER INSERT OR UPDATE OR DELETE ON ap_invoices_all
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

DROP TRIGGER IF EXISTS ap_payments_rtr ON ap_payments_all;
CREATE TRIGGER ap_payments_rtr
AFTER INSERT OR UPDATE OR DELETE ON ap_payments_all
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

-- 5. 验证
SELECT COUNT(*) AS total_triggers FROM pg_trigger WHERE tgname LIKE '%_rtr';
