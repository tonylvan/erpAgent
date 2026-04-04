-- ============================================
-- GSD 智能问数 - P0 功能数据库表
-- ============================================
-- 1. 用户认证与权限管理
-- 2. 查询历史与收藏持久化
-- 3. 数据刷新与缓存策略
-- ============================================

-- ==================== 1. 用户认证与权限管理 ====================

-- 用户表
CREATE TABLE IF NOT EXISTS sys_users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100),
    password_hash VARCHAR(64) NOT NULL,
    role VARCHAR(20) DEFAULT 'readonly',  -- admin/finance/procurement/sales/readonly
    department VARCHAR(50),
    is_active BOOLEAN DEFAULT true,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户角色权限表
CREATE TABLE IF NOT EXISTS sys_roles (
    role_id SERIAL PRIMARY KEY,
    role_name VARCHAR(20) UNIQUE NOT NULL,
    permissions TEXT[],  -- 权限数组：['read', 'write', 'delete', 'admin']
    description VARCHAR(200),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 审计日志表
CREATE TABLE IF NOT EXISTS sys_audit_logs (
    log_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES sys_users(user_id),
    action VARCHAR(50) NOT NULL,  -- LOGIN/LOGOUT/QUERY/EXPORT/DELETE
    resource VARCHAR(100),  -- 操作的资源（表名/API 路径）
    ip_address VARCHAR(45),
    user_agent TEXT,
    request_body JSONB,
    response_status INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_sys_users_username ON sys_users(username);
CREATE INDEX idx_sys_users_role ON sys_users(role);
CREATE INDEX idx_sys_audit_logs_user_id ON sys_audit_logs(user_id);
CREATE INDEX idx_sys_audit_logs_action ON sys_audit_logs(action);
CREATE INDEX idx_sys_audit_logs_created_at ON sys_audit_logs(created_at DESC);


-- ==================== 2. 查询历史与收藏持久化 ====================

-- 查询历史表
CREATE TABLE IF NOT EXISTS query_history (
    query_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES sys_users(user_id),
    query_text TEXT NOT NULL,  -- 用户的自然语言查询
    sql_query TEXT,  -- 生成的 SQL
    result_snapshot JSONB,  -- 结果快照（前 100 条）
    result_type VARCHAR(20),  -- table/chart/stats/text
    result_count INTEGER,  -- 结果总数
    execution_time_ms INTEGER,  -- 执行时间（毫秒）
    cache_hit BOOLEAN DEFAULT false,  -- 是否命中缓存
    query_hash VARCHAR(64),  -- 查询哈希（用于去重）
    ip_address VARCHAR(45),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 收藏查询表
CREATE TABLE IF NOT EXISTS saved_queries (
    saved_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES sys_users(user_id),
    query_id INTEGER REFERENCES query_history(query_id),
    title VARCHAR(200) NOT NULL,  -- 自定义标题
    description TEXT,  -- 描述
    tags TEXT[],  -- 标签数组
    is_public BOOLEAN DEFAULT false,  -- 是否公开分享
    view_count INTEGER DEFAULT 0,  -- 查看次数
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 查询点赞/点踩表
CREATE TABLE IF NOT EXISTS query_feedback (
    feedback_id SERIAL PRIMARY KEY,
    query_id INTEGER REFERENCES query_history(query_id),
    user_id INTEGER REFERENCES sys_users(user_id),
    feedback_type VARCHAR(10) NOT NULL,  -- 'like' 或 'dislike'
    comment TEXT,  -- 反馈意见
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(query_id, user_id)  -- 每个用户对每个查询只能反馈一次
);

-- 索引
CREATE INDEX idx_query_history_user_id ON query_history(user_id);
CREATE INDEX idx_query_history_created_at ON query_history(created_at DESC);
CREATE INDEX idx_query_history_query_hash ON query_history(query_hash);
CREATE INDEX idx_saved_queries_user_id ON saved_queries(user_id);
CREATE INDEX idx_saved_queries_tags ON saved_queries USING GIN(tags);
CREATE INDEX idx_query_feedback_query_id ON query_feedback(query_id);


-- ==================== 3. 数据刷新与缓存策略 ====================

-- 缓存元数据表
CREATE TABLE IF NOT EXISTS cache_metadata (
    cache_id SERIAL PRIMARY KEY,
    cache_key VARCHAR(200) UNIQUE NOT NULL,  -- 缓存键（如：gsd:query:xxx）
    cache_type VARCHAR(20),  -- query/stats/chart
    query_text TEXT,  -- 原始查询
    result_data JSONB,  -- 缓存的数据
    result_type VARCHAR(20),  -- table/chart/stats/text
    hit_count INTEGER DEFAULT 0,  -- 命中次数
    size_bytes INTEGER,  -- 缓存大小（字节）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,  -- 过期时间
    last_accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 数据更新时间记录表
CREATE TABLE IF NOT EXISTS data_refresh_log (
    refresh_id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) NOT NULL,  -- 表名
    operation VARCHAR(20),  -- INSERT/UPDATE/DELETE
    record_count INTEGER,  -- 影响的记录数
    refresh_type VARCHAR(20),  -- auto/manual/scheduled
    triggered_by VARCHAR(50),  -- 触发者（用户/system/cron）
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    status VARCHAR(20),  -- success/failed/running
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 数据表监控配置表
CREATE TABLE IF NOT EXISTS table_monitor_config (
    config_id SERIAL PRIMARY KEY,
    table_name VARCHAR(100) UNIQUE NOT NULL,
    monitor_enabled BOOLEAN DEFAULT true,  -- 是否监控
    refresh_interval_minutes INTEGER DEFAULT 30,  -- 刷新间隔（分钟）
    cache_ttl_minutes INTEGER DEFAULT 15,  -- 缓存 TTL（分钟）
    priority INTEGER DEFAULT 5,  -- 优先级（1-10，10 最高）
    last_refresh_at TIMESTAMP,
    next_refresh_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX idx_cache_metadata_cache_key ON cache_metadata(cache_key);
CREATE INDEX idx_cache_metadata_expires_at ON cache_metadata(expires_at);
CREATE INDEX idx_data_refresh_log_table_name ON data_refresh_log(table_name);
CREATE INDEX idx_data_refresh_log_created_at ON data_refresh_log(created_at DESC);


-- ==================== 4. 初始化数据 ====================

-- 插入默认角色
INSERT INTO sys_roles (role_name, permissions, description) VALUES
('admin', ARRAY['read', 'write', 'delete', 'admin'], '系统管理员 - 所有权限'),
('finance', ARRAY['read', 'write'], '财务人员 - 读写权限'),
('procurement', ARRAY['read', 'write'], '采购人员 - 读写权限'),
('sales', ARRAY['read'], '销售人员 - 只读权限'),
('readonly', ARRAY['read'], '只读用户 - 仅查询权限')
ON CONFLICT (role_name) DO NOTHING;

-- 插入默认管理员账户（密码：admin123）
-- 密码哈希：SHA256('admin123gsd-salt-2026')
INSERT INTO sys_users (username, email, password_hash, role, department) VALUES
('admin', 'admin@gsd.com', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', 'admin', 'IT'),
('finance_user', 'finance@gsd.com', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', 'finance', '财务部'),
('procurement_user', 'procurement@gsd.com', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', 'procurement', '采购部'),
('sales_user', 'sales@gsd.com', 'a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3', 'sales', '销售部')
ON CONFLICT (username) DO NOTHING;

-- 插入默认表监控配置
INSERT INTO table_monitor_config (table_name, refresh_interval_minutes, cache_ttl_minutes, priority) VALUES
('ap_invoice_po_matches', 30, 15, 8),
('gl_balances', 60, 30, 9),
('ar_customer_balances', 30, 15, 8),
('inv_lot_numbers_extended', 120, 60, 6),
('om_shipment_details_extended', 30, 15, 7),
('po_approval_history', 60, 30, 7)
ON CONFLICT (table_name) DO UPDATE SET 
    refresh_interval_minutes = EXCLUDED.refresh_interval_minutes,
    cache_ttl_minutes = EXCLUDED.cache_ttl_minutes;


-- ==================== 5. 视图和函数 ====================

-- 查询历史统计视图
CREATE OR REPLACE VIEW v_query_stats AS
SELECT 
    DATE(created_at) as query_date,
    COUNT(*) as total_queries,
    COUNT(DISTINCT user_id) as unique_users,
    AVG(execution_time_ms) as avg_execution_time,
    SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END) as cache_hits,
    ROUND(100.0 * SUM(CASE WHEN cache_hit THEN 1 ELSE 0 END) / COUNT(*), 2) as cache_hit_rate
FROM query_history
WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(created_at)
ORDER BY query_date DESC;

-- 热门查询视图
CREATE OR REPLACE VIEW v_popular_queries AS
SELECT 
    q.query_id,
    q.query_text,
    q.result_type,
    COUNT(s.saved_id) as save_count,
    COUNT(f.feedback_id) FILTER (WHERE f.feedback_type = 'like') as like_count,
    COUNT(f.feedback_id) FILTER (WHERE f.feedback_type = 'dislike') as dislike_count,
    q.created_at
FROM query_history q
LEFT JOIN saved_queries s ON q.query_id = s.query_id
LEFT JOIN query_feedback f ON q.query_id = f.query_id
WHERE q.created_at >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY q.query_id, q.query_text, q.result_type, q.created_at
ORDER BY save_count DESC, like_count DESC
LIMIT 20;

-- 缓存命中率视图
CREATE OR REPLACE VIEW v_cache_performance AS
SELECT 
    cache_type,
    COUNT(*) as total_caches,
    SUM(hit_count) as total_hits,
    ROUND(100.0 * AVG(hit_count), 2) as avg_hits_per_cache,
    ROUND(100.0 * SUM(CASE WHEN hit_count > 0 THEN 1 ELSE 0 END) / COUNT(*), 2) as active_rate,
    SUM(size_bytes) as total_size_bytes
FROM cache_metadata
GROUP BY cache_type;


-- ==================== 6. 权限说明 ====================

/*
角色权限矩阵:

权限        | admin | finance | procurement | sales | readonly
-----------|-------|---------|-------------|-------|----------
read       |   ✓   |    ✓    |      ✓      |   ✓   |    ✓
write      |   ✓   |    ✓    |      ✓      |   ✗   |    ✗
delete     |   ✓   |    ✗    |      ✗      |   ✗   |    ✗
admin      |   ✓   |    ✗    |      ✗      |   ✗   |    ✗
export     |   ✓   |    ✓    |      ✓      |   ✓   |    ✗
share      |   ✓   |    ✓    |      ✓      |   ✓   |    ✗

数据访问范围:
- admin: 所有数据
- finance: 财务相关（AP/GL/AR）
- procurement: 采购相关（AP/PO/INV）
- sales: 销售相关（AR/OM）只读
- readonly: 所有数据只读
*/

-- 完成提示
SELECT '✅ P0 数据库表创建完成！' as status;
