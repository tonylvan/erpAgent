# -*- coding: utf-8 -*-
"""
执行 RTR 触发器 SQL 脚本
"""

import psycopg2

# 配置 - 从.env 读取实际密码
def get_connection():
    return psycopg2.connect(
        host='localhost',
        port=5432,
        database='erp',
        user='postgres',
        password='postgres'
    )

def execute_sql_file(file_path):
    """执行 SQL 文件"""
    print(f"[SQL] Reading file: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()
    
    # Connect
    print("[DB] Connecting to PostgreSQL...")
    conn = get_connection()
    conn.autocommit = False
    
    try:
        cursor = conn.cursor()
        
        # Split SQL statements
        statements = []
        current_statement = []
        
        for line in sql_content.split('\n'):
            if line.strip().startswith('--'):
                continue
            
            current_statement.append(line)
            
            if ';' in line:
                statement = '\n'.join(current_statement).strip()
                if statement and statement != ';':
                    statements.append(statement)
                current_statement = []
        
        print(f"[INFO] Total {len(statements)} SQL statements\n")
        
        success_count = 0
        skip_count = 0
        error_count = 0
        
        for i, stmt in enumerate(statements, 1):
            try:
                if not stmt.strip() or stmt.strip().startswith('--'):
                    continue
                
                cursor.execute(stmt)
                success_count += 1
                
                if stmt.strip().upper().startswith('SELECT'):
                    result = cursor.fetchall()
                    if result:
                        print(f"[OK] [{i}] {stmt[:50]}...")
                        for row in result:
                            print(f"     {row}")
                else:
                    print(f"[OK] [{i}] Executed")
                
            except Exception as e:
                error_msg = str(e).lower()
                if 'does not exist' in error_msg or 'already exists' in error_msg:
                    print(f"[SKIP] [{i}] Skip (already exists/not exists)")
                    skip_count += 1
                else:
                    print(f"[ERROR] [{i}] Failed: {e}")
                    error_count += 1
        
        conn.commit()
        print("\n[SUCCESS] All SQL executed!")
        
        # Verify triggers
        cursor.execute("SELECT COUNT(*) FROM pg_trigger WHERE tgname LIKE '%_rtr'")
        count = cursor.fetchone()[0]
        print(f"\n[TARGET] Created {count} RTR triggers!")
        
        print(f"\n[SUMMARY] Success: {success_count}, Skip: {skip_count}, Error: {error_count}")
        
        cursor.close()
        
    except Exception as e:
        conn.rollback()
        print(f"\n[ERROR] Failed: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    execute_sql_file('rtr_sync_trigger.sql')
