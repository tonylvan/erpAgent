import requests

print("测试 Neo4j 真实数据查询")
print("=" * 60)

queries = [
    ("显示本周销售趋势", "chart"),
    ("查询 Top 10 客户", "table"),
    ("显示库存预警商品", "table"),
]

for query, expected in queries:
    r = requests.post('http://localhost:8005/api/v1/smart-query-v25/query', json={'query': query})
    result = r.json()
    actual = result.get('data_type')
    status = "[OK]" if actual == expected else "[FAIL]"
    print(f"{status} {query} -> {actual}")

print("=" * 60)
print("Neo4j 真实数据查询测试完成！")
