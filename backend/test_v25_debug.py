import requests
import json

query = "显示本周销售趋势"
r = requests.post('http://localhost:8005/api/v1/smart-query-v25/query', json={'query': query})
print(f"Status: {r.status_code}")
print(f"Response: {json.dumps(r.json(), indent=2, ensure_ascii=False)}")
