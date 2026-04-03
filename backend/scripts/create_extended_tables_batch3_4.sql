-- ============================================================
-- Oracle EBS ERP 扩展表创建脚本 (Batch 3-4)
-- ============================================================
-- 目标：从 93 张表扩展到 177 张核心表
-- 数据库：PostgreSQL 14+
-- 字符集：UTF8
-- 创建日期：2026-04-03
-- ============================================================

-- 开始事务
BEGIN;

-- ============================================================
-- Batch 3: INV/OM 模块扩展 (40 张表)
-- ============================================================

-- 1. INV (库存管理) 模块扩展表
-- ============================================================

-- 物料主表
CREATE TABLE IF NOT EXISTS inv_system_items_b (
    inventory_item_id         BIGSERIAL PRIMARY KEY,
    segment1                  VARCHAR(30) NOT NULL,
    organization_id           BIGINT NOT NULL,
    description               VARCHAR(240),
    item_type                 VARCHAR(30),
    status                    VARCHAR(20) DEFAULT 'ACTIVE',
    primary_uom_code          VARCHAR(10),
    base_unit_of_measure      VARCHAR(30),
    inventory_item_flag       VARCHAR(1) DEFAULT 'Y',
    stockable_flag            VARCHAR(1) DEFAULT 'Y',
    transactable_flag         VARCHAR(1) DEFAULT 'Y',
    mtl_planning_code         INT,
    min_minmax_quantity       NUMERIC(15,2),
    max_minmax_quantity       NUMERIC(15,2),
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by                BIGINT,
    last_update_date          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 物料组织分配表
CREATE TABLE IF NOT EXISTS inv_item_org_assignments (
    assignment_id             BIGSERIAL PRIMARY KEY,
    inventory_item_id         BIGINT NOT NULL,
    organization_id           BIGINT NOT NULL,
    status                    VARCHAR(20) DEFAULT 'ACTIVE',
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 库存余额表
CREATE TABLE IF NOT EXISTS inv_onhand_quantities (
    onhand_id                 BIGSERIAL PRIMARY KEY,
    inventory_item_id         BIGINT NOT NULL,
    organization_id           BIGINT NOT NULL,
    subinventory_code         VARCHAR(10),
    locator_id                BIGINT,
    quantity                  NUMERIC(15,2) NOT NULL,
    unit_cost                 NUMERIC(15,2),
    total_value               NUMERIC(15,2),
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 货位子表
CREATE TABLE IF NOT EXISTS inv_secondary_locators (
    locator_id                BIGSERIAL PRIMARY KEY,
    organization_id           BIGINT NOT NULL,
    subinventory_code         VARCHAR(10),
    segment1                  VARCHAR(20),
    segment2                  VARCHAR(20),
    segment3                  VARCHAR(20),
    segment4                  VARCHAR(20),
    description               VARCHAR(240),
    status                    VARCHAR(20) DEFAULT 'ACTIVE'
);

-- 库存交易表
CREATE TABLE IF NOT EXISTS inv_material_transactions (
    transaction_id            BIGSERIAL PRIMARY KEY,
    transaction_date          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    inventory_item_id         BIGINT NOT NULL,
    organization_id           BIGINT NOT NULL,
    transaction_type_id       INT,
    transaction_type_name     VARCHAR(80),
    quantity                  NUMERIC(15,2),
    primary_quantity          NUMERIC(15,2),
    transaction_cost          NUMERIC(15,2),
    source_document_id        BIGINT,
    source_document_type_id   INT,
    rcv_transaction_id        BIGINT,
    subinventory_code         VARCHAR(10),
    locator_id                BIGINT,
    account_id                BIGINT,
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by                BIGINT
);

-- 交易类型表
CREATE TABLE IF NOT EXISTS inv_transaction_types (
    transaction_type_id       BIGSERIAL PRIMARY KEY,
    transaction_type_name     VARCHAR(80) NOT NULL,
    description               VARCHAR(240),
    transaction_action_id     INT,
    transaction_source_type_id INT,
    status                    VARCHAR(20) DEFAULT 'ACTIVE'
);

-- 物料类别表
CREATE TABLE IF NOT EXISTS inv_item_categories (
    category_id               BIGSERIAL PRIMARY KEY,
    category_set_id           BIGINT,
    structure_id              BIGINT,
    segment1                  VARCHAR(30),
    segment2                  VARCHAR(30),
    segment3                  VARCHAR(30),
    description               VARCHAR(240),
    parent_category_id        BIGINT,
    status                    VARCHAR(20) DEFAULT 'ACTIVE'
);

-- 物料类别分配表
CREATE TABLE IF NOT EXISTS inv_item_category_assignments (
    assignment_id             BIGSERIAL PRIMARY KEY,
    inventory_item_id         BIGINT NOT NULL,
    category_id               BIGINT NOT NULL,
    category_set_id           BIGINT,
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 库存组织参数表
CREATE TABLE IF NOT EXISTS inv_organization_parameters (
    organization_id           BIGSERIAL PRIMARY KEY,
    organization_code         VARCHAR(10) NOT NULL,
    organization_name         VARCHAR(240) NOT NULL,
    master_organization_id    BIGINT,
    location_id               BIGINT,
    status                    VARCHAR(20) DEFAULT 'ACTIVE',
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 库存周期盘点表
CREATE TABLE IF NOT EXISTS inv_cycle_count_headers (
    cycle_count_id            BIGSERIAL PRIMARY KEY,
    organization_id           BIGINT NOT NULL,
    cycle_count_name          VARCHAR(80) NOT NULL,
    description               VARCHAR(240),
    status                    VARCHAR(20) DEFAULT 'ACTIVE',
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 周期盘点行表
CREATE TABLE IF NOT EXISTS inv_cycle_count_entries (
    entry_id                  BIGSERIAL PRIMARY KEY,
    cycle_count_id            BIGINT NOT NULL,
    inventory_item_id         BIGINT NOT NULL,
    locator_id                BIGINT,
    status                    VARCHAR(20),
    last_count_date           DATE
);

-- 库存调整表
CREATE TABLE IF NOT EXISTS inv_adjustment_headers (
    adjustment_id             BIGSERIAL PRIMARY KEY,
    organization_id           BIGINT NOT NULL,
    adjustment_number         VARCHAR(50) NOT NULL,
    status                    VARCHAR(20) DEFAULT 'PENDING',
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 库存调整行表
CREATE TABLE IF NOT EXISTS inv_adjustment_lines (
    line_id                   BIGSERIAL PRIMARY KEY,
    adjustment_id             BIGINT NOT NULL,
    inventory_item_id         BIGINT NOT NULL,
    locator_id                BIGINT,
    quantity                  NUMERIC(15,2),
    unit_cost                 NUMERIC(15,2),
    reason                    VARCHAR(240)
);

-- 库存暂收表
CREATE TABLE IF NOT EXISTS inv_receiving_temporary (
    temp_id                   BIGSERIAL PRIMARY KEY,
    inventory_item_id         BIGINT,
    quantity                  NUMERIC(15,2),
    source_document_id        BIGINT,
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 库存保留表
CREATE TABLE IF NOT EXISTS inv_reservations (
    reservation_id            BIGSERIAL PRIMARY KEY,
    inventory_item_id         BIGINT NOT NULL,
    organization_id           BIGINT NOT NULL,
    demand_source_type_id     INT,
    demand_source_header_id   BIGINT,
    demand_source_line_id     BIGINT,
    supply_source_type_id     INT,
    supply_source_header_id   BIGINT,
    quantity                  NUMERIC(15,2),
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. OM (销售订单) 模块扩展表
-- ============================================================

-- 销售订单头表
CREATE TABLE IF NOT EXISTS oe_order_headers_all (
    header_id                 BIGSERIAL PRIMARY KEY,
    order_number              VARCHAR(50) NOT NULL,
    org_id                    BIGINT,
    order_type_id             BIGINT,
    customer_id               BIGINT NOT NULL,
    ship_to_org_id            BIGINT,
    invoice_to_org_id         BIGINT,
    sales_rep_id              BIGINT,
    order_date                DATE,
    flow_status_code          VARCHAR(30),
    booked_flag               VARCHAR(1) DEFAULT 'N',
    booked_date               DATE,
    status                    VARCHAR(20) DEFAULT 'ENTERED',
    total_amount              NUMERIC(15,2),
    currency_code             VARCHAR(15),
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by                BIGINT
);

-- 销售订单行表
CREATE TABLE IF NOT EXISTS oe_order_lines_all (
    line_id                   BIGSERIAL PRIMARY KEY,
    header_id                 BIGINT NOT NULL,
    line_number               INT NOT NULL,
    inventory_item_id         BIGINT,
    item_identifier_type      VARCHAR(30),
    ordered_quantity          NUMERIC(15,2),
    shipped_quantity          NUMERIC(15,2) DEFAULT 0,
    invoiced_quantity         NUMERIC(15,2) DEFAULT 0,
    unit_selling_price        NUMERIC(15,2),
    list_price                NUMERIC(15,2),
    amount                    NUMERIC(15,2),
    ship_to_org_id            BIGINT,
    ship_from_org_id          BIGINT,
    inventory_item_seg1       VARCHAR(30),
    flow_status_code          VARCHAR(30),
    status                    VARCHAR(20),
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 订单类型表
CREATE TABLE IF NOT EXISTS oe_order_types (
    order_type_id             BIGSERIAL PRIMARY KEY,
    name                      VARCHAR(100) NOT NULL,
    description               VARCHAR(240),
    org_id                    BIGINT,
    status                    VARCHAR(20) DEFAULT 'ACTIVE'
);

-- 销售信贷表
CREATE TABLE IF NOT EXISTS oe_credit_check_results (
    credit_check_id           BIGSERIAL PRIMARY KEY,
    header_id                 BIGINT NOT NULL,
    check_date                DATE,
    result                    VARCHAR(20),
    credit_limit              NUMERIC(15,2),
    available_credit          NUMERIC(15,2)
);

-- 订单发运表
CREATE TABLE IF NOT EXISTS oe_shipments (
    shipment_id               BIGSERIAL PRIMARY KEY,
    header_id                 BIGINT,
    line_id                   BIGINT,
    delivery_id               BIGINT,
    shipped_quantity          NUMERIC(15,2),
    ship_date                 DATE,
    carrier_id                BIGINT,
    tracking_number           VARCHAR(100),
    status                    VARCHAR(20)
);

-- 发运方法表
CREATE TABLE IF NOT EXISTS oe_ship_methods (
    ship_method_id            BIGSERIAL PRIMARY KEY,
    carrier_id                BIGINT,
    ship_method_code          VARCHAR(30) NOT NULL,
    description               VARCHAR(240),
    status                    VARCHAR(20) DEFAULT 'ACTIVE'
);

-- 承运商表
CREATE TABLE IF NOT EXISTS oe_carriers (
    carrier_id                BIGSERIAL PRIMARY KEY,
    carrier_name              VARCHAR(100) NOT NULL,
    carrier_code              VARCHAR(30),
    status                    VARCHAR(20) DEFAULT 'ACTIVE'
);

-- 订单价格调整表
CREATE TABLE IF NOT EXISTS oe_price_adjustments (
    adjustment_id             BIGSERIAL PRIMARY KEY,
    header_id                 BIGINT,
    line_id                   BIGINT,
    adjustment_type           VARCHAR(30),
    adjustment_amount         NUMERIC(15,2),
    reason                    VARCHAR(240),
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 订单持有表
CREATE TABLE IF NOT EXISTS oe_order_holds (
    hold_id                   BIGSERIAL PRIMARY KEY,
    header_id                 BIGINT,
    line_id                   BIGINT,
    hold_source               VARCHAR(30),
    hold_reason               VARCHAR(240),
    released_flag             VARCHAR(1) DEFAULT 'N',
    release_date              DATE
);

-- 订单工作流表
CREATE TABLE IF NOT EXISTS oe_order_workflows (
    workflow_id               BIGSERIAL PRIMARY KEY,
    header_id                 BIGINT NOT NULL,
    item_type                 VARCHAR(30),
    item_key                  VARCHAR(240),
    status                    VARCHAR(20),
    begin_date                DATE,
    end_date                  DATE
);

-- 退货表
CREATE TABLE IF NOT EXISTS oe_returns (
    return_id                 BIGSERIAL PRIMARY KEY,
    return_number             VARCHAR(50) NOT NULL,
    original_order_id         BIGINT,
    original_line_id          BIGINT,
    customer_id               BIGINT,
    return_reason             VARCHAR(240),
    status                    VARCHAR(20),
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 退货行表
CREATE TABLE IF NOT EXISTS oe_return_lines (
    return_line_id            BIGSERIAL PRIMARY KEY,
    return_id                 BIGINT NOT NULL,
    inventory_item_id         BIGINT,
    quantity                  NUMERIC(15,2),
    reason                    VARCHAR(240),
    status                    VARCHAR(20)
);

-- 定价修饰语表
CREATE TABLE IF NOT EXISTS qp_pricing_attributes (
    pricing_attr_id           BIGSERIAL PRIMARY KEY,
    price_list_header_id      BIGINT,
    product_attribute_code    VARCHAR(30),
    product_attr_value        VARCHAR(240),
    pricing_phase_id          INT
);

-- 价格清单表
CREATE TABLE IF NOT EXISTS qp_list_headers (
    list_header_id            BIGSERIAL PRIMARY KEY,
    list_type_code            VARCHAR(30),
    name                      VARCHAR(100),
    description               VARCHAR(240),
    currency_code             VARCHAR(15),
    status                    VARCHAR(20) DEFAULT 'ACTIVE',
    start_date                DATE,
    end_date                  DATE
);

-- 价格清单行表
CREATE TABLE IF NOT EXISTS qp_list_lines (
    list_line_id              BIGSERIAL PRIMARY KEY,
    list_header_id            BIGINT NOT NULL,
    list_line_type_code       VARCHAR(30),
    operand                   NUMERIC(15,2),
    arithmetic_operator       VARCHAR(30),
    inventory_item_id         BIGINT,
    product_attribute_code    VARCHAR(30),
    start_date                DATE,
    end_date                  DATE
);

-- 定价 qualifier 表
CREATE TABLE IF NOT EXISTS qp_qualifiers (
    qualifier_id              BIGSERIAL PRIMARY KEY,
    list_header_id            BIGINT,
    qualifier_type_code       VARCHAR(30),
    qualifier_attribute       VARCHAR(30),
    qualifier_value           VARCHAR(240)
);

-- 折扣表
CREATE TABLE IF NOT EXISTS qp_discounts (
    discount_id               BIGSERIAL PRIMARY KEY,
    discount_name             VARCHAR(100),
    discount_type             VARCHAR(30),
    discount_value            NUMERIC(15,2),
    status                    VARCHAR(20) DEFAULT 'ACTIVE'
);

-- 促销表
CREATE TABLE IF NOT EXISTS qp_promotions (
    promotion_id              BIGSERIAL PRIMARY KEY,
    promotion_name            VARCHAR(100),
    description               VARCHAR(240),
    start_date                DATE,
    end_date                  DATE,
    status                    VARCHAR(20) DEFAULT 'ACTIVE'
);

-- 订单成本表
CREATE TABLE IF NOT EXISTS oe_order_costs (
    cost_id                   BIGSERIAL PRIMARY KEY,
    header_id                 BIGINT,
    line_id                   BIGINT,
    cost_type                 VARCHAR(30),
    cost_amount               NUMERIC(15,2),
    currency_code             VARCHAR(15)
);

-- 订单税表
CREATE TABLE IF NOT EXISTS oe_order_taxes (
    tax_id                    BIGSERIAL PRIMARY KEY,
    header_id                 BIGINT,
    line_id                   BIGINT,
    tax_code                  VARCHAR(30),
    tax_rate                  NUMERIC(5,2),
    tax_amount                NUMERIC(15,2)
);

-- 订单付款计划表
CREATE TABLE IF NOT EXISTS oe_payment_schedules (
    schedule_id               BIGSERIAL PRIMARY KEY,
    header_id                 BIGINT NOT NULL,
    payment_sequence          INT,
    due_date                  DATE,
    amount                    NUMERIC(15,2),
    status                    VARCHAR(20) DEFAULT 'PENDING'
);

-- 订单备注表
CREATE TABLE IF NOT EXISTS oe_order_notes (
    note_id                   BIGSERIAL PRIMARY KEY,
    header_id                 BIGINT,
    line_id                   BIGINT,
    note_type                 VARCHAR(30),
    note_text                 TEXT,
    created_by                BIGINT,
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 订单附件表
CREATE TABLE IF NOT EXISTS oe_order_attachments (
    attachment_id             BIGSERIAL PRIMARY KEY,
    header_id                 BIGINT,
    line_id                   BIGINT,
    file_name                 VARCHAR(240),
    file_path                 VARCHAR(500),
    mime_type                 VARCHAR(100),
    uploaded_by               BIGINT,
    upload_date               TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 订单审计表
CREATE TABLE IF NOT EXISTS oe_order_audit (
    audit_id                  BIGSERIAL PRIMARY KEY,
    header_id                 BIGINT,
    line_id                   BIGINT,
    action                    VARCHAR(30),
    old_value                 TEXT,
    new_value                 TEXT,
    changed_by                BIGINT,
    changed_date              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 订单状态历史表
CREATE TABLE IF NOT EXISTS oe_order_status_history (
    history_id                BIGSERIAL PRIMARY KEY,
    header_id                 BIGINT NOT NULL,
    line_id                   BIGINT,
    status_code               VARCHAR(30),
    status_date               TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    comments                  TEXT
);

-- ============================================================
-- Batch 4: 其他模块扩展 (44 张表)
-- ============================================================

-- 3. FA (固定资产) 模块扩展表
-- ============================================================

-- 资产类别表
CREATE TABLE IF NOT EXISTS fa_category_defs (
    category_id               BIGSERIAL PRIMARY KEY,
    category_key              VARCHAR(30) NOT NULL,
    description               VARCHAR(240),
    property_type_code        VARCHAR(30),
    depreciation_method       VARCHAR(30),
    life                      INT,
    status                    VARCHAR(20) DEFAULT 'ACTIVE'
);

-- 资产账簿表
CREATE TABLE IF NOT EXISTS fa_book_controls (
    book_id                   BIGSERIAL PRIMARY KEY,
    book_type_code            VARCHAR(30) NOT NULL,
    description               VARCHAR(240),
    currency_code             VARCHAR(15),
    fiscal_year_name          VARCHAR(30),
    status                    VARCHAR(20) DEFAULT 'ACTIVE'
);

-- 资产添加表
CREATE TABLE IF NOT EXISTS fa_additions_b (
    addition_id               BIGSERIAL PRIMARY KEY,
    asset_id                  BIGINT NOT NULL,
    date_placed_in_service    DATE,
    cost                      NUMERIC(15,2),
    category_id               BIGINT,
    book_id                   BIGINT,
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 资产折旧明细表
CREATE TABLE IF NOT EXISTS fa_deprn_detail (
    deprn_id                  BIGSERIAL PRIMARY KEY,
    asset_id                  BIGINT NOT NULL,
    book_id                   BIGINT NOT NULL,
    period_name               VARCHAR(30),
    depreciation_expense      NUMERIC(15,2),
    accumulated_deprn         NUMERIC(15,2),
    net_book_value            NUMERIC(15,2),
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 资产交易表
CREATE TABLE IF NOT EXISTS fa_transactions (
    transaction_id            BIGSERIAL PRIMARY KEY,
    asset_id                  BIGINT NOT NULL,
    transaction_type          VARCHAR(30),
    transaction_date          DATE,
    amount                    NUMERIC(15,2),
    status                    VARCHAR(20),
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 资产报废表
CREATE TABLE IF NOT EXISTS fa_retirements (
    retirement_id             BIGSERIAL PRIMARY KEY,
    asset_id                  BIGINT NOT NULL,
    retirement_date           DATE,
    proceeds_of_sale          NUMERIC(15,2),
    cost_of_removal           NUMERIC(15,2),
    status                    VARCHAR(20)
);

-- 资产重估表
CREATE TABLE IF NOT EXISTS fa_revaluations (
    revaluation_id            BIGSERIAL PRIMARY KEY,
    asset_id                  BIGINT NOT NULL,
    revaluation_date          DATE,
    new_cost                  NUMERIC(15,2),
    revaluation_type          VARCHAR(30)
);

-- 资产转移表
CREATE TABLE IF NOT EXISTS fa_transfers (
    transfer_id               BIGSERIAL PRIMARY KEY,
    asset_id                  BIGINT NOT NULL,
    from_location             VARCHAR(100),
    to_location               VARCHAR(100),
    transfer_date             DATE,
    status                    VARCHAR(20)
);

-- 4. HR (人力资源) 模块扩展表
-- ============================================================

-- 员工全表
CREATE TABLE IF NOT EXISTS per_all_people_f (
    person_id                 BIGSERIAL PRIMARY KEY,
    employee_number           VARCHAR(30),
    full_name                 VARCHAR(240),
    first_name                VARCHAR(50),
    last_name                 VARCHAR(50),
    date_of_birth             DATE,
    gender                    VARCHAR(10),
    national_identifier       VARCHAR(30),
    date_from                 DATE,
    date_to                   DATE,
    status                    VARCHAR(20) DEFAULT 'ACTIVE'
);

-- 员工分配表
CREATE TABLE IF NOT EXISTS per_assignments_f (
    assignment_id             BIGSERIAL PRIMARY KEY,
    person_id                 BIGINT NOT NULL,
    organization_id           BIGINT,
    job_id                    BIGINT,
    position_id               BIGINT,
    grade_id                  BIGINT,
    location_id               BIGINT,
    assignment_number         VARCHAR(30),
    assignment_status_type_id INT,
    primary_flag              VARCHAR(1) DEFAULT 'Y',
    date_from                 DATE,
    date_to                   DATE
);

-- 职位表
CREATE TABLE IF NOT EXISTS per_jobs_f (
    job_id                    BIGSERIAL PRIMARY KEY,
    job_code                  VARCHAR(30) NOT NULL,
    name                      VARCHAR(100),
    description               VARCHAR(240),
    job_group_id              BIGINT,
    date_from                 DATE,
    date_to                   DATE
);

-- 岗位表
CREATE TABLE IF NOT EXISTS per_positions_f (
    position_id               BIGSERIAL PRIMARY KEY,
    position_code             VARCHAR(30) NOT NULL,
    name                      VARCHAR(100),
    description               VARCHAR(240),
    organization_id           BIGINT,
    job_id                    BIGINT,
    date_from                 DATE,
    date_to                   DATE
);

-- 职级表
CREATE TABLE IF NOT EXISTS per_grades_f (
    grade_id                  BIGSERIAL PRIMARY KEY,
    grade_code                VARCHAR(30) NOT NULL,
    name                      VARCHAR(100),
    description               VARCHAR(240),
    date_from                 DATE,
    date_to                   DATE
);

-- 员工薪酬表
CREATE TABLE IF NOT EXISTS per_pay_proposals_f (
    proposal_id               BIGSERIAL PRIMARY KEY,
    assignment_id             BIGINT NOT NULL,
    proposed_salary           NUMERIC(15,2),
    currency_code             VARCHAR(15),
    change_date               DATE,
    date_from                 DATE,
    date_to                   DATE
);

-- 5. PA (项目管理) 模块扩展表
-- ============================================================

-- 项目全表
CREATE TABLE IF NOT EXISTS pa_projects_all (
    project_id                BIGSERIAL PRIMARY KEY,
    project_number            VARCHAR(30) NOT NULL,
    project_name              VARCHAR(100) NOT NULL,
    project_type              VARCHAR(30),
    status                    VARCHAR(20) DEFAULT 'ACTIVE',
    manager_id                BIGINT,
    organization_id           BIGINT,
    start_date                DATE,
    completion_date           DATE,
    budget_amount             NUMERIC(15,2),
    actual_cost               NUMERIC(15,2),
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 项目任务表
CREATE TABLE IF NOT EXISTS pa_tasks (
    task_id                   BIGSERIAL PRIMARY KEY,
    project_id                BIGINT NOT NULL,
    task_number               VARCHAR(30) NOT NULL,
    task_name                 VARCHAR(100),
    parent_task_id            BIGINT,
    status                    VARCHAR(20),
    start_date                DATE,
    completion_date           DATE
);

-- 项目预算版本表
CREATE TABLE IF NOT EXISTS pa_budget_versions (
    budget_version_id         BIGSERIAL PRIMARY KEY,
    project_id                BIGINT NOT NULL,
    version_type              VARCHAR(30),
    version_name              VARCHAR(100),
    status                    VARCHAR(20) DEFAULT 'DRAFT',
    budget_amount             NUMERIC(15,2),
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 项目支出表
CREATE TABLE IF NOT EXISTS pa_expenditures_all (
    expenditure_id            BIGSERIAL PRIMARY KEY,
    project_id                BIGINT NOT NULL,
    task_id                   BIGINT,
    expenditure_type          VARCHAR(30),
    expenditure_date          DATE,
    quantity                  NUMERIC(15,2),
    unit_cost                 NUMERIC(15,2),
    total_cost                NUMERIC(15,2),
    status                    VARCHAR(20),
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. CST (成本管理) 模块扩展表
-- ============================================================

-- 成本类型表
CREATE TABLE IF NOT EXISTS cst_cost_types (
    cost_type_id              BIGSERIAL PRIMARY KEY,
    cost_type                 VARCHAR(30) NOT NULL,
    description               VARCHAR(240),
    status                    VARCHAR(20) DEFAULT 'ACTIVE'
);

-- 成本要素表
CREATE TABLE IF NOT EXISTS cst_cost_elements (
    cost_element_id           BIGSERIAL PRIMARY KEY,
    cost_element              VARCHAR(30) NOT NULL,
    description               VARCHAR(240),
    status                    VARCHAR(20) DEFAULT 'ACTIVE'
);

-- 物料成本表
CREATE TABLE IF NOT EXISTS cst_item_costs (
    item_cost_id              BIGSERIAL PRIMARY KEY,
    inventory_item_id         BIGINT NOT NULL,
    organization_id           BIGINT NOT NULL,
    cost_type_id              BIGINT,
    material_cost             NUMERIC(15,2),
    labor_cost                NUMERIC(15,2),
    overhead_cost             NUMERIC(15,2),
    total_cost                NUMERIC(15,2),
    currency_code             VARCHAR(15),
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. 基础数据表
-- ============================================================

-- 货币表
CREATE TABLE IF NOT EXISTS fnd_currencies (
    currency_code             VARCHAR(15) PRIMARY KEY,
    currency_name             VARCHAR(100),
    symbol                    VARCHAR(10),
    precision                 INT DEFAULT 2,
    status                    VARCHAR(20) DEFAULT 'ACTIVE'
);

-- 国家表
CREATE TABLE IF NOT EXISTS fnd_countries (
    country_code              VARCHAR(2) PRIMARY KEY,
    country_name              VARCHAR(100),
    iso_code                  VARCHAR(3),
    status                    VARCHAR(20) DEFAULT 'ACTIVE'
);

-- 地点表
CREATE TABLE IF NOT EXISTS fnd_locations (
    location_id               BIGSERIAL PRIMARY KEY,
    location_code             VARCHAR(30),
    address_line1             VARCHAR(240),
    city                      VARCHAR(80),
    country                   VARCHAR(80),
    postal_code               VARCHAR(30),
    status                    VARCHAR(20) DEFAULT 'ACTIVE'
);

-- 用户表
CREATE TABLE IF NOT EXISTS fnd_user (
    user_id                   BIGSERIAL PRIMARY KEY,
    username                  VARCHAR(100) NOT NULL,
    password_hash             VARCHAR(256),
    email                     VARCHAR(240),
    status                    VARCHAR(20) DEFAULT 'ACTIVE',
    creation_date             TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 责任表
CREATE TABLE IF NOT EXISTS fnd_responsibilities (
    responsibility_id         BIGSERIAL PRIMARY KEY,
    responsibility_key        VARCHAR(100) NOT NULL,
    responsibility_name       VARCHAR(240),
    status                    VARCHAR(20) DEFAULT 'ACTIVE'
);

-- 菜单表
CREATE TABLE IF NOT EXISTS fnd_menus (
    menu_id                   BIGSERIAL PRIMARY KEY,
    menu_name                 VARCHAR(100) NOT NULL,
    description               VARCHAR(240),
    status                    VARCHAR(20) DEFAULT 'ACTIVE'
);

-- 并发请求表
CREATE TABLE IF NOT EXISTS fnd_concurrent_requests (
    request_id                BIGSERIAL PRIMARY KEY,
    program_id                BIGINT,
    status                    VARCHAR(20),
    phase                     VARCHAR(20),
    requested_by              BIGINT,
    request_date              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completion_date           DATE
);

-- 8. BOM (物料清单) 模块扩展表
-- ============================================================

-- BOM 头表
CREATE TABLE IF NOT EXISTS bom_bill_of_materials (
    bill_id                   BIGSERIAL PRIMARY KEY,
    assembly_item_id          BIGINT NOT NULL,
    organization_id           BIGINT NOT NULL,
    bill_sequence_id          BIGINT,
    common_bill_sequence_id   BIGINT,
    status                    VARCHAR(20) DEFAULT 'ACTIVE'
);

-- BOM 组件表
CREATE TABLE IF NOT EXISTS bom_inventory_components (
    component_id              BIGSERIAL PRIMARY KEY,
    bill_sequence_id          BIGINT NOT NULL,
    component_item_id         BIGINT NOT NULL,
    component_quantity        NUMERIC(15,2),
    operation_seq_num         NUMERIC(5,2),
    position_seq              NUMERIC(5,2),
    status                    VARCHAR(20)
);

-- 工艺路线表
CREATE TABLE IF NOT EXISTS bom_operational_routings (
    routing_id                BIGSERIAL PRIMARY KEY,
    assembly_item_id          BIGINT NOT NULL,
    organization_id           BIGINT,
    routing_sequence_id       BIGINT,
    status                    VARCHAR(20) DEFAULT 'ACTIVE'
);

-- 工序表
CREATE TABLE IF NOT EXISTS bom_operations (
    operation_id              BIGSERIAL PRIMARY KEY,
    routing_sequence_id       BIGINT NOT NULL,
    operation_seq_num         NUMERIC(5,2),
    operation_code            VARCHAR(30),
    description               VARCHAR(240)
);

-- 9. WIP (在制品) 模块扩展表
-- ============================================================

-- WIP 工单表
CREATE TABLE IF NOT EXISTS wip_discrete_jobs (
    job_id                    BIGSERIAL PRIMARY KEY,
    job_number                VARCHAR(30) NOT NULL,
    assembly_item_id          BIGINT NOT NULL,
    organization_id           BIGINT NOT NULL,
    status                    VARCHAR(20) DEFAULT 'RELEASED',
    start_quantity            NUMERIC(15,2),
    quantity_completed        NUMERIC(15,2) DEFAULT 0,
    quantity_scrapped         NUMERIC(15,2) DEFAULT 0,
    start_date                DATE,
    completion_date           DATE
);

-- WIP 工单工序表
CREATE TABLE IF NOT EXISTS wip_job_operations (
    job_operation_id          BIGSERIAL PRIMARY KEY,
    job_id                    BIGINT NOT NULL,
    operation_seq_num         NUMERIC(5,2),
    status                    VARCHAR(20),
    quantity_completed        NUMERIC(15,2)
);

-- WIP 物料需求表
CREATE TABLE IF NOT EXISTS wip_requirement_operations (
    requirement_id            BIGSERIAL PRIMARY KEY,
    job_id                    BIGINT NOT NULL,
    component_item_id         BIGINT NOT NULL,
    required_quantity         NUMERIC(15,2),
    quantity_issued           NUMERIC(15,2) DEFAULT 0
);

-- WIP 交易表
CREATE TABLE IF NOT EXISTS wip_transactions (
    transaction_id            BIGSERIAL PRIMARY KEY,
    job_id                    BIGINT NOT NULL,
    transaction_type          VARCHAR(30),
    transaction_date          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    quantity                  NUMERIC(15,2),
    status                    VARCHAR(20)
);

-- ============================================================
-- 创建索引
-- ============================================================

-- INV 模块索引
CREATE INDEX IF NOT EXISTS idx_inv_sys_item_org ON inv_system_items_b(organization_id);
CREATE INDEX IF NOT EXISTS idx_inv_onhand_item ON inv_onhand_quantities(inventory_item_id);
CREATE INDEX IF NOT EXISTS idx_inv_onhand_org ON inv_onhand_quantities(organization_id);
CREATE INDEX IF NOT EXISTS idx_inv_mat_trans_item ON inv_material_transactions(inventory_item_id);
CREATE INDEX IF NOT EXISTS idx_inv_mat_trans_org ON inv_material_transactions(organization_id);
CREATE INDEX IF NOT EXISTS idx_inv_mat_trans_date ON inv_material_transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_inv_reserv_item ON inv_reservations(inventory_item_id);
CREATE INDEX IF NOT EXISTS idx_inv_reserv_demand ON inv_reservations(demand_source_header_id);

-- OM 模块索引
CREATE INDEX IF NOT EXISTS idx_oe_order_hdr_cust ON oe_order_headers_all(customer_id);
CREATE INDEX IF NOT EXISTS idx_oe_order_hdr_date ON oe_order_headers_all(order_date);
CREATE INDEX IF NOT EXISTS idx_oe_order_line_hdr ON oe_order_lines_all(header_id);
CREATE INDEX IF NOT EXISTS idx_oe_order_line_item ON oe_order_lines_all(inventory_item_id);
CREATE INDEX IF NOT EXISTS idx_oe_shipment_hdr ON oe_shipments(header_id);
CREATE INDEX IF NOT EXISTS idx_oe_shipment_line ON oe_shipments(line_id);
CREATE INDEX IF NOT EXISTS idx_qp_list_lines_hdr ON qp_list_lines(list_header_id);
CREATE INDEX IF NOT EXISTS idx_qp_list_lines_item ON qp_list_lines(inventory_item_id);

-- FA 模块索引
CREATE INDEX IF NOT EXISTS idx_fa_addition_asset ON fa_additions_b(asset_id);
CREATE INDEX IF NOT EXISTS idx_fa_deprn_asset ON fa_deprn_detail(asset_id);
CREATE INDEX IF NOT EXISTS idx_fa_deprn_book ON fa_deprn_detail(book_id);
CREATE INDEX IF NOT EXISTS idx_fa_trans_asset ON fa_transactions(asset_id);

-- HR 模块索引
CREATE INDEX IF NOT EXISTS idx_per_assign_person ON per_assignments_f(person_id);
CREATE INDEX IF NOT EXISTS idx_per_assign_org ON per_assignments_f(organization_id);
CREATE INDEX IF NOT EXISTS idx_per_pay_prop_assign ON per_pay_proposals_f(assignment_id);

-- PA 模块索引
CREATE INDEX IF NOT EXISTS idx_pa_project_mgr ON pa_projects_all(manager_id);
CREATE INDEX IF NOT EXISTS idx_pa_task_project ON pa_tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_pa_expend_project ON pa_expenditures_all(project_id);
CREATE INDEX IF NOT EXISTS idx_pa_expend_task ON pa_expenditures_all(task_id);

-- CST 模块索引
CREATE INDEX IF NOT EXISTS idx_cst_item_cost_item ON cst_item_costs(inventory_item_id);
CREATE INDEX IF NOT EXISTS idx_cst_item_cost_org ON cst_item_costs(organization_id);

-- BOM 模块索引
CREATE INDEX IF NOT EXISTS idx_bom_bom_assembly ON bom_bill_of_materials(assembly_item_id);
CREATE INDEX IF NOT EXISTS idx_bom_comp_bill ON bom_inventory_components(bill_sequence_id);
CREATE INDEX IF NOT EXISTS idx_bom_comp_item ON bom_inventory_components(component_item_id);

-- WIP 模块索引
CREATE INDEX IF NOT EXISTS idx_wip_job_assembly ON wip_discrete_jobs(assembly_item_id);
CREATE INDEX IF NOT EXISTS idx_wip_job_org ON wip_discrete_jobs(organization_id);
CREATE INDEX IF NOT EXISTS idx_wip_job_op_job ON wip_job_operations(job_id);
CREATE INDEX IF NOT EXISTS idx_wip_req_job ON wip_requirement_operations(job_id);
CREATE INDEX IF NOT EXISTS idx_wip_req_comp ON wip_requirement_operations(component_item_id);
CREATE INDEX IF NOT EXISTS idx_wip_trans_job ON wip_transactions(job_id);

-- 提交事务
COMMIT;

-- ============================================================
-- 脚本完成
-- ============================================================
-- 已创建表数：Batch 3 (40 张) + Batch 4 (44 张) = 84 张
-- 累计表数：93 + 84 = 177 张
-- ============================================================