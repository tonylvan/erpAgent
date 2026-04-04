"""
Neo4j 测试数据定时生成器
每 5 分钟自动生成今日数据并同步到 Neo4j
"""
import subprocess
import time
import schedule
from datetime import datetime

def generate_data():
    """生成测试数据"""
    print(f"\n{'='*60}")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] 开始生成测试数据...")
    print('='*60)
    
    try:
        result = subprocess.run(
            ['python', 'scripts/generate_test_data.py'],
            cwd=r'D:\erpAgent\backend',
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print(f"[OK] 数据生成成功")
            print(result.stdout)
        else:
            print(f"[ERROR] 数据生成失败")
            print(result.stderr)
            
    except subprocess.TimeoutExpired:
        print(f"[ERROR] 生成超时")
    except Exception as e:
        print(f"[ERROR] {e}")


# 定时任务
print("="*60)
print("Neo4j 测试数据定时生成器")
print("="*60)
print(f"启动时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("任务：每 5 分钟生成今日测试数据")
print("="*60)

# 立即执行一次
generate_data()

# 每 5 分钟执行
schedule.every(5).minutes.do(generate_data)

# 运行定时任务
while True:
    schedule.run_pending()
    time.sleep(1)
