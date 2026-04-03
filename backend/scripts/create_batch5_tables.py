#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Oracle EBS ERP Batch 5 扩展表创建
目标：从 113 张表扩展到 150 张核心表
"""

import psycopg2
from datetime import datetime

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'erp',
    'user': 'postgres',
    'password': 'postgres'
}

def count_tables(conn):
    with conn.cursor() as cur:
        cur.execute("""
            SELECT COUNT(*) FROM information_schema.tables 
            WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        """)
        return cur.fetchone()[0]

def create_batch5_tables(conn):
    """创建 Batch 5 扩展表 (37 张)"""
    
    tables = [
        # ==================== XLA (子账会计) 模块 - 8 张 ====================
        """CREATE TABLE IF NOT EXISTS xla_events (
            event_id BIGSERIAL PRIMARY KEY,
            event_type_code VARCHAR(30) NOT NULL,
            event_date DATE NOT NULL,
            source_id BIGINT,
            source_type VARCHAR(30),
            status VARCHAR(20) DEFAULT 'VALID',
            creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        
        """CREATE TABLE IF NOT EXISTS xla_event_classes (
            class_id BIGSERIAL PRIMARY KEY,
            class_code VARCHAR(30) NOT NULL,
            class_name VARCHAR(100),
            description VARCHAR(240),
            status VARCHAR(20) DEFAULT 'ACTIVE'
        )""",
        
        """CREATE TABLE IF NOT EXISTS xla_accounting_entries (
            entry_id BIGSERIAL PRIMARY KEY,
            event_id BIGINT NOT NULL,
            accounting_date DATE,
            ledger_id BIGINT,
            currency_code VARCHAR(15),
            entered_dr NUMERIC(15,2),
            entered_cr NUMERIC(15,2),
            accounted_dr NUMERIC(15,2),
            accounted_cr NUMERIC(15,2),
            code_combination_id BIGINT,
            status VARCHAR(20) DEFAULT 'VALID'
        )""",
        
        """CREATE TABLE IF NOT EXISTS xla_distribution_sets (
            set_id BIGSERIAL PRIMARY KEY,
            set_name VARCHAR(100) NOT NULL,
            description VARCHAR(240),
            status VARCHAR(20) DEFAULT 'ACTIVE'
        )""",
        
        """CREATE TABLE IF NOT EXISTS xla_journal_lines (
            line_id BIGSERIAL PRIMARY KEY,
            entry_id BIGINT NOT NULL,
            line_number INT,
            account_type VARCHAR(10),
            debit_amount NUMERIC(15,2),
            credit_amount NUMERIC(15,2),
            description VARCHAR(240)
        )""",
        
        """CREATE TABLE IF NOT EXISTS xla_subledger_transactions (
            transaction_id BIGSERIAL PRIMARY KEY,
            transaction_number VARCHAR(50) NOT NULL,
            transaction_date DATE,
            source_application VARCHAR(30),
            entity_id BIGINT,
            status VARCHAR(20) DEFAULT 'VALID'
        )""",
        
        """CREATE TABLE IF NOT EXISTS xla_mapping_sets (
            mapping_set_id BIGSERIAL PRIMARY KEY,
            mapping_set_name VARCHAR(100) NOT NULL,
            description VARCHAR(240),
            status VARCHAR(20) DEFAULT 'ACTIVE'
        )""",
        
        """CREATE TABLE IF NOT EXISTS xla_period_statuses (
            period_status_id BIGSERIAL PRIMARY KEY,
            ledger_id BIGINT,
            period_name VARCHAR(30),
            period_year INT,
            period_num INT,
            status VARCHAR(20) DEFAULT 'OPEN'
        )""",
        
        # ==================== MTL (详细库存) 模块 - 10 张 ====================
        """CREATE TABLE IF NOT EXISTS mtl_categories_b (
            category_id BIGSERIAL PRIMARY KEY,
            category_set_id BIGINT,
            structure_id BIGINT,
            segment1 VARCHAR(30),
            segment2 VARCHAR(30),
            segment3 VARCHAR(30),
            summary_flag VARCHAR(1),
            enabled_flag VARCHAR(1) DEFAULT 'Y'
        )""",
        
        """CREATE TABLE IF NOT EXISTS mtl_category_sets (
            category_set_id BIGSERIAL PRIMARY KEY,
            category_set_name VARCHAR(30) NOT NULL,
            description VARCHAR(240),
            structure_id BIGINT,
            status VARCHAR(20) DEFAULT 'ACTIVE'
        )""",
        
        """CREATE TABLE IF NOT EXISTS mtl_item_sub_inventories (
            inv_item_sub_id BIGSERIAL PRIMARY KEY,
            inventory_item_id BIGINT NOT NULL,
            organization_id BIGINT NOT NULL,
            subinventory_code VARCHAR(10),
            status VARCHAR(20) DEFAULT 'ACTIVE'
        )""",
        
        """CREATE TABLE IF NOT EXISTS mtl_item_trx (
            transaction_id BIGSERIAL PRIMARY KEY,
            inventory_item_id BIGINT NOT NULL,
            organization_id BIGINT NOT NULL,
            transaction_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            transaction_type_id INT,
            quantity NUMERIC(15,2),
            primary_quantity NUMERIC(15,2)
        )""",
        
        """CREATE TABLE IF NOT EXISTS mtl_supply (
            supply_id BIGSERIAL PRIMARY KEY,
            supply_type_code VARCHAR(30),
            inventory_item_id BIGINT,
            organization_id BIGINT,
            quantity NUMERIC(15,2),
            quantity_received NUMERIC(15,2) DEFAULT 0
        )""",
        
        """CREATE TABLE IF NOT EXISTS mtl_demand (
            demand_id BIGSERIAL PRIMARY KEY,
            demand_type_code VARCHAR(30),
            inventory_item_id BIGINT,
            organization_id BIGINT,
            quantity NUMERIC(15,2),
            due_date DATE
        )""",
        
        """CREATE TABLE IF NOT EXISTS mtl_safe_stocks (
            safe_stock_id BIGSERIAL PRIMARY KEY,
            inventory_item_id BIGINT NOT NULL,
            organization_id BIGINT NOT NULL,
            subinventory_code VARCHAR(10),
            safety_stock_quantity NUMERIC(15,2),
            effective_date DATE
        )""",
        
        """CREATE TABLE IF NOT EXISTS mtl_cycle_counts (
            cycle_count_id BIGSERIAL PRIMARY KEY,
            organization_id BIGINT NOT NULL,
            cycle_count_name VARCHAR(80) NOT NULL,
            description VARCHAR(240),
            status VARCHAR(20) DEFAULT 'ACTIVE'
        )""",
        
        """CREATE TABLE IF NOT EXISTS mtl_adjustments (
            adjustment_id BIGSERIAL PRIMARY KEY,
            cycle_count_id BIGINT,
            inventory_item_id BIGINT,
            locator_id BIGINT,
            quantity_adjusted NUMERIC(15,2),
            adjustment_date DATE
        )""",
        
        """CREATE TABLE IF NOT EXISTS mtl_physical_inventory (
            physical_inv_id BIGSERIAL PRIMARY KEY,
            organization_id BIGINT NOT NULL,
            physical_inventory_name VARCHAR(80),
            status VARCHAR(20) DEFAULT 'PENDING',
            start_date DATE,
            end_date DATE
        )""",
        
        # ==================== ENG (工程) 模块 - 6 张 ====================
        """CREATE TABLE IF NOT EXISTS eng_engineering_changes (
            change_id BIGSERIAL PRIMARY KEY,
            change_number VARCHAR(50) NOT NULL,
            change_type VARCHAR(30),
            description VARCHAR(240),
            status VARCHAR(20) DEFAULT 'DRAFT',
            creation_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""",
        
        """CREATE TABLE IF NOT EXISTS eng_change_orders (
            order_id BIGSERIAL PRIMARY KEY,
            change_id BIGINT NOT NULL,
            order_number VARCHAR(50),
            priority VARCHAR(20),
            status VARCHAR(20) DEFAULT 'PENDING'
        )""",
        
        """CREATE TABLE IF NOT EXISTS eng_change_lines (
            line_id BIGSERIAL PRIMARY KEY,
            order_id BIGINT NOT NULL,
            inventory_item_id BIGINT,
            change_action VARCHAR(30),
            status VARCHAR(20)
        )""",
        
        """CREATE TABLE IF NOT EXISTS eng_item_revisions (
            revision_id BIGSERIAL PRIMARY KEY,
            inventory_item_id BIGINT NOT NULL,
            revision VARCHAR(10) NOT NULL,
            description VARCHAR(240),
            revision_date DATE,
            status VARCHAR(20) DEFAULT 'ACTIVE'
        )""",
        
        """CREATE TABLE IF NOT EXISTS eng_item_substitutes (
            substitute_id BIGSERIAL PRIMARY KEY,
            inventory_item_id BIGINT NOT NULL,
            substitute_item_id BIGINT NOT NULL,
            substitution_type VARCHAR(30),
            effective_date DATE
        )""",
        
        """CREATE TABLE IF NOT EXISTS eng_change_notifications (
            notification_id BIGSERIAL PRIMARY KEY,
            change_id BIGINT,
            recipient_id BIGINT,
            notification_type VARCHAR(30),
            status VARCHAR(20) DEFAULT 'UNREAD'
        )""",
        
        # ==================== FND (扩展基础数据) - 8 张 ====================
        """CREATE TABLE IF NOT EXISTS fnd_application (
            application_id BIGSERIAL PRIMARY KEY,
            application_name VARCHAR(100) NOT NULL,
            application_short_name VARCHAR(30),
            description VARCHAR(240),
            status VARCHAR(20) DEFAULT 'ACTIVE'
        )""",
        
        """CREATE TABLE IF NOT EXISTS fnd_responsibility_vl (
            responsibility_id BIGSERIAL PRIMARY KEY,
            responsibility_key VARCHAR(100) NOT NULL,
            responsibility_name VARCHAR(240),
            application_id BIGINT,
            status VARCHAR(20) DEFAULT 'ACTIVE'
        )""",
        
        """CREATE TABLE IF NOT EXISTS fnd_user_resp_groups (
            user_resp_id BIGSERIAL PRIMARY KEY,
            user_id BIGINT NOT NULL,
            responsibility_id BIGINT NOT NULL,
            start_date DATE,
            end_date DATE
        )""",
        
        """CREATE TABLE IF NOT EXISTS fnd_profile_options (
            profile_option_id BIGSERIAL PRIMARY KEY,
            profile_option_name VARCHAR(100) NOT NULL,
            profile_option_value TEXT,
            level_id INT,
            level_value BIGINT
        )""",
        
        """CREATE TABLE IF NOT EXISTS fnd_concurrent_programs (
            program_id BIGSERIAL PRIMARY KEY,
            program_name VARCHAR(100) NOT NULL,
            program_short_name VARCHAR(30),
            application_id BIGINT,
            status VARCHAR(20) DEFAULT 'ACTIVE'
        )""",
        
        """CREATE TABLE IF NOT EXISTS fnd_lookup_types (
            lookup_type_id BIGSERIAL PRIMARY KEY,
            lookup_type VARCHAR(30) NOT NULL,
            meaning VARCHAR(80),
            description VARCHAR(240)
        )""",
        
        """CREATE TABLE IF NOT EXISTS fnd_lookup_values (
            lookup_value_id BIGSERIAL PRIMARY KEY,
            lookup_type_id BIGINT,
            lookup_code VARCHAR(30) NOT NULL,
            meaning VARCHAR(80),
            description VARCHAR(240),
            tag VARCHAR(30)
        )""",
        
        """CREATE TABLE IF NOT EXISTS fnd_attachment_categories (
            category_id BIGSERIAL PRIMARY KEY,
            category_name VARCHAR(100) NOT NULL,
            description VARCHAR(240),
            status VARCHAR(20) DEFAULT 'ACTIVE'
        )""",
        
        # ==================== OKE (项目合同) 模块 - 5 张 ====================
        """CREATE TABLE IF NOT EXISTS oke_contract_headers (
            contract_id BIGSERIAL PRIMARY KEY,
            contract_number VARCHAR(50) NOT NULL,
            contract_type VARCHAR(30),
            customer_id BIGINT,
            project_id BIGINT,
            status VARCHAR(20) DEFAULT 'DRAFT',
            start_date DATE,
            end_date DATE
        )""",
        
        """CREATE TABLE IF NOT EXISTS oke_contract_lines (
            line_id BIGSERIAL PRIMARY KEY,
            contract_id BIGINT NOT NULL,
            line_number INT,
            inventory_item_id BIGINT,
            quantity NUMERIC(15,2),
            unit_price NUMERIC(15,2),
            amount NUMERIC(15,2)
        )""",
        
        """CREATE TABLE IF NOT EXISTS oke_contract_terms (
            term_id BIGSERIAL PRIMARY KEY,
            contract_id BIGINT,
            term_type VARCHAR(30),
            term_description TEXT,
            effective_date DATE
        )""",
        
        """CREATE TABLE IF NOT EXISTS oke_contract_deliverables (
            deliverable_id BIGSERIAL PRIMARY KEY,
            contract_id BIGINT,
            line_id BIGINT,
            deliverable_name VARCHAR(100),
            due_date DATE,
            status VARCHAR(20) DEFAULT 'PENDING'
        )""",
        
        """CREATE TABLE IF NOT EXISTS oke_contract_amendments (
            amendment_id BIGSERIAL PRIMARY KEY,
            contract_id BIGINT NOT NULL,
            amendment_number VARCHAR(50),
            amendment_date DATE,
            description VARCHAR(240)
        )""",
    ]
    
    print(f"\n[INFO] 创建 {len(tables)} 张 Batch 5 表...")
    
    with conn.cursor() as cur:
        for i, sql in enumerate(tables, 1):
            cur.execute(sql)
            if i % 10 == 0:
                print(f"  - 已创建 {i}/{len(tables)} 张表")
    conn.commit()
    print(f"[OK] Batch 5 表创建完成!")

def main():
    print("=" * 70)
    print("Oracle EBS ERP Batch 5 扩展表创建")
    print("=" * 70)
    
    print("\n正在连接数据库...")
    conn = psycopg2.connect(**DB_CONFIG)
    print("[OK] 数据库连接成功")
    
    current_count = count_tables(conn)
    print(f"[INFO] 当前表数量：{current_count}")
    
    # 创建 Batch 5 表
    create_batch5_tables(conn)
    
    new_count = count_tables(conn)
    print(f"\n[INFO] 表数量统计:")
    print(f"   创建前：{current_count} 张")
    print(f"   创建后：{new_count} 张")
    print(f"   新增：{new_count - current_count} 张")
    
    print("\n" + "=" * 70)
    print(f"[OK] Batch 5 完成！总计 {new_count} 张核心表")
    print("=" * 70)
    
    conn.close()
    print("\n数据库连接已关闭")

if __name__ == '__main__':
    main()
