import requests

print("测试 v2.5 API...")
r = requests.post('http://localhost:8005/api/v1/smart-query-v25/query', json={'query': '显示本周销售趋势'})
print(f'Status: {r.status_code}')
data = r.json()
print(f'Type: {data.get("data_type")}')
print(f'Has follow_up: {"follow_up" in data}')
print(f'Success: {data.get("success")}')
