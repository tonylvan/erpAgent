-- ============================================================
-- Oracle EBS 表关系扩展脚本
-- ============================================================
-- 目标：添加缺失的关键关系表和关联字段
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

-- 供应商绩效评估
CREATE TABLE IF NOT EXISTS vendor_performance_scores (
    score_id              BIGSERIAL PRIMARY KEY,
    vendor_id             BIGINT NOT NULL,
    evaluation_period     VARCHAR(30),
    quality_score         NUMERIC(5,2),  -- 质量评分
    delivery_score        NUMERIC(5,2),  -- 交货评分
    price_score           NUMERIC(5,2),  -- 价格评分
    service_score         NUMERIC(5,2),  -- 服务评分
    overall_score         NUMERIC(5,2),  -- 综合评分
    evaluated_by          BIGINT,
    evaluation_date       TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 3. GL 模块关系扩展
-- ============================================================

-- 总账批次
CREATE TABLE IF NOT EXISTS gl_batches (
    batch_id              BIGSERIAL PRIMARY KEY,
    batch_name            VARCHAR(100) NOT NULL,
    batch_type            VARCHAR(30),  -- MANUAL/AUTO
    period_name           VARCHAR(30),
    effective_date        DATE,
    total_dr_amount       NUMERIC(15,2) DEFAULT 0,
    total_cr_amount       NUMERIC(15,2) DEFAULT 0,
    status                VARCHAR(20) DEFAULT 'PENDING',
    posted_date           TIMESTAMP,
    posted_by             BIGINT,
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by            BIGINT
);

-- 总账日记账行
CREATE TABLE IF NOT EXISTS gl_journal_lines (
    line_id               BIGSERIAL PRIMARY KEY,
    journal_id            BIGINT NOT NULL,
    line_number           INT NOT NULL,
    code_combination_id   BIGINT NOT NULL,
    account_type          VARCHAR(10),
    dr_amount             NUMERIC(15,2) DEFAULT 0,
    cr_amount             NUMERIC(15,2) DEFAULT 0,
    description           VARCHAR(240),
    reference_type        VARCHAR(30),
    reference_id          BIGINT,  -- AP/AR/FA 等来源
    posted_flag           VARCHAR(1) DEFAULT 'N',
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 总账余额
CREATE TABLE IF NOT EXISTS gl_balances (
    balance_id            BIGSERIAL PRIMARY KEY,
    code_combination_id   BIGINT NOT NULL,
    period_name           VARCHAR(30) NOT NULL,
    actual_flag           VARCHAR(10),  -- ACTUAL/BUDGET/ENCUMBRANCE
    currency_code         VARCHAR(15) DEFAULT 'USD',
    begin_balance_dr      NUMERIC(15,2) DEFAULT 0,
    begin_balance_cr      NUMERIC(15,2) DEFAULT 0,
    period_dr             NUMERIC(15,2) DEFAULT 0,
    period_cr             NUMERIC(15,2) DEFAULT 0,
    end_balance_dr        NUMERIC(15,2) DEFAULT 0,
    end_balance_cr        NUMERIC(15,2) DEFAULT 0,
    last_updated          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 科目组合
CREATE TABLE IF NOT EXISTS gl_code_combinations (
    code_combination_id   BIGSERIAL PRIMARY KEY,
    segment1              VARCHAR(30),  -- 公司
    segment2              VARCHAR(30),  -- 部门
    segment3              VARCHAR(30),  -- 科目
    segment4              VARCHAR(30),  -- 子科目
    segment5              VARCHAR(30),  -- 项目
    segment6              VARCHAR(30),  -- 产品
    segment7              VARCHAR(30),
    segment8              VARCHAR(30),
    segment9              VARCHAR(30),
    segment10             VARCHAR(30),
    combined_string       VARCHAR(240),
    enabled_flag          VARCHAR(1) DEFAULT 'Y',
    start_date            DATE,
    end_date              DATE,
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 期间状态
CREATE TABLE IF NOT EXISTS gl_period_statuses (
    period_status_id      BIGSERIAL PRIMARY KEY,
    ledger_id             BIGINT NOT NULL,
    period_name           VARCHAR(30) NOT NULL,
    period_type           VARCHAR(30),
    start_date            DATE,
    end_date              DATE,
    status                VARCHAR(20),  -- OPEN/FUTURE/ENTERED/CLOSED/PERMANENTLY_CLOSED
    opened_date           TIMESTAMP,
    closed_date           TIMESTAMP,
    last_updated          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 子账来源
CREATE TABLE IF NOT EXISTS gl_subledger_sources (
    source_id             BIGSERIAL PRIMARY KEY,
    source_type           VARCHAR(30),  -- AP/AR/FA/PO/OM
    source_table          VARCHAR(50),
    source_id_col         VARCHAR(50),
    description           VARCHAR(240),
    enabled_flag          VARCHAR(1) DEFAULT 'Y',
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 4. AR 模块关系扩展
-- ============================================================

-- 收款与发票应用
CREATE TABLE IF NOT EXISTS ar_receipt_applications (
    application_id        BIGSERIAL PRIMARY KEY,
    receipt_id            BIGINT NOT NULL,
    invoice_id            BIGINT NOT NULL,
    applied_amount        NUMERIC(15,2) NOT NULL,
    discount_amount       NUMERIC(15,2) DEFAULT 0,
    application_date      DATE,
    application_type      VARCHAR(30),  -- CASH/DISCOUNT/ADJUSTMENT/CHARGEBACK
    status                VARCHAR(20) DEFAULT 'ACTIVE',
    gl_posted_flag        VARCHAR(1) DEFAULT 'N',
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 客户配置文件
CREATE TABLE IF NOT EXISTS ar_customer_profiles (
    profile_id            BIGSERIAL PRIMARY KEY,
    customer_id           BIGINT NOT NULL,
    credit_limit          NUMERIC(15,2),
    credit_limit_currency VARCHAR(15) DEFAULT 'USD',
    payment_term_id       BIGINT,
    discount_percent      NUMERIC(5,2),
    interest_rate         NUMERIC(5,2),
    statement_cycle       VARCHAR(30),
    dunning_letter_cycle  VARCHAR(30),
    auto_invoice_flag     VARCHAR(1) DEFAULT 'Y',
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 客户余额
CREATE TABLE IF NOT EXISTS ar_customer_balances (
    balance_id            BIGSERIAL PRIMARY KEY,
    customer_id           BIGINT NOT NULL,
    currency_code         VARCHAR(15) DEFAULT 'USD',
    outstanding_balance   NUMERIC(15,2) DEFAULT 0,
    on_account_balance    NUMERIC(15,2) DEFAULT 0,
    unapplied_balance     NUMERIC(15,2) DEFAULT 0,
    unidentified_balance  NUMERIC(15,2) DEFAULT 0,
    last_calc_date        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 收入确认
CREATE TABLE IF NOT EXISTS ar_revenue_recognition (
    rev_rec_id            BIGSERIAL PRIMARY KEY,
    invoice_line_id       BIGINT NOT NULL,
    rev_rec_type          VARCHAR(30),  -- IMMEDIATE/OVER_TIME/AT_POINT
    total_amount          NUMERIC(15,2),
    recognized_amount     NUMERIC(15,2) DEFAULT 0,
    deferred_amount       NUMERIC(15,2) DEFAULT 0,
    start_date            DATE,
    end_date              DATE,
    recognition_period    VARCHAR(30),
    status                VARCHAR(20) DEFAULT 'PENDING',
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 催款记录
CREATE TABLE IF NOT EXISTS ar_collection_cases (
    case_id               BIGSERIAL PRIMARY KEY,
    customer_id           BIGINT NOT NULL,
    case_type             VARCHAR(30),  -- DELINQUENT/PROMISE_TO_PAY/DISPUTE
    case_status           VARCHAR(20) DEFAULT 'OPEN',
    amount_due            NUMERIC(15,2),
    assigned_to           BIGINT,  -- 催收员 ID
    priority              VARCHAR(10),  -- HIGH/MEDIUM/LOW
    opened_date           TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_date           TIMESTAMP,
    last_activity_date    TIMESTAMP
);

-- 催款活动历史
CREATE TABLE IF NOT EXISTS ar_collection_activities (
    activity_id           BIGSERIAL PRIMARY KEY,
    case_id               BIGINT NOT NULL,
    activity_type         VARCHAR(30),  -- CALL/EMAIL/LETTER/LEGAL
    activity_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    description           TEXT,
    result                VARCHAR(100),
    follow_up_date        DATE,
    performed_by          BIGINT
);

-- ============================================================
-- 5. INV 模块关系扩展
-- ============================================================

-- 库存子库
CREATE TABLE IF NOT EXISTS inv_subinventories (
    subinventory_id       BIGSERIAL PRIMARY KEY,
    organization_id       BIGINT NOT NULL,
    subinventory_code     VARCHAR(10) NOT NULL,
    description           VARCHAR(240),
    location_id           BIGINT,
    picking_order         INT,
    material_account      BIGINT,  -- 会计科目
    status                VARCHAR(20) DEFAULT 'ACTIVE',
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 库存货位
CREATE TABLE IF NOT EXISTS inv_item_locators (
    locator_id            BIGSERIAL PRIMARY KEY,
    subinventory_id       BIGINT NOT NULL,
    organization_id       BIGINT NOT NULL,
    locator_type          VARCHAR(30),
    segment1              VARCHAR(30),  -- 区
    segment2              VARCHAR(30),  -- 排
    segment3              VARCHAR(30),  -- 架
    segment4              VARCHAR(30),  -- 位
    combined_locator      VARCHAR(240),
    status                VARCHAR(20) DEFAULT 'ACTIVE',
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 批次管理
CREATE TABLE IF NOT EXISTS inv_lot_numbers (
    lot_id                BIGSERIAL PRIMARY KEY,
    inventory_item_id     BIGINT NOT NULL,
    organization_id       BIGINT NOT NULL,
    lot_number            VARCHAR(80) NOT NULL,
    description           VARCHAR(240),
    expiration_date       DATE,
    status                VARCHAR(20) DEFAULT 'ACTIVE',
    quantity_on_hand      NUMERIC(15,2) DEFAULT 0,
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 序列号管理
CREATE TABLE IF NOT EXISTS inv_serial_numbers (
    serial_id             BIGSERIAL PRIMARY KEY,
    inventory_item_id     BIGINT NOT NULL,
    organization_id       BIGINT NOT NULL,
    serial_number         VARCHAR(80) NOT NULL,
    lot_id                BIGINT,
    status                VARCHAR(20),  -- IN_STOCK/ISSUED/RECEIVED/RETURNED
    current_locator_id    BIGINT,
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 库存盘点
CREATE TABLE IF NOT EXISTS inv_cycle_counts (
    count_id              BIGSERIAL PRIMARY KEY,
    organization_id       BIGINT NOT NULL,
    subinventory_id       BIGINT,
    count_name            VARCHAR(100) NOT NULL,
    count_type            VARCHAR(30),  -- SCHEDULED/RANDOM
    frequency_days        INT DEFAULT 30,
    last_count_date       DATE,
    next_count_date       DATE,
    status                VARCHAR(20) DEFAULT 'ACTIVE',
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 盘点调整
CREATE TABLE IF NOT EXISTS inv_cycle_count_adjustments (
    adjustment_id         BIGSERIAL PRIMARY KEY,
    count_id              BIGINT NOT NULL,
    inventory_item_id     BIGINT NOT NULL,
    locator_id            BIGINT,
    lot_id                BIGINT,
    system_quantity       NUMERIC(15,2),
    counted_quantity      NUMERIC(15,2),
    adjustment_quantity   NUMERIC(15,2),
    adjustment_amount     NUMERIC(15,2),
    approval_status       VARCHAR(20) DEFAULT 'PENDING',
    approved_by           BIGINT,
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 6. OM 模块关系扩展
-- ============================================================

-- 发运明细
CREATE TABLE IF NOT EXISTS om_shipment_details (
    shipment_detail_id    BIGSERIAL PRIMARY KEY,
    shipment_id           BIGINT NOT NULL,
    line_id               BIGINT NOT NULL,
    shipped_quantity      NUMERIC(15,2),
    delivered_quantity    NUMERIC(15,2) DEFAULT 0,
    ship_method           VARCHAR(30),
    carrier_id            BIGINT,
    tracking_number       VARCHAR(100),
    ship_date             DATE,
    delivery_date         DATE,
    status                VARCHAR(20) DEFAULT 'PENDING'
);

-- 订单预留
CREATE TABLE IF NOT EXISTS om_order_reservations (
    reservation_id        BIGSERIAL PRIMARY KEY,
    line_id               BIGINT NOT NULL,
    inventory_item_id     BIGINT NOT NULL,
    organization_id       BIGINT NOT NULL,
    subinventory_id       BIGINT,
    locator_id            BIGINT,
    lot_id                BIGINT,
    reserved_quantity     NUMERIC(15,2),
    reservation_date      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status                VARCHAR(20) DEFAULT 'ACTIVE'
);

-- 价格列表
CREATE TABLE IF NOT EXISTS om_price_lists (
    price_list_id         BIGSERIAL PRIMARY KEY,
    price_list_name       VARCHAR(100) NOT NULL,
    currency_code         VARCHAR(15) DEFAULT 'USD',
    start_date            DATE,
    end_date              DATE,
    price_type            VARCHAR(30),  -- STANDARD/PROMOTIONAL
    status                VARCHAR(20) DEFAULT 'ACTIVE',
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 价格列表行
CREATE TABLE IF NOT EXISTS om_price_list_lines (
    price_line_id         BIGSERIAL PRIMARY KEY,
    price_list_id         BIGINT NOT NULL,
    inventory_item_id     BIGINT NOT NULL,
    unit_price            NUMERIC(15,2) NOT NULL,
    start_date            DATE,
    end_date              DATE,
    min_quantity          NUMERIC(15,2) DEFAULT 1,
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 订单折扣
CREATE TABLE IF NOT EXISTS om_order_discounts (
    discount_id           BIGSERIAL PRIMARY KEY,
    header_id             BIGINT,
    line_id               BIGINT,
    discount_type         VARCHAR(30),  -- PERCENT/AMOUNT
    discount_amount       NUMERIC(15,2),
    discount_percent      NUMERIC(5,2),
    reason                VARCHAR(100),
    applied_by            BIGINT,
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 退货原因
CREATE TABLE IF NOT EXISTS om_return_reasons (
    reason_id             BIGSERIAL PRIMARY KEY,
    reason_code           VARCHAR(30) NOT NULL,
    reason_name           VARCHAR(100),
    description           VARCHAR(240),
    requires_approval     VARCHAR(1) DEFAULT 'N',
    status                VARCHAR(20) DEFAULT 'ACTIVE'
);

-- ============================================================
-- 7. 跨模块关联表
-- ============================================================

-- 业务事件日志
CREATE TABLE IF NOT EXISTS fnd_business_events (
    event_id              BIGSERIAL PRIMARY KEY,
    event_name            VARCHAR(100) NOT NULL,
    event_type            VARCHAR(30),
    source_module         VARCHAR(10),  -- AP/PO/AR/OM/INV
    source_table          VARCHAR(50),
    source_id             BIGINT,
    event_data            JSONB,
    processed_flag        VARCHAR(1) DEFAULT 'N',
    processed_date        TIMESTAMP,
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 附件管理
CREATE TABLE IF NOT EXISTS fnd_attachments (
    attachment_id         BIGSERIAL PRIMARY KEY,
    entity_type           VARCHAR(50),  -- INVOICE/ORDER/ITEM 等
    entity_id             BIGINT,
    file_name             VARCHAR(240),
    file_type             VARCHAR(50),
    file_size             BIGINT,
    file_path             VARCHAR(500),
    description           VARCHAR(240),
    uploaded_by           BIGINT,
    upload_date           TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 工作流审批
CREATE TABLE IF NOT EXISTS fnd_workflow_approvals (
    approval_id           BIGSERIAL PRIMARY KEY,
    workflow_type         VARCHAR(50),
    entity_type           VARCHAR(50),
    entity_id             BIGINT,
    current_approver_id   BIGINT,
    approval_level        INT,
    status                VARCHAR(20) DEFAULT 'PENDING',
    approved_date         TIMESTAMP,
    comments              TEXT,
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 通知消息
CREATE TABLE IF NOT EXISTS fnd_notifications (
    notification_id       BIGSERIAL PRIMARY KEY,
    user_id               BIGINT NOT NULL,
    notification_type     VARCHAR(30),
    title                 VARCHAR(240),
    message               TEXT,
    priority              VARCHAR(10),  -- HIGH/MEDIUM/LOW
    status                VARCHAR(20) DEFAULT 'UNREAD',
    read_date             TIMESTAMP,
    action_url            VARCHAR(500),
    creation_date         TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 创建索引（性能优化）
-- ============================================================

-- AP 模块索引
CREATE INDEX IF NOT EXISTS idx_ap_inv_po_match_inv ON ap_invoice_po_matches(invoice_id);
CREATE INDEX IF NOT EXISTS idx_ap_inv_po_match_po ON ap_invoice_po_matches(po_line_id);
CREATE INDEX IF NOT EXISTS idx_ap_gl_interface_inv ON ap_gl_interface(invoice_id);
CREATE INDEX IF NOT EXISTS idx_ap_gl_interface_status ON ap_gl_interface(status);

-- PO 模块索引
CREATE INDEX IF NOT EXISTS idx_po_approval_po ON po_approval_history(po_header_id);
CREATE INDEX IF NOT EXISTS idx_po_change_po ON po_change_orders(po_header_id);
CREATE INDEX IF NOT EXISTS idx_po_req_link_req ON po_requisition_links(requisition_line_id);
CREATE INDEX IF NOT EXISTS idx_po_perf_vendor ON vendor_performance_scores(vendor_id);

-- GL 模块索引
CREATE INDEX IF NOT EXISTS idx_gl_batch_period ON gl_batches(period_name);
CREATE INDEX IF NOT EXISTS idx_gl_journal_line_jrnl ON gl_journal_lines(journal_id);
CREATE INDEX IF NOT EXISTS idx_gl_balance_ccid ON gl_balances(code_combination_id);
CREATE INDEX IF NOT EXISTS idx_gl_balance_period ON gl_balances(period_name);
CREATE INDEX IF NOT EXISTS idx_gl_code_comb_seg1 ON gl_code_combinations(segment1, segment2, segment3);

-- AR 模块索引
CREATE INDEX IF NOT EXISTS idx_ar_receipt_app_receipt ON ar_receipt_applications(receipt_id);
CREATE INDEX IF NOT EXISTS idx_ar_receipt_app_inv ON ar_receipt_applications(invoice_id);
CREATE INDEX IF NOT EXISTS idx_ar_cust_profile_cust ON ar_customer_profiles(customer_id);
CREATE INDEX IF NOT EXISTS idx_ar_cust_bal_cust ON ar_customer_balances(customer_id);
CREATE INDEX IF NOT EXISTS idx_ar_collection_cust ON ar_collection_cases(customer_id);

-- INV 模块索引
CREATE INDEX IF NOT EXISTS idx_inv_subinv_org ON inv_subinventories(organization_id);
CREATE INDEX IF NOT EXISTS idx_inv_locator_subinv ON inv_item_locators(subinventory_id);
CREATE INDEX IF NOT EXISTS idx_inv_lot_item ON inv_lot_numbers(inventory_item_id, organization_id);
CREATE INDEX IF NOT EXISTS idx_inv_serial_item ON inv_serial_numbers(inventory_item_id, organization_id);
CREATE INDEX IF NOT EXISTS idx_inv_cycle_count_org ON inv_cycle_counts(organization_id);

-- OM 模块索引
CREATE INDEX IF NOT EXISTS idx_om_shipment_detail_ship ON om_shipment_details(shipment_id);
CREATE INDEX IF NOT EXISTS idx_om_reservation_line ON om_order_reservations(line_id);
CREATE INDEX IF NOT EXISTS idx_om_price_list_line ON om_price_list_lines(price_list_id);
CREATE INDEX IF NOT EXISTS idx_om_discount_header ON om_order_discounts(header_id);

-- 跨模块索引
CREATE INDEX IF NOT EXISTS idx_fnd_event_entity ON fnd_business_events(source_table, source_id);
CREATE INDEX IF NOT EXISTS idx_fnd_attach_entity ON fnd_attachments(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_fnd_workflow_entity ON fnd_workflow_approvals(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_fnd_notify_user ON fnd_notifications(user_id);

COMMIT;

-- ============================================================
-- 数据验证查询
-- ============================================================

-- 检查新表创建数量
SELECT COUNT(*) as new_tables_created 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN (
    'ap_invoice_po_matches', 'ap_gl_interface', 'ap_payment_invoice_dists',
    'po_approval_history', 'po_change_orders', 'po_requisition_links', 'vendor_performance_scores',
    'gl_batches', 'gl_journal_lines', 'gl_balances', 'gl_code_combinations', 'gl_period_statuses', 'gl_subledger_sources',
    'ar_receipt_applications', 'ar_customer_profiles', 'ar_customer_balances', 'ar_revenue_recognition', 'ar_collection_cases', 'ar_collection_activities',
    'inv_subinventories', 'inv_item_locators', 'inv_lot_numbers', 'inv_serial_numbers', 'inv_cycle_counts', 'inv_cycle_count_adjustments',
    'om_shipment_details', 'om_order_reservations', 'om_price_lists', 'om_price_list_lines', 'om_order_discounts', 'om_return_reasons',
    'fnd_business_events', 'fnd_attachments', 'fnd_workflow_approvals', 'fnd_notifications'
);

-- 按模块统计表数量
SELECT 
    CASE 
        WHEN table_name LIKE 'ap_%' THEN 'AP (应付)'
        WHEN table_name LIKE 'po_%' THEN 'PO (采购)'
        WHEN table_name LIKE 'gl_%' THEN 'GL (总账)'
        WHEN table_name LIKE 'ar_%' THEN 'AR (应收)'
        WHEN table_name LIKE 'inv_%' THEN 'INV (库存)'
        WHEN table_name LIKE 'om_%' THEN 'OM (销售)'
        WHEN table_name LIKE 'fnd_%' THEN 'FND (基础)'
        ELSE '其他'
    END as module,
    COUNT(*) as table_count
FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN (
    'ap_invoice_po_matches', 'ap_gl_interface', 'ap_payment_invoice_dists',
    'po_approval_history', 'po_change_orders', 'po_requisition_links', 'vendor_performance_scores',
    'gl_batches', 'gl_journal_lines', 'gl_balances', 'gl_code_combinations', 'gl_period_statuses', 'gl_subledger_sources',
    'ar_receipt_applications', 'ar_customer_profiles', 'ar_customer_balances', 'ar_revenue_recognition', 'ar_collection_cases', 'ar_collection_activities',
    'inv_subinventories', 'inv_item_locators', 'inv_lot_numbers', 'inv_serial_numbers', 'inv_cycle_counts', 'inv_cycle_count_adjustments',
    'om_shipment_details', 'om_order_reservations', 'om_price_lists', 'om_price_list_lines', 'om_order_discounts', 'om_return_reasons',
    'fnd_business_events', 'fnd_attachments', 'fnd_workflow_approvals', 'fnd_notifications'
)
GROUP BY 
    CASE 
        WHEN table_name LIKE 'ap_%' THEN 'AP (应付)'
        WHEN table_name LIKE 'po_%' THEN 'PO (采购)'
        WHEN table_name LIKE 'gl_%' THEN 'GL (总账)'
        WHEN table_name LIKE 'ar_%' THEN 'AR (应收)'
        WHEN table_name LIKE 'inv_%' THEN 'INV (库存)'
        WHEN table_name LIKE 'om_%' THEN 'OM (销售)'
        WHEN table_name LIKE 'fnd_%' THEN 'FND (基础)'
        ELSE '其他'
    END
ORDER BY table_count DESC;
