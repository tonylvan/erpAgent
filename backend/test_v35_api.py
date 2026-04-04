# -*- coding: utf-8 -*-
import requests
import json

url = "http://localhost:8005/api/v1/smart-query-v35/query"
payload = {
    "query": "你好，请用中文回答：什么是 GSD 智能问数？",
    "user_id": "admin"
}

print("Testing v3.5 API with new DashScope API Key...")
print("=" * 60)

response = requests.post(url, json=payload, timeout=90)
result = response.json()

print(f"Success: {result.get('success')}")
print(f"Route: {result.get('route')}")
print(f"Data Type: {result.get('data_type')}")
print("\nAnswer:")
print("-" * 60)
print(result.get('answer'))
print("-" * 60)
