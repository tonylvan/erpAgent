# -*- coding: utf-8 -*-
import sys
import requests

# 设置控制台编码为 UTF-8
sys.stdout.reconfigure(encoding='utf-8')

url = "http://localhost:8005/api/v1/smart-query-v35/query"
payload = {
    "query": "你好，请用中文简单介绍 GSD 智能问数",
    "user_id": "admin"
}

print("🧪 Testing v3.5 API with new DashScope API Key...")
print("=" * 60)

try:
    response = requests.post(url, json=payload, timeout=90)
    result = response.json()
    
    print(f"✅ Status: {response.status_code}")
    print(f"✅ Success: {result.get('success')}")
    print(f"✅ Route: {result.get('route')}")
    print(f"✅ Data Type: {result.get('data_type')}")
    print("\n📝 Answer:")
    print("-" * 60)
    print(result.get('answer'))
    print("-" * 60)
    
except Exception as e:
    print(f"❌ Error: {e}")
