"""
Query PostgreSQL to verify sales data
"""
import os
import sys
import psycopg2
from datetime import datetime

# Add project path
sys.path.insert(0, 'D:\\erpAgent\\backend')

# Load environment variables
from dotenv import load_dotenv
load_dotenv('D:\\erpAgent\\backend\\.env')

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://postgres:Tony1985@localhost:5432/erpagent')

print("=" * 60)
print("PostgreSQL 销售数据验证")
print("=" * 60)
print()

try:
    # Connect to PostgreSQL
    print("连接 PostgreSQL...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    print("✅ 连接成功")
    print()
    
    # Query 1: Total sales count
    print("1. 销售记录统计：")
    cur.execute("SELECT COUNT(*) FROM sales")
    sale_count = cur.fetchone()[0]
    print(f"   总销售记录: {sale_count}")
    print()
    
    # Query 2: Total sales amount
    print("2. 销售金额统计：")
    cur.execute("""
        SELECT 
            COUNT(*) as count,
            SUM(total_amount) as total,
            AVG(total_amount) as avg,
            MAX(total_amount) as max,
            MIN(total_amount) as min
        FROM sales
        WHERE total_amount IS NOT NULL
    """)
    result = cur.fetchone()
    print(f"   记录数: {result[0]}")
    print(f"   总金额: ¥{result[1]:,.2f}" if result[1] else "   总金额: N/A")
    print(f"   平均金额: ¥{result[2]:,.2f}" if result[2] else "   平均金额: N/A")
    print(f"   最大金额: ¥{result[3]:,.2f}" if result[3] else "   最大金额: N/A")
    print(f"   最小金额: ¥{result[4]:,.2f}" if result[4] else "   最小金额: N/A")
    print()
    
    # Query 3: Top 5 sales
    print("3. Top 5 销售记录：")
    cur.execute("""
        SELECT id, customer_id, total_amount, sale_date
        FROM sales
        ORDER BY total_amount DESC
        LIMIT 5
    """)
    rows = cur.fetchall()
    for i, row in enumerate(rows, 1):
        print(f"   {i}. ID:{row[0]}, 客户:{row[1]}, 金额:¥{row[2]:,.2f}, 日期:{row[3]}")
    print()
    
    # Query 4: Check other tables
    print("4. 相关表统计：")
    tables = ['customers', 'products', 'orders']
    for table in tables:
        try:
            cur.execute(f"SELECT COUNT(*) FROM {table}")
            count = cur.fetchone()[0]
            print(f"   {table}: {count} 条记录")
        except:
            print(f"   {table}: 表不存在")
    print()
    
    # Close connection
    cur.close()
    conn.close()
    
    print("✅ PostgreSQL 验证完成")
    
except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()