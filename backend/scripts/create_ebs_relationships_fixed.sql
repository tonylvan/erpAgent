-- ============================================================
-- Oracle EBS 表关系扩展脚本（修正版）
-- ============================================================
-- 目标：基于现有表添加缺失的关系表
-- 数据库：PostgreSQL 14+
-- 创建日期：2026-04-04
-- ============================================================

BEGIN;

-- ============================================================
-- 1. AP 模块关系扩展
-- ============================================================

-- 发票与 PO 匹配关系
CREATE TABLE IF NOT EXISTS ap_invoice_po_matches (
    match_id              BIGSERIAL PRIMARY KEY,
    invoice_id            BIGINT NOT NULL,
    invoice_line_id       BIGINT,
    po_line_id            BIGINT NOT NULL,
    po_distribution_id    BIGINT,
    receipt_id            BIGINT,
    matched_quantity      NUMERIC(15,2),
    matched_amount        NUMERIC(15,2),
    match_date            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    match_type            VARCHAR(30),  -- PO/RECEIPT
    status                VARCHAR(20) DEFAULT 'ACTIVE',
    created_by            BIGINT,
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE ap_invoice_po_matches IS '发票与 PO 三向匹配关系';
COMMENT ON COLUMN ap_invoice_po_matches.match_type IS '匹配类型：PO/RECEIPT';

-- 发票与总账接口
CREATE TABLE IF NOT EXISTS ap_gl_interface (
    interface_id          BIGSERIAL PRIMARY KEY,
    invoice_id            BIGINT NOT NULL,
    distribution_id       BIGINT,
    gl_batch_name         VARCHAR(100),
    gl_period_name        VARCHAR(30),
    accounting_date       DATE,
    dr_amount             NUMERIC(15,2) DEFAULT 0,
    cr_amount             NUMERIC(15,2) DEFAULT 0,
    code_combination_id   BIGINT,
    status                VARCHAR(20) DEFAULT 'PENDING',
    error_message         TEXT,
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE ap_gl_interface IS '应付总账接口表';
COMMENT ON COLUMN ap_gl_interface.status IS '状态：PENDING/PROCESSED/ERROR';

-- 付款与发票分配
CREATE TABLE IF NOT EXISTS ap_payment_invoice_dists (
    payment_dist_id       BIGSERIAL PRIMARY KEY,
    payment_id            BIGINT NOT NULL,
    invoice_id            BIGINT NOT NULL,
    distribution_id       BIGINT,
    amount                NUMERIC(15,2) NOT NULL,
    discount_amount       NUMERIC(15,2) DEFAULT 0,
    payment_date          DATE,
    gl_posted_flag        VARCHAR(1) DEFAULT 'N',
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE ap_payment_invoice_dists IS '付款与发票分配关系';

-- ============================================================
-- 2. PO 模块关系扩展
-- ============================================================

-- 采购订单审批历史
CREATE TABLE IF NOT EXISTS po_approval_history (
    approval_id           BIGSERIAL PRIMARY KEY,
    po_header_id          BIGINT NOT NULL,
    approver_id           BIGINT NOT NULL,
    approval_level        INT,
    approval_status       VARCHAR(20),  -- APPROVED/REJECTED/PENDING
    approval_date         TIMESTAMP,
    comments              TEXT,
    delegation_from_id    BIGINT,
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE po_approval_history IS '采购订单审批历史';
COMMENT ON COLUMN po_approval_history.approval_status IS '审批状态：APPROVED/REJECTED/PENDING';

-- 采购订单变更历史
CREATE TABLE IF NOT EXISTS po_change_orders (
    change_order_id       BIGSERIAL PRIMARY KEY,
    po_header_id          BIGINT NOT NULL,
    change_number         INT NOT NULL,
    change_type           VARCHAR(30),  -- QUANTITY/PRICE/DATE
    old_value             TEXT,
    new_value             TEXT,
    change_reason         TEXT,
    changed_by            BIGINT,
    change_date           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    approval_status       VARCHAR(20) DEFAULT 'PENDING'
);
COMMENT ON TABLE po_change_orders IS '采购订单变更历史';

-- 采购申请与 PO 关联
CREATE TABLE IF NOT EXISTS po_requisition_links (
    req_link_id           BIGSERIAL PRIMARY KEY,
    requisition_line_id   BIGINT NOT NULL,
    po_line_id            BIGINT NOT NULL,
    linked_quantity       NUMERIC(15,2),
    linked_amount         NUMERIC(15,2),
    link_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status                VARCHAR(20) DEFAULT 'ACTIVE'
);
COMMENT ON TABLE po_requisition_links IS '采购申请与 PO 关联';

-- 供应商绩效评估
CREATE TABLE IF NOT EXISTS vendor_performance_scores (
    score_id              BIGSERIAL PRIMARY KEY,
    supplier_id           BIGINT NOT NULL,
    supplier_site_id      BIGINT,
    evaluation_period     VARCHAR(30),  -- YEAR/MONTH
    quality_score         NUMERIC(5,2) DEFAULT 0,  -- 质量评分
    delivery_score        NUMERIC(5,2) DEFAULT 0,  -- 交付评分
    price_score           NUMERIC(5,2) DEFAULT 0,  -- 价格评分
    service_score         NUMERIC(5,2) DEFAULT 0,  -- 服务评分
    overall_score         NUMERIC(5,2) DEFAULT 0,  -- 综合评分
    evaluation_date       DATE,
    evaluated_by          BIGINT,
    comments              TEXT,
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE vendor_performance_scores IS '供应商绩效评估';

-- ============================================================
-- 3. GL 模块关系扩展
-- ============================================================

-- 总账批次
CREATE TABLE IF NOT EXISTS gl_batches (
    batch_id              BIGSERIAL PRIMARY KEY,
    batch_name            VARCHAR(100) NOT NULL,
    ledger_id             BIGINT,
    period_name           VARCHAR(30),
    batch_type            VARCHAR(30),  -- MANUAL/AUTO/IMPORT
    status                VARCHAR(20) DEFAULT 'PENDING',
    total_dr_amount       NUMERIC(15,2) DEFAULT 0,
    total_cr_amount       NUMERIC(15,2) DEFAULT 0,
    posted_date           TIMESTAMP,
    posted_by             BIGINT,
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE gl_batches IS '总账批次';

-- 总账日记账行
CREATE TABLE IF NOT EXISTS gl_journal_lines (
    line_id               BIGSERIAL PRIMARY KEY,
    je_header_id          BIGINT NOT NULL,
    line_number           INT NOT NULL,
    code_combination_id   BIGINT NOT NULL,
    line_description      VARCHAR(255),
    dr_amount             NUMERIC(15,2) DEFAULT 0,
    cr_amount             NUMERIC(15,2) DEFAULT 0,
    reference_1           VARCHAR(100),
    reference_2           VARCHAR(100),
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE gl_journal_lines IS '总账日记账行';

-- 总账余额
CREATE TABLE IF NOT EXISTS gl_balances (
    balance_id            BIGSERIAL PRIMARY KEY,
    code_combination_id   BIGINT NOT NULL,
    period_name           VARCHAR(30) NOT NULL,
    ledger_id             BIGINT,
    balance_type          VARCHAR(20),  -- ACTUAL/BUDGET/ENCUMBRANCE
    period_year           INT,
    period_num            INT,
    begin_balance_dr      NUMERIC(15,2) DEFAULT 0,
    begin_balance_cr      NUMERIC(15,2) DEFAULT 0,
    period_dr             NUMERIC(15,2) DEFAULT 0,
    period_cr             NUMERIC(15,2) DEFAULT 0,
    end_balance_dr        NUMERIC(15,2) DEFAULT 0,
    end_balance_cr        NUMERIC(15,2) DEFAULT 0,
    last_updated          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE gl_balances IS '总账余额';

-- 科目组合（多段）
CREATE TABLE IF NOT EXISTS gl_code_combination_segments (
    segment_id            BIGSERIAL PRIMARY KEY,
    code_combination_id   BIGINT NOT NULL,
    segment_num           INT NOT NULL,  -- 1,2,3...
    segment_name          VARCHAR(50),   -- COMPANY/COST_CENTER/ACCOUNT...
    segment_value         VARCHAR(100),
    segment_description   VARCHAR(255)
);
COMMENT ON TABLE gl_code_combination_segments IS '科目组合段';

-- 期间状态
CREATE TABLE IF NOT EXISTS gl_period_statuses_extended (
    status_id             BIGSERIAL PRIMARY KEY,
    ledger_id             BIGINT NOT NULL,
    period_name           VARCHAR(30) NOT NULL,
    period_type           VARCHAR(30),   -- MONTH/QUARTER/YEAR
    period_status         VARCHAR(20),   -- OPEN/CLOSED/FUTURE
    open_date             DATE,
    close_date            DATE,
    closed_by             BIGINT,
    last_updated          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE gl_period_statuses_extended IS '期间状态扩展';

-- 子账来源
CREATE TABLE IF NOT EXISTS gl_subledger_sources (
    source_id             BIGSERIAL PRIMARY KEY,
    ledger_id             BIGINT,
    subledger_type        VARCHAR(30),  -- AP/AR/PO/INV/OM
    source_table          VARCHAR(100),
    source_id_col         VARCHAR(100),
    gl_batch_id           BIGINT,
    transfer_status       VARCHAR(20) DEFAULT 'PENDING',
    transfer_date         TIMESTAMP,
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE gl_subledger_sources IS '子账来源';

-- ============================================================
-- 4. AR 模块关系扩展
-- ============================================================

-- 收款与发票应用
CREATE TABLE IF NOT EXISTS ar_receipt_applications_extended (
    application_id        BIGSERIAL PRIMARY KEY,
    receipt_id            BIGINT NOT NULL,
    invoice_id            BIGINT NOT NULL,
    applied_amount        NUMERIC(15,2) NOT NULL,
    discount_amount       NUMERIC(15,2) DEFAULT 0,
    application_date      DATE,
    application_type      VARCHAR(30),  -- CASH/ADJUSTMENT/CHARGEBACK
    status                VARCHAR(20) DEFAULT 'ACTIVE',
    gl_posted_flag        VARCHAR(1) DEFAULT 'N',
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE ar_receipt_applications_extended IS '收款与发票应用扩展';

-- 客户配置（信用额度）
CREATE TABLE IF NOT EXISTS ar_customer_profiles_extended (
    profile_id            BIGSERIAL PRIMARY KEY,
    customer_id           BIGINT NOT NULL,
    customer_site_id      BIGINT,
    credit_limit          NUMERIC(15,2) DEFAULT 0,
    credit_currency       VARCHAR(10) DEFAULT 'CNY',
    payment_terms_id      BIGINT,
    discount_percent      NUMERIC(5,2) DEFAULT 0,
    dunning_letters_flag  VARCHAR(1) DEFAULT 'Y',
    statement_cycle       VARCHAR(20),  -- WEEKLY/MONTHLY
    last_review_date      DATE,
    next_review_date      DATE,
    reviewed_by           BIGINT,
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE ar_customer_profiles_extended IS '客户配置扩展';

-- 客户余额
CREATE TABLE IF NOT EXISTS ar_customer_balances (
    balance_id            BIGSERIAL PRIMARY KEY,
    customer_id           BIGINT NOT NULL,
    balance_date          DATE NOT NULL,
    currency_code         VARCHAR(10) DEFAULT 'CNY',
    outstanding_balance   NUMERIC(15,2) DEFAULT 0,
    current_balance       NUMERIC(15,2) DEFAULT 0,
    balance_1_30          NUMERIC(15,2) DEFAULT 0,  -- 1-30 天
    balance_31_60         NUMERIC(15,2) DEFAULT 0,  -- 31-60 天
    balance_61_90         NUMERIC(15,2) DEFAULT 0,  -- 61-90 天
    balance_over_90       NUMERIC(15,2) DEFAULT 0,  -- 90 天以上
    last_updated          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE ar_customer_balances IS '客户余额账龄分析';

-- 收入确认
CREATE TABLE IF NOT EXISTS ar_revenue_recognition (
    recognition_id        BIGSERIAL PRIMARY KEY,
    invoice_id            BIGINT NOT NULL,
    invoice_line_id       BIGINT,
    revenue_amount        NUMERIC(15,2) NOT NULL,
    recognition_method    VARCHAR(30),  -- IMMEDIATE/OVER_TIME
    start_date            DATE,
    end_date              DATE,
    recognized_amount     NUMERIC(15,2) DEFAULT 0,
    remaining_amount      NUMERIC(15,2) DEFAULT 0,
    last_recognition_date DATE,
    status                VARCHAR(20) DEFAULT 'PENDING',
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE ar_revenue_recognition IS '收入确认';

-- 催收案例
CREATE TABLE IF NOT EXISTS ar_collection_cases (
    case_id               BIGSERIAL PRIMARY KEY,
    customer_id           BIGINT NOT NULL,
    invoice_id            BIGINT,
    case_status           VARCHAR(20) DEFAULT 'OPEN',  -- OPEN/CLOSED/ESCALATED
    priority              VARCHAR(10) DEFAULT 'MEDIUM',  -- LOW/MEDIUM/HIGH
    assigned_to           BIGINT,
    opened_date           DATE,
    closed_date           DATE,
    total_amount          NUMERIC(15,2),
    resolved_amount       NUMERIC(15,2) DEFAULT 0,
    resolution            TEXT,
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE ar_collection_cases IS '催收案例';

-- 催收活动历史
CREATE TABLE IF NOT EXISTS ar_collection_activities (
    activity_id           BIGSERIAL PRIMARY KEY,
    case_id               BIGINT NOT NULL,
    activity_type         VARCHAR(30),  -- CALL/EMAIL/LETTER/LEGAL
    activity_date         DATE,
    contact_person        VARCHAR(100),
    contact_method        VARCHAR(30),  -- PHONE/EMAIL/MAIL
    promised_amount       NUMERIC(15,2),
    promised_date         DATE,
    follow_up_date        DATE,
    notes                 TEXT,
    created_by            BIGINT,
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE ar_collection_activities IS '催收活动历史';

-- ============================================================
-- 5. INV 模块关系扩展
-- ============================================================

-- 子库存
CREATE TABLE IF NOT EXISTS inv_subinventories_extended (
    subinv_id             BIGSERIAL PRIMARY KEY,
    organization_id       BIGINT NOT NULL,
    subinventory_code     VARCHAR(50) NOT NULL,
    description           VARCHAR(255),
    subinventory_type     VARCHAR(30),  -- STORAGE/PRODUCTION/RETURN
    locator_control       VARCHAR(20),  -- PREDETERMINED/DYNAMIC
    picking_order         INT,
    status                VARCHAR(20) DEFAULT 'ACTIVE',
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE inv_subinventories_extended IS '子库存扩展';

-- 库存货位
CREATE TABLE IF NOT EXISTS inv_item_locators_extended (
    locator_id            BIGSERIAL PRIMARY KEY,
    subinventory_id       BIGINT NOT NULL,
    organization_id       BIGINT NOT NULL,
    locator_code          VARCHAR(100) NOT NULL,  -- 如：A-01-B-02-C-03
    segment1              VARCHAR(50),  -- 通道
    segment2              VARCHAR(50),  -- 货架
    segment3              VARCHAR(50),  -- 层
    segment4              VARCHAR(50),  -- 位
    status                VARCHAR(20) DEFAULT 'ACTIVE',
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE inv_item_locators_extended IS '库存货位扩展';

-- 批次管理
CREATE TABLE IF NOT EXISTS inv_lot_numbers_extended (
    lot_id                BIGSERIAL PRIMARY KEY,
    item_id               BIGINT NOT NULL,
    organization_id       BIGINT NOT NULL,
    lot_number            VARCHAR(100) NOT NULL,
    description           VARCHAR(255),
    generation_date       DATE,
    expiration_date       DATE,
    supplier_id           BIGINT,
    supplier_lot_number   VARCHAR(100),
    status                VARCHAR(20) DEFAULT 'ACTIVE',
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE inv_lot_numbers_extended IS '批次管理扩展';

-- 序列号
CREATE TABLE IF NOT EXISTS inv_serial_numbers_extended (
    serial_id             BIGSERIAL PRIMARY KEY,
    item_id               BIGINT NOT NULL,
    organization_id       BIGINT NOT NULL,
    serial_number         VARCHAR(100) NOT NULL,
    lot_id                BIGINT,
    status                VARCHAR(20) DEFAULT 'ACTIVE',  -- ACTIVE/INACTIVE/SCRAP
    current_location      VARCHAR(100),
    supplier_id           BIGINT,
    receipt_date          DATE,
    issue_date            DATE,
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE inv_serial_numbers_extended IS '序列号管理扩展';

-- 周期盘点
CREATE TABLE IF NOT EXISTS inv_cycle_counts_extended (
    count_id              BIGSERIAL PRIMARY KEY,
    organization_id       BIGINT NOT NULL,
    subinventory_id       BIGINT,
    count_name            VARCHAR(100) NOT NULL,
    count_type            VARCHAR(30),  -- REGULAR/RANDOM/CLASS
    count_frequency       VARCHAR(20),  -- DAILY/WEEKLY/MONTHLY
    last_count_date       DATE,
    next_count_date       DATE,
    status                VARCHAR(20) DEFAULT 'ACTIVE',
    created_by            BIGINT,
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE inv_cycle_counts_extended IS '周期盘点扩展';

-- 盘点调整
CREATE TABLE IF NOT EXISTS inv_cycle_count_adjustments (
    adjustment_id         BIGSERIAL PRIMARY KEY,
    count_id              BIGINT NOT NULL,
    item_id               BIGINT NOT NULL,
    locator_id            BIGINT,
    lot_id                BIGINT,
    serial_id             BIGINT,
    system_quantity       NUMERIC(15,2),
    actual_quantity       NUMERIC(15,2),
    adjustment_quantity   NUMERIC(15,2),
    adjustment_amount     NUMERIC(15,2),
    adjustment_reason     VARCHAR(255),
    approved_flag         VARCHAR(1) DEFAULT 'N',
    approved_by           BIGINT,
    approval_date         TIMESTAMP,
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE inv_cycle_count_adjustments IS '盘点调整';

-- ============================================================
-- 6. OM 模块关系扩展
-- ============================================================

-- 发运明细
CREATE TABLE IF NOT EXISTS om_shipment_details_extended (
    shipment_detail_id    BIGSERIAL PRIMARY KEY,
    shipment_id           BIGINT NOT NULL,
    order_line_id         BIGINT NOT NULL,
    shipped_quantity      NUMERIC(15,2),
    shipped_date          TIMESTAMP,
    carrier_code          VARCHAR(50),
    tracking_number       VARCHAR(100),
    delivery_date         DATE,
    status                VARCHAR(20) DEFAULT 'PENDING',  -- PENDING/SHIPPED/DELIVERED
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE om_shipment_details_extended IS '发运明细扩展';

-- 订单预留
CREATE TABLE IF NOT EXISTS om_order_reservations (
    reservation_id        BIGSERIAL PRIMARY KEY,
    order_line_id         BIGINT NOT NULL,
    item_id               BIGINT NOT NULL,
    organization_id       BIGINT NOT NULL,
    subinventory_id       BIGINT,
    locator_id            BIGINT,
    lot_id                BIGINT,
    reserved_quantity     NUMERIC(15,2) NOT NULL,
    reservation_date      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status                VARCHAR(20) DEFAULT 'ACTIVE',
    expiry_date           DATE
);
COMMENT ON TABLE om_order_reservations IS '订单预留';

-- 价格列表
CREATE TABLE IF NOT EXISTS om_price_lists_extended (
    price_list_id         BIGSERIAL PRIMARY KEY,
    price_list_name       VARCHAR(100) NOT NULL,
    description           VARCHAR(255),
    currency_code         VARCHAR(10) DEFAULT 'CNY',
    effective_start_date  DATE,
    effective_end_date    DATE,
    price_type            VARCHAR(30),  -- STANDARD/PROMOTIONAL/CUSTOMER
    status                VARCHAR(20) DEFAULT 'ACTIVE',
    approved_flag         VARCHAR(1) DEFAULT 'N',
    approved_by           BIGINT,
    approved_date         TIMESTAMP,
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE om_price_lists_extended IS '价格列表扩展';

-- 价格列表行
CREATE TABLE IF NOT EXISTS om_price_list_lines (
    line_id               BIGSERIAL PRIMARY KEY,
    price_list_id         BIGINT NOT NULL,
    item_id               BIGINT NOT NULL,
    line_number           INT NOT NULL,
    unit_price            NUMERIC(15,2) NOT NULL,
    currency_code         VARCHAR(10) DEFAULT 'CNY',
    start_date            DATE,
    end_date              DATE,
    minimum_quantity      NUMERIC(15,2) DEFAULT 1,
    break_type            VARCHAR(20),  -- FIXED/PERCENT
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE om_price_list_lines IS '价格列表行';

-- 订单折扣
CREATE TABLE IF NOT EXISTS om_order_discounts (
    discount_id           BIGSERIAL PRIMARY KEY,
    order_header_id       BIGINT,
    order_line_id         BIGINT,
    discount_type         VARCHAR(30),  -- PERCENT/AMOUNT
    discount_value        NUMERIC(15,2) NOT NULL,
    discount_amount       NUMERIC(15,2),
    reason_code           VARCHAR(50),
    reason_description    VARCHAR(255),
    approved_flag         VARCHAR(1) DEFAULT 'N',
    approved_by           BIGINT,
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE om_order_discounts IS '订单折扣';

-- 退货原因
CREATE TABLE IF NOT EXISTS om_return_reasons_extended (
    reason_id             BIGSERIAL PRIMARY KEY,
    reason_code           VARCHAR(50) NOT NULL,
    reason_name           VARCHAR(100) NOT NULL,
    reason_type           VARCHAR(30),  -- QUALITY/WRONG/DAMAGED/OTHER
    description           VARCHAR(255),
    active_flag           VARCHAR(1) DEFAULT 'Y',
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE om_return_reasons_extended IS '退货原因扩展';

-- ============================================================
-- 7. FND 模块关系扩展
-- ============================================================

-- 业务事件日志
CREATE TABLE IF NOT EXISTS fnd_business_events_log (
    event_id              BIGSERIAL PRIMARY KEY,
    event_name            VARCHAR(100) NOT NULL,
    event_type            VARCHAR(30),
    event_key             VARCHAR(100),
    event_data            JSONB,
    source_system         VARCHAR(50),
    source_id             BIGINT,
    occurred_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_flag        VARCHAR(1) DEFAULT 'N',
    processed_date        TIMESTAMP,
    error_message         TEXT
);
COMMENT ON TABLE fnd_business_events_log IS '业务事件日志';

-- 附件管理
CREATE TABLE IF NOT EXISTS fnd_attachments_extended (
    attachment_id         BIGSERIAL PRIMARY KEY,
    entity_name           VARCHAR(100) NOT NULL,  -- 如：AP_INVOICE/PO_ORDER
    entity_id             BIGINT NOT NULL,
    file_name             VARCHAR(255) NOT NULL,
    file_path             VARCHAR(500),
    file_type             VARCHAR(50),  -- PDF/IMAGE/EXCEL/WORD
    file_size             BIGINT,
    uploaded_by           BIGINT,
    upload_date           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description           VARCHAR(255),
    status                VARCHAR(20) DEFAULT 'ACTIVE'
);
COMMENT ON TABLE fnd_attachments_extended IS '附件管理扩展';

-- 工作流审批
CREATE TABLE IF NOT EXISTS fnd_workflow_approvals (
    approval_id           BIGSERIAL PRIMARY KEY,
    workflow_name         VARCHAR(100) NOT NULL,
    entity_name           VARCHAR(100),
    entity_id             BIGINT,
    current_step          INT,
    total_steps           INT,
    status                VARCHAR(20) DEFAULT 'PENDING',  -- PENDING/APPROVED/REJECTED
    initiated_by          BIGINT,
    initiated_date        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_date        TIMESTAMP,
    final_status          VARCHAR(20)
);
COMMENT ON TABLE fnd_workflow_approvals IS '工作流审批';

-- 通知消息
CREATE TABLE IF NOT EXISTS fnd_notifications_extended (
    notification_id       BIGSERIAL PRIMARY KEY,
    recipient_id          BIGINT NOT NULL,
    message_type          VARCHAR(30),  -- EMAIL/SYSTEM/ALERT
    subject               VARCHAR(255),
    message_body          TEXT,
    priority              VARCHAR(10) DEFAULT 'NORMAL',  -- LOW/NORMAL/HIGH/URGENT
    status                VARCHAR(20) DEFAULT 'UNREAD',  -- UNREAD/READ/ARCHIVED
    sent_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    read_date             TIMESTAMP,
    expiry_date           DATE
);
COMMENT ON TABLE fnd_notifications_extended IS '通知消息扩展';

-- ============================================================
-- 创建索引（性能优化）
-- ============================================================

-- AP 模块索引
CREATE INDEX IF NOT EXISTS idx_ap_invoice_po_matches_invoice ON ap_invoice_po_matches(invoice_id);
CREATE INDEX IF NOT EXISTS idx_ap_invoice_po_matches_po_line ON ap_invoice_po_matches(po_line_id);
CREATE INDEX IF NOT EXISTS idx_ap_gl_interface_invoice ON ap_gl_interface(invoice_id);
CREATE INDEX IF NOT EXISTS idx_ap_gl_interface_status ON ap_gl_interface(status);

-- PO 模块索引
CREATE INDEX IF NOT EXISTS idx_po_approval_history_po_header ON po_approval_history(po_header_id);
CREATE INDEX IF NOT EXISTS idx_po_change_orders_po_header ON po_change_orders(po_header_id);
CREATE INDEX IF NOT EXISTS idx_po_requisition_links_req_line ON po_requisition_links(requisition_line_id);
CREATE INDEX IF NOT EXISTS idx_vendor_performance_supplier ON vendor_performance_scores(supplier_id);

-- GL 模块索引
CREATE INDEX IF NOT EXISTS idx_gl_batches_ledger ON gl_batches(ledger_id);
CREATE INDEX IF NOT EXISTS idx_gl_journal_lines_header ON gl_journal_lines(je_header_id);
CREATE INDEX IF NOT EXISTS idx_gl_balances_ccid ON gl_balances(code_combination_id);
CREATE INDEX IF NOT EXISTS idx_gl_balances_period ON gl_balances(period_name);

-- AR 模块索引
CREATE INDEX IF NOT EXISTS idx_ar_receipt_applications_receipt ON ar_receipt_applications_extended(receipt_id);
CREATE INDEX IF NOT EXISTS idx_ar_receipt_applications_invoice ON ar_receipt_applications_extended(invoice_id);
CREATE INDEX IF NOT EXISTS idx_ar_customer_balances_customer ON ar_customer_balances(customer_id);
CREATE INDEX IF NOT EXISTS idx_ar_collection_cases_customer ON ar_collection_cases(customer_id);

-- INV 模块索引
CREATE INDEX IF NOT EXISTS idx_inv_subinventories_org ON inv_subinventories_extended(organization_id);
CREATE INDEX IF NOT EXISTS idx_inv_item_locators_subinv ON inv_item_locators_extended(subinventory_id);
CREATE INDEX IF NOT EXISTS idx_inv_lot_numbers_item ON inv_lot_numbers_extended(item_id);
CREATE INDEX IF NOT EXISTS idx_inv_serial_numbers_item ON inv_serial_numbers_extended(item_id);

-- OM 模块索引
CREATE INDEX IF NOT EXISTS idx_om_shipment_details_shipment ON om_shipment_details_extended(shipment_id);
CREATE INDEX IF NOT EXISTS idx_om_shipment_details_order_line ON om_shipment_details_extended(order_line_id);
CREATE INDEX IF NOT EXISTS idx_om_order_reservations_order_line ON om_order_reservations(order_line_id);
CREATE INDEX IF NOT EXISTS idx_om_price_list_lines_list ON om_price_list_lines(price_list_id);

-- FND 模块索引
CREATE INDEX IF NOT EXISTS idx_fnd_attachments_entity ON fnd_attachments_extended(entity_name, entity_id);
CREATE INDEX IF NOT EXISTS idx_fnd_workflow_approvals_entity ON fnd_workflow_approvals(entity_name, entity_id);
CREATE INDEX IF NOT EXISTS idx_fnd_notifications_recipient ON fnd_notifications_extended(recipient_id);

-- ============================================================
-- 提交事务
-- ============================================================

COMMIT;

-- ============================================================
-- 验证创建的表
-- ============================================================

SELECT 
    '新增表统计' as report_title,
    COUNT(*) as total_new_tables
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN (
    'ap_invoice_po_matches', 'ap_gl_interface', 'ap_payment_invoice_dists',
    'po_approval_history', 'po_change_orders', 'po_requisition_links', 'vendor_performance_scores',
    'gl_batches', 'gl_journal_lines', 'gl_balances', 'gl_code_combination_segments',
    'gl_period_statuses_extended', 'gl_subledger_sources',
    'ar_receipt_applications_extended', 'ar_customer_profiles_extended', 'ar_customer_balances',
    'ar_revenue_recognition', 'ar_collection_cases', 'ar_collection_activities',
    'inv_subinventories_extended', 'inv_item_locators_extended', 'inv_lot_numbers_extended',
    'inv_serial_numbers_extended', 'inv_cycle_counts_extended', 'inv_cycle_count_adjustments',
    'om_shipment_details_extended', 'om_order_reservations', 'om_price_lists_extended',
    'om_price_list_lines', 'om_order_discounts', 'om_return_reasons_extended',
    'fnd_business_events_log', 'fnd_attachments_extended', 'fnd_workflow_approvals', 'fnd_notifications_extended'
);
