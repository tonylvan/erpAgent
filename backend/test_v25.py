import requests
import json

print("=" * 60)
print("测试 GSD 智能问数 v2.5 API")
print("=" * 60)

test_queries = [
    ("显示本周销售趋势", "chart"),
    ("查询 Top 10 客户", "table"),
    ("显示库存预警商品", "table"),
    ("查看本周付款单", "table"),
    ("统计各产品类别销售额", "stats"),
    ("今天天气怎么样", "text"),
]

passed = 0
failed = 0

for query, expected_type in test_queries:
    r = requests.post('http://localhost:8005/api/v1/smart-query-v25/query', json={'query': query})
    result = r.json()
    actual_type = result.get('data_type')
    
    if actual_type == expected_type:
        print(f"[OK] {query} -> {actual_type}")
        passed += 1
    else:
        print(f"[FAIL] {query} -> 期望:{expected_type}, 实际:{actual_type}")
        failed += 1

print("=" * 60)
print(f"结果：{passed} 通过，{failed} 失败")
print("=" * 60)
