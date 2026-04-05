#!/usr/bin/env python
"""测试智能问数 v3.0 API"""
import requests
import json

base_url = 'http://localhost:8005'

test_queries = [
    "查询本月销售趋势",
    "显示 Top 10 客户排行",
    "华东区上月销售额统计",
    "库存预警商品有哪些",
]

print("=" * 60)
print("智能问数 v3.0 API 测试")
print("=" * 60)

for query in test_queries:
    print(f"\n查询：{query}")
    print("-" * 60)
    
    response = requests.post(
        f'{base_url}/api/v1/smart-query-v3/query',
        json={
            'query': query,
            'session_id': 'test-user-001',
            'limit': 10
        },
        headers={'Content-Type': 'application/json'}
    )
    
    print(f"状态码：{response.status_code}")
    
    if response.status_code == 200:
        data = response.json()
        print(f"✅ 成功")
        print(f"意图：{data.get('intent', {}).get('type', 'N/A')}")
        print(f"数据类型：{data.get('data_type', 'N/A')}")
        print(f"回答：{data.get('answer', 'N/A')[:200]}")
        print(f"追问建议：{data.get('suggested_questions', [])}")
    else:
        print(f"❌ 失败：{response.text}")

print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)
