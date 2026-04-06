-- 工单中心 v3.0 数据库迁移脚本
-- 创建时间：2026-04-06
-- 功能：工单评论、通知、工作流日志表

-- 1. 工单评论表
CREATE TABLE IF NOT EXISTS ticket_comments (
    id VARCHAR(50) PRIMARY KEY,
    ticket_id VARCHAR(50) NOT NULL,
    parent_id VARCHAR(50) DEFAULT NULL,  -- 回复评论时指向父评论
    author_id VARCHAR(50) NOT NULL,
    author_name VARCHAR(100) NOT NULL,
    author_email VARCHAR(100) DEFAULT NULL,
    content TEXT NOT NULL,
    is_internal BOOLEAN DEFAULT FALSE,  -- 是否内部评论（用户不可见）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_edited BOOLEAN DEFAULT FALSE,
    
    -- 外键约束
    CONSTRAINT fk_ticket_comments_ticket 
        FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE,
    CONSTRAINT fk_ticket_comments_parent 
        FOREIGN KEY (parent_id) REFERENCES ticket_comments(id) ON DELETE CASCADE,
    
    -- 索引
    INDEX idx_ticket_comments_ticket_id (ticket_id),
    INDEX idx_ticket_comments_author_id (author_id),
    INDEX idx_ticket_comments_created_at (created_at)
);

-- 2. 工单通知表
CREATE TABLE IF NOT EXISTS ticket_notifications (
    id VARCHAR(50) PRIMARY KEY,
    ticket_id VARCHAR(50) NOT NULL,
    user_id VARCHAR(50) NOT NULL,
    user_name VARCHAR(100) NOT NULL,
    user_email VARCHAR(100) DEFAULT NULL,
    notification_type VARCHAR(50) NOT NULL,  -- ASSIGN, TRANSFER, ESCALATE, RESOLVE, CLOSE, COMMENT, MENTION
    channel VARCHAR(50) NOT NULL,  -- IN_APP, EMAIL, WECHAT
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP DEFAULT NULL,
    sent_at TIMESTAMP DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 外键约束
    CONSTRAINT fk_ticket_notifications_ticket 
        FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE,
    
    -- 索引
    INDEX idx_ticket_notifications_user_id (user_id),
    INDEX idx_ticket_notifications_ticket_id (ticket_id),
    INDEX idx_ticket_notifications_is_read (is_read),
    INDEX idx_ticket_notifications_created_at (created_at)
);

-- 3. 工单工作流日志表
CREATE TABLE IF NOT EXISTS ticket_workflow_logs (
    id VARCHAR(50) PRIMARY KEY,
    ticket_id VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,  -- ASSIGN, TRANSFER, ESCALATE, RESOLVE, CLOSE, STATUS_CHANGE
    from_status VARCHAR(50) DEFAULT NULL,
    to_status VARCHAR(50) DEFAULT NULL,
    operator_id VARCHAR(50) NOT NULL,
    operator_name VARCHAR(100) NOT NULL,
    comment TEXT DEFAULT NULL,
    metadata JSON DEFAULT NULL,  -- 附加信息（如旧负责人、新负责人等）
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 外键约束
    CONSTRAINT fk_ticket_workflow_logs_ticket 
        FOREIGN KEY (ticket_id) REFERENCES tickets(id) ON DELETE CASCADE,
    
    -- 索引
    INDEX idx_ticket_workflow_logs_ticket_id (ticket_id),
    INDEX idx_ticket_workflow_logs_action (action),
    INDEX idx_ticket_workflow_logs_created_at (created_at)
);

-- 4. 工单 SLA 配置表
CREATE TABLE IF NOT EXISTS ticket_sla_config (
    id VARCHAR(50) PRIMARY KEY,
    priority VARCHAR(50) NOT NULL UNIQUE,  -- URGENT, HIGH, MEDIUM, LOW
    response_time_hours INT NOT NULL,  -- 响应时间（小时）
    resolution_time_hours INT NOT NULL,  -- 解决时间（小时）
    warning_threshold_minutes INT DEFAULT 30,  -- 提前预警时间（分钟）
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. 插入默认 SLA 配置
INSERT INTO ticket_sla_config (id, priority, response_time_hours, resolution_time_hours, warning_threshold_minutes) 
VALUES 
    ('sla_urgent', 'URGENT', 0.5, 2, 30),
    ('sla_high', 'HIGH', 2, 24, 60),
    ('sla_medium', 'MEDIUM', 8, 72, 120),
    ('sla_low', 'LOW', 24, 168, 240)
ON CONFLICT (priority) DO UPDATE SET
    response_time_hours = EXCLUDED.response_time_hours,
    resolution_time_hours = EXCLUDED.resolution_time_hours,
    warning_threshold_minutes = EXCLUDED.warning_threshold_minutes,
    updated_at = CURRENT_TIMESTAMP;

-- 6. 工单派单规则表
CREATE TABLE IF NOT EXISTS ticket_assignment_rules (
    id VARCHAR(50) PRIMARY KEY,
    rule_name VARCHAR(100) NOT NULL,
    rule_type VARCHAR(50) NOT NULL,  -- ROUND_ROBIN, SKILL_BASED, WORKLOAD_BASED, CUSTOM
    priority INT DEFAULT 0,  -- 规则优先级（数字越大优先级越高）
    conditions JSON DEFAULT NULL,  -- 触发条件（如 issue_type = 'BUG'）
    config JSON DEFAULT NULL,  -- 规则配置（如负责人列表、技能要求等）
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 索引
    INDEX idx_ticket_assignment_rules_type (rule_type),
    INDEX idx_ticket_assignment_rules_priority (priority),
    INDEX idx_ticket_assignment_rules_active (is_active)
);

-- 7. 工单负责人技能表
CREATE TABLE IF NOT EXISTS ticket_assignee_skills (
    id VARCHAR(50) PRIMARY KEY,
    assignee_id VARCHAR(50) NOT NULL,
    assignee_name VARCHAR(100) NOT NULL,
    skill_tags JSON DEFAULT NULL,  -- 技能标签列表
    max_workload INT DEFAULT 10,  -- 最大并发工单数
    current_workload INT DEFAULT 0,  -- 当前工单数
    is_available BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- 外键约束
    UNIQUE KEY uk_assignee_id (assignee_id),
    
    -- 索引
    INDEX idx_ticket_assignee_skills_available (is_available)
);

-- 迁移完成提示
SELECT '工单中心 v3.0 数据库迁移完成！' AS migration_status;
