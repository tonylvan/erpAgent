# -*- coding: utf-8 -*-
"""
Oracle EBS Table Import Script
Generates sample data and imports to PostgreSQL
"""

import psycopg2
import random
from datetime import datetime, timedelta

DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'erp',
    'user': 'postgres',
    'password': 'postgres'
}

def get_connection():
    return psycopg2.connect(**DB_CONFIG)

def create_tables():
    conn = get_connection()
    cur = conn.cursor()
    
    tables = """
    CREATE TABLE IF NOT EXISTS mtl_system_items_b (
        inventory_item_id NUMERIC PRIMARY KEY,
        organization_id NUMERIC,
        segment1 VARCHAR(40),
        description VARCHAR(240),
        inventory_item_status_code VARCHAR(10),
        primary_uom_code VARCHAR(10),
        creation_date TIMESTAMP,
        created_by NUMERIC
    );
    
    CREATE TABLE IF NOT EXISTS mtl_item_locations (
        inventory_location_id NUMERIC PRIMARY KEY,
        organization_id NUMERIC,
        subinventory_code VARCHAR(10),
        location_maximum_units NUMERIC,
        x_coordinate NUMERIC,
        y_coordinate NUMERIC,
        z_coordinate NUMERIC
    );
    
    CREATE TABLE IF NOT EXISTS mtl_material_transactions (
        transaction_id NUMERIC PRIMARY KEY,
        transaction_type_id NUMERIC,
        transaction_date TIMESTAMP,
        organization_id NUMERIC,
        inventory_item_id NUMERIC,
        transaction_quantity NUMERIC,
        primary_quantity NUMERIC,
        transaction_reference VARCHAR(240),
        distribution_account_id NUMERIC
    );
    
    CREATE TABLE IF NOT EXISTS so_headers_all (
        header_id NUMERIC PRIMARY KEY,
        order_number VARCHAR(50),
        order_type_id NUMERIC,
        customer_id NUMERIC,
        order_date DATE,
        flow_status_code VARCHAR(30),
        sales_rep_id NUMERIC,
        org_id NUMERIC,
        creation_date TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS so_lines_all (
        line_id NUMERIC PRIMARY KEY,
        header_id NUMERIC,
        line_number NUMERIC,
        inventory_item_id NUMERIC,
        ordered_quantity NUMERIC,
        unit_selling_price NUMERIC,
        flow_status_code VARCHAR(30),
        ship_from_org_id NUMERIC,
        creation_date TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS per_all_people_f (
        person_id NUMERIC PRIMARY KEY,
        employee_number VARCHAR(30),
        full_name VARCHAR(240),
        first_name VARCHAR(60),
        last_name VARCHAR(60),
        date_of_birth DATE,
        email_address VARCHAR(240),
        phone_number VARCHAR(30),
        hire_date DATE,
        termination_date DATE
    );
    
    CREATE TABLE IF NOT EXISTS fa_additions_b (
        asset_id NUMERIC PRIMARY KEY,
        asset_number VARCHAR(15),
        asset_type VARCHAR(15),
        asset_category_id NUMERIC,
        book_type_code VARCHAR(15),
        date_placed_in_service DATE,
        cost NUMERIC,
        depreciation_method VARCHAR(30),
        life_in_months NUMERIC,
        creation_date TIMESTAMP
    );
    
    CREATE TABLE IF NOT EXISTS ce_bank_accounts (
        bank_account_id NUMERIC PRIMARY KEY,
        bank_account_name VARCHAR(240),
        bank_account_num VARCHAR(50),
        bank_id NUMERIC,
        branch_id NUMERIC,
        currency_code VARCHAR(15),
        account_type VARCHAR(30),
        creation_date TIMESTAMP
    );
    """
    
    for statement in tables.split(';'):
        if statement.strip():
            try:
                cur.execute(statement)
            except Exception as e:
                print(f"Error: {e}")
    
    conn.commit()
    cur.close()
    conn.close()
    print("Tables created")

def generate_data():
    conn = get_connection()
    cur = conn.cursor()
    
    print("Generating inventory data...")
    for i in range(1, 101):
        cur.execute("""
            INSERT INTO mtl_system_items_b 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (i, random.choice([204, 207, 211]), f'ITEM-{i:05d}', f'Item {i}',
            random.choice(['Active', 'Inactive']), 'Ea',
            datetime.now() - timedelta(days=random.randint(0, 365)), random.randint(1, 10)))
    
    print("Generating sales orders...")
    for i in range(1, 51):
        cur.execute("""
            INSERT INTO so_headers_all 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (i, f'SO-{i:05d}', random.choice([1, 2, 3]), random.randint(1, 20),
            datetime.now() - timedelta(days=random.randint(0, 90)),
            random.choice(['BOOKED', 'SHIPPED']), random.randint(1, 10),
            random.choice([204, 207]), datetime.now()))
        
        for j in range(1, random.randint(2, 6)):
            cur.execute("""
                INSERT INTO so_lines_all 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, ((i-1)*5+j, i, j, random.randint(1, 100), random.randint(1, 100),
                round(random.uniform(10, 1000), 2), 'PENDING',
                random.choice([204, 207]), datetime.now()))
    
    print("Generating HR data...")
    for i in range(1, 101):
        cur.execute("""
            INSERT INTO per_all_people_f 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (i, f'EMP{i:04d}', f'Employee {i}', f'First{i}', f'Last{i}',
            datetime.now() - timedelta(days=random.randint(7300, 18250)),
            f'emp{i}@company.com', f'138{i:08d}',
            datetime.now() - timedelta(days=random.randint(30, 3650)), None))
    
    print("Generating fixed assets...")
    for i in range(1, 51):
        cur.execute("""
            INSERT INTO fa_additions_b 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (i, f'ASSET-{i:04d}', 'CAPITALIZED', random.randint(1, 20), 'CORP',
            datetime.now() - timedelta(days=random.randint(30, 1825)),
            round(random.uniform(1000, 100000), 2), 'STRAIGHT-LINE',
            random.choice([36, 60, 120]), datetime.now()))
    
    print("Generating bank accounts...")
    for i in range(1, 11):
        cur.execute("""
            INSERT INTO ce_bank_accounts 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (i, f'Bank {i}', f'6222{i:08d}', random.randint(1, 5),
            random.randint(1, 20), random.choice(['CNY', 'USD']), 'CHECKING', datetime.now()))
    
    conn.commit()
    cur.close()
    conn.close()
    print("Data generated")

if __name__ == '__main__':
    print("Starting Oracle EBS import...")
    create_tables()
    generate_data()
    print("Done!")
