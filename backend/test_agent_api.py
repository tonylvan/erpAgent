# -*- coding: utf-8 -*-
import requests
import json

url = 'http://localhost:8007/api/v1/smart-query-agent/query'
data = {
    'query': '本周销售趋势',
    'session_id': 'test-python-001'
}

print(f"Sending query: {data['query']}")
response = requests.post(url, json=data)
result = response.json()

print(f"\n✅ Success: {result['success']}")
print(f"DataType: {result['data_type']}")
if result['data'] and isinstance(result['data'], dict) and 'message' not in result['data']:
    print(f"✅ 真实数据！Count: {len(result['data']) if isinstance(result['data'], list) else 'N/A'}")
    if result['data']:
        print(f"Data: {json.dumps(result['data'], ensure_ascii=False, indent=2)}")
else:
    print(f"Data: {result['data']}")
print(f"\nAnswer: {result['answer']}")
