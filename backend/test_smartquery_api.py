import requests
import json

url = 'http://localhost:8005/api/v1/smart-query-v40/query'
data = {
    'query': '查询本月销售趋势',
    'session_id': 'test'
}

response = requests.post(url, json=data)
print(f'Status: {response.status_code}')
print(f'Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}')
