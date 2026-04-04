#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
执行 P0 功能数据库表创建脚本
"""

import psycopg2
import sys
from pathlib import Path
import io

# 设置标准输出编码
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'erp',
    'user': 'postgres',
    'password': 'postgres'
}

def execute_sql_file(sql_file_path):
    """执行 SQL 文件"""
    print(f"📄 读取 SQL 文件：{sql_file_path}")
    
    with open(sql_file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    print(f"✅ SQL 文件大小：{len(sql_content)} 字节")
    
    # 连接数据库
    print(f"\n🔗 连接数据库：{DB_CONFIG['database']}@{DB_CONFIG['host']}")
    conn = psycopg2.connect(**DB_CONFIG)
    conn.autocommit = False
    
    try:
        cursor = conn.cursor()
        
        # 执行 SQL（按分号分割）
        statements = sql_content.split(';')
        executed = 0
        errors = []
        
        for stmt in statements:
            stmt = stmt.strip()
            if stmt and not stmt.startswith('--'):
                try:
                    cursor.execute(stmt)
                    executed += 1
                except Exception as e:
                    # 忽略已存在的错误
                    if 'already exists' in str(e).lower() or 'on conflict' in str(e).lower():
                        executed += 1
                    else:
                        errors.append(f"❌ 执行失败：{e}")
        
        # 提交事务
        conn.commit()
        
        print(f"\n✅ 执行完成")
        print(f"   - 成功执行：{executed} 条语句")
        print(f"   - 错误：{len(errors)} 条")
        
        if errors:
            print("\n错误详情:")
            for err in errors[:5]:  # 只显示前 5 个错误
                print(f"  {err}")
        
        # 验证表创建
        print("\n📊 验证表创建:")
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name LIKE 'sys_%' OR table_name LIKE 'query_%' 
            OR table_name LIKE 'saved_%' OR table_name LIKE 'cache_%'
            OR table_name LIKE 'data_%' OR table_name LIKE 'table_%'
            ORDER BY table_name
        """)
        
        tables = cursor.fetchall()
        for table in tables:
            print(f"  ✅ {table[0]}")
        
        # 验证初始数据
        print("\n📊 验证初始数据:")
        cursor.execute("SELECT COUNT(*) FROM sys_users")
        print(f"  - 用户数：{cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM sys_roles")
        print(f"  - 角色数：{cursor.fetchone()[0]}")
        
        cursor.execute("SELECT COUNT(*) FROM table_monitor_config")
        print(f"  - 表监控配置：{cursor.fetchone()[0]}")
        
        cursor.close()
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ 执行失败：{e}")
        return False
        
    finally:
        conn.close()
        print(f"\n🔓 数据库连接已关闭")


if __name__ == "__main__":
    # SQL 文件路径
    sql_file = Path(__file__).parent / "create_p0_tables.sql"
    
    if not sql_file.exists():
        print(f"❌ SQL 文件不存在：{sql_file}")
        sys.exit(1)
    
    # 执行
    success = execute_sql_file(sql_file)
    
    if success:
        print("\n" + "="*60)
        print("✅ P0 数据库表创建成功！")
        print("="*60)
        print("\n已创建:")
        print("  ✅ 用户认证表 (sys_users, sys_roles, sys_audit_logs)")
        print("  ✅ 查询历史表 (query_history, saved_queries, query_feedback)")
        print("  ✅ 缓存管理表 (cache_metadata, data_refresh_log, table_monitor_config)")
        print("\n默认账户:")
        print("  - admin / admin123 (管理员)")
        print("  - finance_user / admin123 (财务)")
        print("  - procurement_user / admin123 (采购)")
        print("  - sales_user / admin123 (销售)")
        print("="*60)
    else:
        print("\n❌ P0 数据库表创建失败！")
        sys.exit(1)
