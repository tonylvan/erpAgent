import requests
import json

url = "http://localhost:8007/api/v1/smart-query-v2/query"
data = {"query": "本周销售趋势"}

response = requests.post(url, json=data)
result = response.json()

print("=== Response ===")
print(f"Success: {result.get('success')}")
print(f"Data Type: {result.get('data_type')}")
print(f"Data: {result.get('data')}")
print(f"Chart Config: {result.get('chart_config')}")
print(f"Answer: {result.get('answer')[:200] if result.get('answer') else 'None'}...")
print(f"Follow up: {result.get('follow_up')}")