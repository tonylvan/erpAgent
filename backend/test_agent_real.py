# -*- coding: utf-8 -*-
import requests
import json

url = 'http://localhost:8007/api/v1/smart-query-agent/query'

# 测试 1：销售趋势查询
print("=" * 60)
print("测试 1：销售趋势查询")
print("=" * 60)
data = {'query': '本周销售趋势', 'session_id': 'test-001'}
response = requests.post(url, json=data, timeout=30)
result = response.json()
print(f"✅ Success: {result['success']}")
print(f"DataType: {result['data_type']}")
if result['data'] and isinstance(result['data'], list) and len(result['data']) > 0:
    print(f"✅ 真实 Neo4j 数据！Count: {len(result['data'])}")
    print(f"Data preview: {json.dumps(result['data'][:2], ensure_ascii=False, indent=2)}")
else:
    print(f"Data: {result['data']}")
print(f"\nAnswer: {result['answer'][:200]}...")
print(f"\nReasoning: {result.get('reasoning_process', [])[:2]}")

# 测试 2：追问（多轮对话）
print("\n" + "=" * 60)
print("测试 2：多轮对话追问")
print("=" * 60)
data2 = {'query': '对比上月数据', 'session_id': 'test-001'}
response2 = requests.post(url, json=data2, timeout=30)
result2 = response2.json()
print(f"✅ Success: {result2['success']}")
print(f"Answer: {result2['answer'][:200]}...")

print("\n" + "=" * 60)
print("✅ 测试完成！")
print("=" * 60)
