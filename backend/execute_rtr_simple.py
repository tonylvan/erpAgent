# -*- coding: utf-8 -*-
"""执行 RTR 简化版 SQL 脚本"""

import psycopg2

def get_connection():
    return psycopg2.connect(
        host='localhost',
        port=5432,
        database='erp',
        user='postgres',
        password='postgres'
    )

def execute_sql_file(file_path):
    print(f"[SQL] Reading: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    print("[DB] Connecting...")
    conn = get_connection()
    conn.autocommit = True
    
    try:
        cursor = conn.cursor()
        cursor.execute(sql_content)
        
        # 验证
        cursor.execute("SELECT COUNT(*) FROM pg_trigger WHERE tgname LIKE '%_rtr'")
        count = cursor.fetchone()[0]
        print(f"\n[SUCCESS] Created {count} RTR triggers!")
        
        # 显示触发器列表
        cursor.execute("""
            SELECT tgname, tgrelid::regclass 
            FROM pg_trigger 
            WHERE tgname LIKE '%_rtr'
            ORDER BY tgname
        """)
        triggers = cursor.fetchall()
        print("\nTriggers created:")
        for name, table in triggers:
            print(f"  - {name} on {table}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        raise

if __name__ == "__main__":
    execute_sql_file('rtr_sync_simple.sql')
