#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Oracle EBS ERP 扩展表创建脚本
创建 Batch 1-2: 60 张扩展表
"""

import psycopg2
from psycopg2 import sql
import os
import sys

# 设置控制台编码为 UTF-8
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 数据库连接配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'erp',
    'user': 'postgres',
    'password': 'postgres'
}

def read_sql_file(file_path):
    """读取 SQL 文件"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def execute_sql_script(conn, sql_script):
    """执行 SQL 脚本"""
    try:
        with conn.cursor() as cur:
            cur.execute(sql_script)
        conn.commit()
        return True, "成功"
    except Exception as e:
        conn.rollback()
        return False, str(e)

def count_tables(conn):
    """统计当前表数量"""
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                  AND table_type = 'BASE TABLE'
            """)
            return cur.fetchone()[0]
    except Exception as e:
        return f"错误：{e}"

def main():
    print("=" * 70)
    print("Oracle EBS ERP 扩展表创建脚本")
    print("=" * 70)
    
    # 连接数据库
    print("\n正在连接数据库...")
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        print(f"[OK] 数据库连接成功：{DB_CONFIG['host']}:{DB_CONFIG['port']}/{DB_CONFIG['database']}")
    except Exception as e:
        print(f"[ERROR] 数据库连接失败：{e}")
        return
    
    # 统计当前表数
    current_count = count_tables(conn)
    print(f"[INFO] 当前表数量：{current_count}")
    
    # 读取 SQL 文件
    sql_file = os.path.join(os.path.dirname(__file__), 'create_extended_tables.sql')
    print(f"\n正在读取 SQL 文件：{sql_file}")
    
    try:
        sql_script = read_sql_file(sql_file)
        print(f"[OK] SQL 文件读取成功 (文件大小：{len(sql_script):,} 字节)")
    except Exception as e:
        print(f"[ERROR] 读取 SQL 文件失败：{e}")
        conn.close()
        return
    
    # 执行 SQL 脚本
    print("\n正在执行 SQL 脚本...")
    print("[INFO] 这可能需要几分钟时间，请稍候...")
    
    success, message = execute_sql_script(conn, sql_script)
    
    if success:
        print(f"\n[OK] SQL 脚本执行成功!")
        
        # 统计新表数
        new_count = count_tables(conn)
        print(f"\n[INFO] 表数量统计:")
        print(f"   创建前：{current_count} 张")
        print(f"   创建后：{new_count} 张")
        print(f"   新增：{new_count - current_count} 张")
        
        # 列出新创建的表
        print(f"\n[INFO] 新创建的表列表:")
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                  AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """)
            tables = cur.fetchall()
            for table in tables:
                print(f"   - {table[0]}")
        
        print("\n" + "=" * 70)
        print("[OK] 扩展表创建完成!")
        print("=" * 70)
        
    else:
        print(f"\n[ERROR] SQL 脚本执行失败:")
        print(f"   错误信息：{message}")
        
        print("\n" + "=" * 70)
        print("[WARN] 请检查错误信息并修复后重试")
        print("=" * 70)
    
    # 关闭连接
    conn.close()
    print(f"\n数据库连接已关闭")

if __name__ == '__main__':
    main()
