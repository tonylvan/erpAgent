-- RTR 触发器修复版 - 发送完整数据
-- 先删除旧触发器
DROP TRIGGER IF EXISTS ap_invoices_rtr ON ap_invoices_all;
DROP TRIGGER IF EXISTS ap_payments_rtr ON ap_payments_all;
DROP TRIGGER IF EXISTS po_headers_rtr ON po_headers_all;
DROP TRIGGER IF EXISTS po_lines_rtr ON po_lines_all;

-- 删除旧函数
DROP FUNCTION IF EXISTS notify_neo4j_sync() CASCADE;

-- 创建新函数（发送完整数据）
CREATE OR REPLACE FUNCTION notify_neo4j_sync() 
RETURNS TRIGGER AS $func$
DECLARE
    payload TEXT;
    record_id BIGINT;
    record_data JSONB;
BEGIN
    IF TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN
        -- 获取主键
        IF TG_TABLE_NAME = 'ap_invoices_all' THEN
            record_id := NEW.invoice_id;
        ELSIF TG_TABLE_NAME = 'ap_payments_all' THEN
            record_id := NEW.payment_id;
        ELSIF TG_TABLE_NAME = 'po_headers_all' THEN
            record_id := NEW.po_header_id;
        ELSIF TG_TABLE_NAME = 'po_lines_all' THEN
            record_id := NEW.po_line_id;
        ELSE
            record_id := COALESCE(NEW.id, 0);
        END IF;
        
        -- 获取完整记录数据
        record_data := to_jsonb(CASE WHEN TG_OP = 'INSERT' OR TG_OP = 'UPDATE' THEN NEW ELSE OLD END);
        
        -- 构建完整 payload
        payload := json_build_object(
            'table', TG_TABLE_NAME,
            'operation', TG_OP,
            'record_id', record_id,
            'data', record_data
        )::text;
        
        PERFORM pg_notify('neo4j_rtr_sync', payload);
        
        -- 记录日志
        INSERT INTO rtr_sync_log (table_name, operation, record_id, status) 
        VALUES (TG_TABLE_NAME, TG_OP, record_id, 'pending');
        
        RETURN CASE WHEN TG_OP = 'DELETE' THEN OLD ELSE NEW END;
    ELSE
        -- DELETE
        IF TG_TABLE_NAME = 'ap_invoices_all' THEN
            record_id := OLD.invoice_id;
        ELSIF TG_TABLE_NAME = 'ap_payments_all' THEN
            record_id := OLD.payment_id;
        ELSIF TG_TABLE_NAME = 'po_headers_all' THEN
            record_id := OLD.po_header_id;
        ELSIF TG_TABLE_NAME = 'po_lines_all' THEN
            record_id := OLD.po_line_id;
        ELSE
            record_id := COALESCE(OLD.id, 0);
        END IF;
        
        record_data := to_jsonb(OLD);
        
        payload := json_build_object(
            'table', TG_TABLE_NAME,
            'operation', TG_OP,
            'record_id', record_id,
            'data', record_data
        )::text;
        
        PERFORM pg_notify('neo4j_rtr_sync', payload);
        
        INSERT INTO rtr_sync_log (table_name, operation, record_id, status) 
        VALUES (TG_TABLE_NAME, TG_OP, record_id, 'pending');
        
        RETURN OLD;
    END IF;
END;
$func$ LANGUAGE plpgsql;

-- 重新创建触发器
CREATE TRIGGER ap_invoices_rtr
AFTER INSERT OR UPDATE OR DELETE ON ap_invoices_all
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

CREATE TRIGGER ap_payments_rtr
AFTER INSERT OR UPDATE OR DELETE ON ap_payments_all
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

CREATE TRIGGER po_headers_rtr
AFTER INSERT OR UPDATE OR DELETE ON po_headers_all
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

CREATE TRIGGER po_lines_rtr
AFTER INSERT OR UPDATE OR DELETE ON po_lines_all
FOR EACH ROW EXECUTE FUNCTION notify_neo4j_sync();

-- 验证
SELECT COUNT(*) AS total_triggers FROM pg_trigger WHERE tgname LIKE '%_rtr';
