import requests
import time

# 测试查询
url = 'http://localhost:8005/api/v1/smart-query-v25/query'
query = 'ERP 员工数量'

print(f"测试查询：{query}")
print("=" * 60)

start = time.time()

try:
    response = requests.post(url, json={'query': query}, timeout=30)
    elapsed = (time.time() - start) * 1000
    
    print(f"Status: {response.status_code}")
    print(f"响应时间：{elapsed:.0f}ms")
    print("=" * 60)
    
    if response.ok:
        data = response.json()
        print(f"Success: {data.get('success')}")
        print(f"Data Type: {data.get('data_type')}")
        answer = data.get('answer', '')
        print(f"\n回答:\n{answer}")
        
        # 显示表格数据（如果有）
        if data.get('data'):
            print(f"\n表格数据:")
            print(data.get('data'))
            
        # 显示追问建议
        if data.get('follow_up'):
            print(f"\n追问建议：{data.get('follow_up')}")
    else:
        print(f"Error: {response.text[:500]}")
except Exception as e:
    print(f"Exception: {e}")

print("=" * 60)
