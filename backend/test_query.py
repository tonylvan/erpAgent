import requests

# 测试查询
url = 'http://localhost:8005/api/v1/smart-query-v25/query'
query = '查询当前库存状态'

print(f"测试查询：{query}")
print("=" * 60)

try:
    response = requests.post(url, json={'query': query}, timeout=15)
    print(f"Status: {response.status_code}")
    
    if response.ok:
        data = response.json()
        print(f"Success: {data.get('success')}")
        print(f"Data Type: {data.get('data_type')}")
        answer = data.get('answer', '')
        print(f"Answer: {answer[:300]}")
    else:
        print(f"Error: {response.text[:500]}")
except Exception as e:
    print(f"Exception: {e}")

print("=" * 60)
