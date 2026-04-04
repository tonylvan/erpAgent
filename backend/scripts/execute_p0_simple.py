#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
执行 P0 功能数据库表创建脚本 - 简化版
"""

import psycopg2
import sys

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'erp',
    'user': 'postgres',
    'password': 'postgres'
}

def main():
    """主函数"""
    sql_file = r'D:\erpAgent\backend\scripts\create_p0_tables.sql'
    
    print(f"Reading SQL file: {sql_file}")
    
    with open(sql_file, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    print(f"SQL file size: {len(sql_content)} bytes")
    print(f"\nConnecting to database...")
    
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    cursor = conn.cursor()
    
    try:
        # 直接执行整个 SQL
        cursor.execute(sql_content)
        conn.commit()
        print("SQL executed successfully!")
        
        # 验证
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND (table_name LIKE 'sys_%' OR table_name LIKE 'query_%' 
            OR table_name LIKE 'saved_%' OR table_name LIKE 'cache_%')
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        print(f"\nCreated {len(tables)} tables:")
        for table in tables:
            print(f"  - {table[0]}")
        
        cursor.close()
        conn.close()
        
        print("\n✅ P0 database tables created successfully!")
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"\nError: {e}")
        cursor.close()
        conn.close()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
