# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests

print("=" * 60)
print("🧪 Testing v4.0 API - Smart Router")
print("=" * 60)

# 健康检查
print("\n📊 Health Check:")
r = requests.get("http://localhost:8005/api/v1/smart-query-v40/health", timeout=10)
health = r.json()
print(f"  Status: {health.get('status')}")
print(f"  Version: {health.get('version')}")
print(f"  DashScope: {health.get('dashscope_available')}")
print(f"  ERP Keywords: {health.get('erp_keywords_count')}")

# 测试 ERP 查询
print("\n📈 ERP Query Test:")
r = requests.post("http://localhost:8005/api/v1/smart-query-v40/query", json={
    "query": "查询本周的采购订单",
    "user_id": "admin"
}, timeout=30)
result = r.json()
print(f"  Success: {result.get('success')}")
print(f"  Route: {result.get('route')}")
print(f"  Answer: {result.get('answer')[:100]}...")

# 测试通用问题
print("\n💬 General Query Test:")
r = requests.post("http://localhost:8005/api/v1/smart-query-v40/query", json={
    "query": "今天天气怎么样",
    "user_id": "admin"
}, timeout=30)
result = r.json()
print(f"  Success: {result.get('success')}")
print(f"  Route: {result.get('route')}")
print(f"  Answer: {result.get('answer')[:100]}...")

print("\n" + "=" * 60)
print("✅ v4.0 API Test Complete!")
print("=" * 60)
