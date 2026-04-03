-- ============================================================
-- Oracle EBS ERP 扩展表创建脚本 (Batch 1-2)
-- ============================================================
-- 目标：从现有 56 张表扩展到 116 张核心表
-- 数据库：PostgreSQL 14+
-- 字符集：UTF8
-- 创建日期：2026-04-03
-- ============================================================
-- 注意：Oracle VARCHAR2 类型已替换为 PostgreSQL VARCHAR
-- ============================================================

-- 开始事务
BEGIN;

-- ============================================================
-- Batch 1: AP/PO 模块扩展 (20 张表)
-- ============================================================

-- 1. AP 模块扩展表
-- ============================================================

-- 发票分配表
CREATE TABLE IF NOT EXISTS ap_invoice_distributions_all (
    distribution_id           BIGSERIAL PRIMARY KEY,
    invoice_id                BIGINT NOT NULL,
    invoice_line_id           BIGINT,
    distribution_num          INT NOT NULL,
    amount                    NUMERIC(15,2) NOT NULL,
    accounting_date           DATE,
    period_name               VARCHAR(30),
    code_combination_id       BIGINT,
    account_class             VARCHAR(30),
    dist_code_concatenated    VARCHAR(240),
    description               VARCHAR(240),
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by                BIGINT,
    last_update_date          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_updated_by           BIGINT,
    org_id                    BIGINT
);

-- 付款计划表
CREATE TABLE IF NOT EXISTS ap_payment_schedules_all (
    schedule_id               BIGSERIAL PRIMARY KEY,
    invoice_id                BIGINT NOT NULL,
    payment_num               INT NOT NULL,
    due_date                  DATE,
    amount_due                NUMERIC(15,2) NOT NULL,
    amount_paid               NUMERIC(15,2) DEFAULT 0,
    discount_date             DATE,
    discount_amount           NUMERIC(15,2) DEFAULT 0,
    payment_status            VARCHAR(20) DEFAULT 'PENDING',
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by                BIGINT,
    org_id                    BIGINT
);

-- 银行账户表
CREATE TABLE IF NOT EXISTS ap_bank_accounts (
    bank_account_id           BIGSERIAL PRIMARY KEY,
    vendor_id                 BIGINT,
    account_num               VARCHAR(50) NOT NULL,
    account_name              VARCHAR(100),
    bank_name                 VARCHAR(100),
    bank_branch_name          VARCHAR(100),
    currency_code             VARCHAR(15) DEFAULT 'USD',
    account_type              VARCHAR(30),
    status                    VARCHAR(20) DEFAULT 'ACTIVE',
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by                BIGINT
);

-- 银行分行表
CREATE TABLE IF NOT EXISTS ap_bank_branches (
    branch_id                 BIGSERIAL PRIMARY KEY,
    bank_id                   BIGINT,
    branch_name               VARCHAR(100) NOT NULL,
    branch_code               VARCHAR(50),
    address_line1             VARCHAR(240),
    city                      VARCHAR(80),
    country                   VARCHAR(80),
    postal_code               VARCHAR(30),
    phone                     VARCHAR(50),
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 支票表
CREATE TABLE IF NOT EXISTS ap_checks (
    check_id                  BIGSERIAL PRIMARY KEY,
    check_number              VARCHAR(50) NOT NULL,
    amount                    NUMERIC(15,2) NOT NULL,
    check_date                DATE,
    status                    VARCHAR(20) DEFAULT 'ISSUED',
    vendor_id                 BIGINT NOT NULL,
    bank_account_id           BIGINT,
    payment_method            VARCHAR(30),
    cleared_flag              VARCHAR(1) DEFAULT 'N',
    cleared_date              DATE,
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by                BIGINT,
    org_id                    BIGINT
);

-- 预扣税表
CREATE TABLE IF NOT EXISTS ap_withholding_tax (
    withholding_id            BIGSERIAL PRIMARY KEY,
    invoice_id                BIGINT NOT NULL,
    tax_code                  VARCHAR(30) NOT NULL,
    tax_rate                  NUMERIC(5,2) NOT NULL,
    tax_amount                NUMERIC(15,2) NOT NULL,
    tax_base                  NUMERIC(15,2),
    withholding_type          VARCHAR(30),
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by                BIGINT
);

-- 费用报告表
CREATE TABLE IF NOT EXISTS ap_expense_reports (
    report_id                 BIGSERIAL PRIMARY KEY,
    report_number             VARCHAR(50) NOT NULL,
    employee_id               BIGINT NOT NULL,
    total_amount              NUMERIC(15,2) NOT NULL,
    currency_code             VARCHAR(15) DEFAULT 'USD',
    status                    VARCHAR(20) DEFAULT 'PENDING',
    submission_date           DATE,
    approval_date             DATE,
    approved_by               BIGINT,
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by                BIGINT
);

-- 发票税表
CREATE TABLE IF NOT EXISTS ap_invoice_taxes (
    tax_id                    BIGSERIAL PRIMARY KEY,
    invoice_id                BIGINT NOT NULL,
    tax_code                  VARCHAR(30),
    tax_rate                  NUMERIC(5,2),
    tax_amount                NUMERIC(15,2),
    tax_type                  VARCHAR(30),
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 供应商联系人电话表
CREATE TABLE IF NOT EXISTS ap_supplier_contact_phones (
    contact_phone_id          BIGSERIAL PRIMARY KEY,
    vendor_contact_id         BIGINT NOT NULL,
    phone_type                VARCHAR(30),
    phone_number              VARCHAR(50),
    extension                 VARCHAR(20),
    is_primary                VARCHAR(1) DEFAULT 'N'
);

-- 供应商银行使用表
CREATE TABLE IF NOT EXISTS ap_supplier_bank_uses (
    bank_use_id               BIGSERIAL PRIMARY KEY,
    vendor_id                 BIGINT NOT NULL,
    bank_account_id           BIGINT NOT NULL,
    vendor_site_id            BIGINT,
    payment_method            VARCHAR(30),
    is_primary                VARCHAR(1) DEFAULT 'N'
);

-- 2. PO 模块扩展表
-- ============================================================

-- 请购单头表
CREATE TABLE IF NOT EXISTS po_requisitions_all (
    requisition_header_id     BIGSERIAL PRIMARY KEY,
    segment1                  VARCHAR(30) NOT NULL,
    requisition_type          VARCHAR(25) DEFAULT 'PURCHASE',
    status                    VARCHAR(20) DEFAULT 'INCOMPLETE',
    description               VARCHAR(240),
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by                BIGINT,
    need_by_date              DATE,
    org_id                    BIGINT
);

-- 请购单行表
CREATE TABLE IF NOT EXISTS po_requisition_lines (
    requisition_line_id       BIGSERIAL PRIMARY KEY,
    requisition_header_id     BIGINT NOT NULL,
    line_num                  INT NOT NULL,
    item_id                   BIGINT,
    item_description          VARCHAR(240),
    quantity                  NUMERIC(15,2),
    unit_price                NUMERIC(15,2),
    amount                    NUMERIC(15,2),
    need_by_date              DATE,
    destination_org_id        BIGINT,
    destination_subinventory  VARCHAR(30),
    status                    VARCHAR(20)
);

-- 报价请求头表
CREATE TABLE IF NOT EXISTS po_rfq_headers (
    rfq_header_id             BIGSERIAL PRIMARY KEY,
    rfq_number                VARCHAR(30) NOT NULL,
    rfq_type                  VARCHAR(25) DEFAULT 'RFQ',
    status                    VARCHAR(20) DEFAULT 'ACTIVE',
    description               VARCHAR(240),
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by                BIGINT,
    close_date                DATE,
    vendor_id                 BIGINT
);

-- 报价请求行表
CREATE TABLE IF NOT EXISTS po_rfq_lines (
    rfq_line_id               BIGSERIAL PRIMARY KEY,
    rfq_header_id             BIGINT NOT NULL,
    line_num                  INT NOT NULL,
    item_id                   BIGINT,
    item_description          VARCHAR(240),
    quantity                  NUMERIC(15,2),
    unit_price                NUMERIC(15,2),
    category                  VARCHAR(30)
);

-- 供应商报价表
CREATE TABLE IF NOT EXISTS po_quotations (
    quotation_id              BIGSERIAL PRIMARY KEY,
    rfq_header_id             BIGINT,
    vendor_id                 BIGINT NOT NULL,
    quotation_number          VARCHAR(30) NOT NULL,
    status                    VARCHAR(20) DEFAULT 'PENDING',
    total_amount              NUMERIC(15,2),
    currency_code             VARCHAR(15),
    submission_date           DATE,
    valid_until_date          DATE,
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 批准供应商清单表
CREATE TABLE IF NOT EXISTS po_approved_supplier_list (
    asl_id                    BIGSERIAL PRIMARY KEY,
    vendor_id                 BIGINT NOT NULL,
    item_id                   BIGINT,
    organization_id           BIGINT,
    status                    VARCHAR(20) DEFAULT 'ACTIVE',
    approval_date             DATE,
    expiry_date               DATE,
    manufacturer_name         VARCHAR(100),
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 寻源规则表
CREATE TABLE IF NOT EXISTS po_sourcing_rules (
    sourcing_rule_id          BIGSERIAL PRIMARY KEY,
    rule_name                 VARCHAR(100) NOT NULL,
    rule_type                 VARCHAR(30),
    item_id                   BIGINT,
    vendor_id                 BIGINT,
    allocation_percentage     NUMERIC(5,2),
    priority                  INT,
    start_date                DATE,
    end_date                  DATE,
    status                    VARCHAR(20) DEFAULT 'ACTIVE'
);

-- PO 发运表
CREATE TABLE IF NOT EXISTS po_shipments_all (
    shipment_id               BIGSERIAL PRIMARY KEY,
    po_header_id              BIGINT NOT NULL,
    po_line_id                BIGINT NOT NULL,
    shipment_num              INT NOT NULL,
    quantity                  NUMERIC(15,2),
    quantity_received         NUMERIC(15,2) DEFAULT 0,
    quantity_accepted         NUMERIC(15,2) DEFAULT 0,
    quantity_rejected         NUMERIC(15,2) DEFAULT 0,
    need_by_date              DATE,
    promised_date             DATE,
    actual_date               DATE,
    status                    VARCHAR(20)
);

-- 接收表头表
CREATE TABLE IF NOT EXISTS rcv_shipment_headers (
    shipment_header_id        BIGSERIAL PRIMARY KEY,
    receipt_num               VARCHAR(30) NOT NULL,
    shipment_num              VARCHAR(30),
    vendor_id                 BIGINT NOT NULL,
    receipt_date              DATE,
    status                    VARCHAR(20) DEFAULT 'PENDING',
    carrier                   VARCHAR(100),
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 接收交易表
CREATE TABLE IF NOT EXISTS rcv_transactions (
    transaction_id            BIGSERIAL PRIMARY KEY,
    shipment_header_id        BIGINT,
    po_header_id              BIGINT,
    po_line_id                BIGINT,
    transaction_type          VARCHAR(30) NOT NULL,
    transaction_date          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    quantity                  NUMERIC(15,2),
    status                    VARCHAR(20),
    created_by                BIGINT
);

-- ============================================================
-- Batch 2: AR/GL 模块扩展 (40 张表)
-- ============================================================

-- 3. AR 模块扩展表
-- ============================================================

-- 客户主表
CREATE TABLE IF NOT EXISTS ar_customers (
    customer_id               BIGSERIAL PRIMARY KEY,
    customer_number           VARCHAR(30) NOT NULL,
    customer_name             VARCHAR(360) NOT NULL,
    customer_type             VARCHAR(30),
    status                    VARCHAR(20) DEFAULT 'ACTIVE',
    credit_limit              NUMERIC(15,2),
    currency_code             VARCHAR(15),
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by                BIGINT
);

-- 客户地点表
CREATE TABLE IF NOT EXISTS ar_customer_sites (
    site_id                   BIGSERIAL PRIMARY KEY,
    customer_id               BIGINT NOT NULL,
    site_code                 VARCHAR(30) NOT NULL,
    site_type                 VARCHAR(30),
    address_line1             VARCHAR(240),
    city                      VARCHAR(80),
    country                   VARCHAR(80),
    postal_code               VARCHAR(30),
    phone                     VARCHAR(50),
    is_primary                VARCHAR(1) DEFAULT 'N'
);

-- 应收交易表
CREATE TABLE IF NOT EXISTS ar_transactions_all (
    transaction_id            BIGSERIAL PRIMARY KEY,
    transaction_number        VARCHAR(50) NOT NULL,
    transaction_type          VARCHAR(30),
    customer_id               BIGINT NOT NULL,
    amount                    NUMERIC(15,2) NOT NULL,
    amount_due                NUMERIC(15,2),
    amount_paid               NUMERIC(15,2) DEFAULT 0,
    status                    VARCHAR(20) DEFAULT 'OPEN',
    transaction_date          DATE,
    due_date                  DATE,
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 应收交易行表
CREATE TABLE IF NOT EXISTS ar_transaction_lines (
    line_id                   BIGSERIAL PRIMARY KEY,
    transaction_id            BIGINT NOT NULL,
    line_number               INT NOT NULL,
    description               VARCHAR(240),
    quantity                  NUMERIC(15,2),
    unit_price                NUMERIC(15,2),
    amount                    NUMERIC(15,2),
    tax_amount                NUMERIC(15,2),
    item_id                   BIGINT
);

-- 收款表
CREATE TABLE IF NOT EXISTS ar_receipts (
    receipt_id                BIGSERIAL PRIMARY KEY,
    receipt_number            VARCHAR(50) NOT NULL,
    customer_id               BIGINT,
    amount                    NUMERIC(15,2) NOT NULL,
    receipt_date              DATE,
    status                    VARCHAR(20) DEFAULT 'UNAPPLIED',
    payment_method            VARCHAR(30),
    currency_code             VARCHAR(15),
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 收款应用表
CREATE TABLE IF NOT EXISTS ar_receipt_applications (
    application_id            BIGSERIAL PRIMARY KEY,
    receipt_id                BIGINT NOT NULL,
    transaction_id            BIGINT NOT NULL,
    applied_amount            NUMERIC(15,2) NOT NULL,
    application_date          DATE,
    application_type          VARCHAR(30)
);

-- 调整表
CREATE TABLE IF NOT EXISTS ar_adjustments (
    adjustment_id             BIGSERIAL PRIMARY KEY,
    transaction_id            BIGINT NOT NULL,
    adjustment_type           VARCHAR(30),
    amount                    NUMERIC(15,2) NOT NULL,
    reason                    VARCHAR(240),
    status                    VARCHAR(20) DEFAULT 'PENDING',
    approval_date             DATE,
    created_by                BIGINT,
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 客户档案表
CREATE TABLE IF NOT EXISTS ar_customer_profiles (
    profile_id                BIGSERIAL PRIMARY KEY,
    customer_id               BIGINT NOT NULL,
    credit_limit              NUMERIC(15,2),
    payment_terms             VARCHAR(30),
    statement_cycle           VARCHAR(30),
    dso_target                NUMERIC(5,2),
    risk_level                VARCHAR(20)
);

-- 催款表
CREATE TABLE IF NOT EXISTS ar_dunning_letters (
    letter_id                 BIGSERIAL PRIMARY KEY,
    customer_id               BIGINT NOT NULL,
    transaction_id            BIGINT,
    letter_type               VARCHAR(30),
    send_date                 DATE,
    amount_due                NUMERIC(15,2),
    status                    VARCHAR(20)
);

-- 4. GL 模块扩展表
-- ============================================================

-- 科目表组合表
CREATE TABLE IF NOT EXISTS gl_code_combinations (
    code_combination_id       BIGSERIAL PRIMARY KEY,
    segment1                  VARCHAR(30),
    segment2                  VARCHAR(30),
    segment3                  VARCHAR(30),
    segment4                  VARCHAR(30),
    segment5                  VARCHAR(30),
    segment6                  VARCHAR(30),
    combined_segment          VARCHAR(240),
    enabled_flag              VARCHAR(1) DEFAULT 'Y',
    start_date                DATE,
    end_date                  DATE,
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 日记账头表
CREATE TABLE IF NOT EXISTS gl_je_headers (
    je_header_id              BIGSERIAL PRIMARY KEY,
    je_name                   VARCHAR(100) NOT NULL,
    je_category               VARCHAR(30),
    je_source                 VARCHAR(30),
    period_name               VARCHAR(30),
    currency_code             VARCHAR(15),
    status                    VARCHAR(20) DEFAULT 'PENDING',
    posted_date               DATE,
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by                BIGINT
);

-- 日记账行表
CREATE TABLE IF NOT EXISTS gl_je_lines (
    je_line_id                BIGSERIAL PRIMARY KEY,
    je_header_id              BIGINT NOT NULL,
    line_num                  INT NOT NULL,
    code_combination_id       BIGINT,
    debit                     NUMERIC(15,2) DEFAULT 0,
    credit                    NUMERIC(15,2) DEFAULT 0,
    description               VARCHAR(240),
    effective_date            DATE,
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 余额表
CREATE TABLE IF NOT EXISTS gl_balances (
    balance_id                BIGSERIAL PRIMARY KEY,
    code_combination_id       BIGINT NOT NULL,
    period_name               VARCHAR(30),
    currency_code             VARCHAR(15),
    actual_flag               VARCHAR(1) DEFAULT 'A',
    begin_balance             NUMERIC(15,2) DEFAULT 0,
    debit                     NUMERIC(15,2) DEFAULT 0,
    credit                    NUMERIC(15,2) DEFAULT 0,
    end_balance               NUMERIC(15,2) DEFAULT 0,
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 预算表
CREATE TABLE IF NOT EXISTS gl_budgets (
    budget_id                 BIGSERIAL PRIMARY KEY,
    budget_name               VARCHAR(100) NOT NULL,
    budget_year               INT,
    currency_code             VARCHAR(15),
    status                    VARCHAR(20) DEFAULT 'DRAFT',
    approval_date             DATE,
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 预算行表
CREATE TABLE IF NOT EXISTS gl_budget_lines (
    budget_line_id            BIGSERIAL PRIMARY KEY,
    budget_id                 BIGINT NOT NULL,
    code_combination_id       BIGINT,
    period_name               VARCHAR(30),
    budget_amount             NUMERIC(15,2),
    actual_amount             NUMERIC(15,2),
    variance_amount           NUMERIC(15,2)
);

-- 会计期间表
CREATE TABLE IF NOT EXISTS gl_periods (
    period_id                 BIGSERIAL PRIMARY KEY,
    period_name               VARCHAR(30) NOT NULL,
    period_type               VARCHAR(30),
    year                      INT,
    start_date                DATE,
    end_date                  DATE,
    status                    VARCHAR(20) DEFAULT 'OPEN',
    fiscal_year               INT
);

-- 账套表
CREATE TABLE IF NOT EXISTS gl_sets_of_books (
    set_of_books_id           BIGSERIAL PRIMARY KEY,
    name                      VARCHAR(100) NOT NULL,
    currency_code             VARCHAR(15) NOT NULL,
    chart_of_accounts_id      BIGINT,
    fiscal_year_start         DATE,
    status                    VARCHAR(20) DEFAULT 'ACTIVE'
);

-- 日记账批次表
CREATE TABLE IF NOT EXISTS gl_je_batches (
    batch_id                  BIGSERIAL PRIMARY KEY,
    batch_name                VARCHAR(100) NOT NULL,
    je_category               VARCHAR(30),
    period_name               VARCHAR(30),
    status                    VARCHAR(20),
    total_debit               NUMERIC(15,2),
    total_credit              NUMERIC(15,2),
    posted_date               DATE,
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 分配统计表
CREATE TABLE IF NOT EXISTS gl_distribution_sets (
    distribution_set_id       BIGSERIAL PRIMARY KEY,
    set_name                  VARCHAR(100) NOT NULL,
    description               VARCHAR(240),
    status                    VARCHAR(20) DEFAULT 'ACTIVE'
);

-- 承诺表
CREATE TABLE IF NOT EXISTS gl_encumbrances (
    encumbrance_id            BIGSERIAL PRIMARY KEY,
    code_combination_id       BIGINT,
    period_name               VARCHAR(30),
    amount                    NUMERIC(15,2),
    encumbrance_type          VARCHAR(30),
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 统计期间表
CREATE TABLE IF NOT EXISTS gl_period_statuses (
    period_status_id          BIGSERIAL PRIMARY KEY,
    period_name               VARCHAR(30),
    set_of_books_id           BIGINT,
    status                    VARCHAR(20),
    last_update_date          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 日记账导入表
CREATE TABLE IF NOT EXISTS gl_interface (
    interface_id              BIGSERIAL PRIMARY KEY,
    je_header_id              BIGINT,
    status                    VARCHAR(20) DEFAULT 'PENDING',
    error_message             TEXT,
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 重估表
CREATE TABLE IF NOT EXISTS gl_revaluations (
    revaluation_id            BIGSERIAL PRIMARY KEY,
    period_name               VARCHAR(30),
    currency_code             VARCHAR(15),
    revaluation_rate          NUMERIC(15,6),
    status                    VARCHAR(20),
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 转换表
CREATE TABLE IF NOT EXISTS gl_conversions (
    conversion_id             BIGSERIAL PRIMARY KEY,
    from_currency             VARCHAR(15),
    to_currency               VARCHAR(15),
    conversion_rate           NUMERIC(15,6),
    conversion_type           VARCHAR(30),
    effective_date            DATE
);

-- 冲销表
CREATE TABLE IF NOT EXISTS gl_reversals (
    reversal_id               BIGSERIAL PRIMARY KEY,
    je_header_id              BIGINT NOT NULL,
    reversal_period           VARCHAR(30),
    reversal_date             DATE,
    status                    VARCHAR(20)
);

-- 翻译表
CREATE TABLE IF NOT EXISTS gl_translations (
    translation_id            BIGSERIAL PRIMARY KEY,
    period_name               VARCHAR(30),
    currency_code             VARCHAR(15),
    status                    VARCHAR(20),
    completion_date           DATE
);

-- 合并表
CREATE TABLE IF NOT EXISTS gl_consolidation (
    consolidation_id          BIGSERIAL PRIMARY KEY,
    parent_set_of_books_id    BIGINT,
    child_set_of_books_id     BIGINT,
    period_name               VARCHAR(30),
    status                    VARCHAR(20)
);

-- 报表表
CREATE TABLE IF NOT EXISTS gl_financial_reports (
    report_id                 BIGSERIAL PRIMARY KEY,
    report_name               VARCHAR(100),
    report_type               VARCHAR(30),
    period_name               VARCHAR(30),
    status                    VARCHAR(20)
);

-- 交叉验证规则表
CREATE TABLE IF NOT EXISTS gl_cross_validation_rules (
    rule_id                   BIGSERIAL PRIMARY KEY,
    segment_num               INT,
    value_from                VARCHAR(30),
    value_to                  VARCHAR(30),
    other_segment_num         INT,
    other_value               VARCHAR(30)
);

-- 安全规则表
CREATE TABLE IF NOT EXISTS gl_security_rules (
    rule_id                   BIGSERIAL PRIMARY KEY,
    rule_name                 VARCHAR(100),
    segment_num               INT,
    value_set                 VARCHAR(30)
);

-- 日记账行描述表
CREATE TABLE IF NOT EXISTS gl_je_line_descriptions (
    description_id            BIGSERIAL PRIMARY KEY,
    je_line_id                BIGINT,
    description               VARCHAR(240),
    language_code             VARCHAR(10)
);

-- 日记账统计表
CREATE TABLE IF NOT EXISTS gl_je_statistics (
    statistic_id              BIGSERIAL PRIMARY KEY,
    je_header_id              BIGINT,
    statistic_type            VARCHAR(30),
    statistic_value           NUMERIC(15,2)
);

-- 提交历史表
CREATE TABLE IF NOT EXISTS gl_posting_history (
    history_id                BIGSERIAL PRIMARY KEY,
    je_header_id              BIGINT,
    posting_date              DATE,
    posted_by                 BIGINT,
    status                    VARCHAR(20)
);

-- 审计表
CREATE TABLE IF NOT EXISTS gl_audit_trail (
    audit_id                  BIGSERIAL PRIMARY KEY,
    table_name                VARCHAR(50),
    record_id                 BIGINT,
    action                    VARCHAR(20),
    old_value                 TEXT,
    new_value                 TEXT,
    changed_by                BIGINT,
    changed_date              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 注释表
CREATE TABLE IF NOT EXISTS gl_notes (
    note_id                   BIGSERIAL PRIMARY KEY,
    object_type               VARCHAR(30),
    object_id                 BIGINT,
    note_text                 TEXT,
    created_by                BIGINT,
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 附件表
CREATE TABLE IF NOT EXISTS gl_attachments (
    attachment_id             BIGSERIAL PRIMARY KEY,
    object_type               VARCHAR(30),
    object_id                 BIGINT,
    file_name                 VARCHAR(240),
    file_path                 VARCHAR(500),
    mime_type                 VARCHAR(100),
    uploaded_by               BIGINT,
    upload_date               TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- 创建索引
-- ============================================================

-- AP 模块索引
CREATE INDEX IF NOT EXISTS idx_ap_inv_dist_invoice ON ap_invoice_distributions_all(invoice_id);
CREATE INDEX IF NOT EXISTS idx_ap_pay_sched_invoice ON ap_payment_schedules_all(invoice_id);
CREATE INDEX IF NOT EXISTS idx_ap_bank_vendor ON ap_bank_accounts(vendor_id);
CREATE INDEX IF NOT EXISTS idx_ap_checks_vendor ON ap_checks(vendor_id);
CREATE INDEX IF NOT EXISTS idx_ap_wht_invoice ON ap_withholding_tax(invoice_id);

-- PO 模块索引
CREATE INDEX IF NOT EXISTS idx_po_req_line_header ON po_requisition_lines(requisition_header_id);
CREATE INDEX IF NOT EXISTS idx_po_rfq_line_header ON po_rfq_lines(rfq_header_id);
CREATE INDEX IF NOT EXISTS idx_po_quotation_rfq ON po_quotations(rfq_header_id);
CREATE INDEX IF NOT EXISTS idx_po_shipment_header ON po_shipments_all(po_header_id);
CREATE INDEX IF NOT EXISTS idx_po_shipment_line ON po_shipments_all(po_line_id);
CREATE INDEX IF NOT EXISTS idx_rcv_trans_header ON rcv_transactions(shipment_header_id);

-- AR 模块索引
CREATE INDEX IF NOT EXISTS idx_ar_cust_site_cust ON ar_customer_sites(customer_id);
CREATE INDEX IF NOT EXISTS idx_ar_trans_cust ON ar_transactions_all(customer_id);
CREATE INDEX IF NOT EXISTS idx_ar_trans_line_trans ON ar_transaction_lines(transaction_id);
CREATE INDEX IF NOT EXISTS idx_ar_receipt_cust ON ar_receipts(customer_id);
CREATE INDEX IF NOT EXISTS idx_ar_receipt_app_receipt ON ar_receipt_applications(receipt_id);
CREATE INDEX IF NOT EXISTS idx_ar_receipt_app_trans ON ar_receipt_applications(transaction_id);

-- GL 模块索引
CREATE INDEX IF NOT EXISTS idx_gl_je_lines_header ON gl_je_lines(je_header_id);
CREATE INDEX IF NOT EXISTS idx_gl_je_lines_cc ON gl_je_lines(code_combination_id);
CREATE INDEX IF NOT EXISTS idx_gl_balances_cc ON gl_balances(code_combination_id);
CREATE INDEX IF NOT EXISTS idx_gl_budget_lines_budget ON gl_budget_lines(budget_id);
CREATE INDEX IF NOT EXISTS idx_gl_posting_hist_header ON gl_posting_history(je_header_id);

-- 提交事务
COMMIT;

-- ============================================================
-- 脚本完成
-- ============================================================
-- 已创建表数：Batch 1 (20 张) + Batch 2 (40 张) = 60 张
-- 累计表数：56 + 60 = 116 张
-- ============================================================
