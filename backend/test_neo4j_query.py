import requests
import json

print("=" * 60)
print("测试 Neo4j 真实数据查询")
print("=" * 60)

test_queries = [
    "显示本周销售趋势",
    "查询 Top 10 客户",
    "显示库存预警商品",
    "查看本周付款单",
    "统计各产品类别销售额",
]

for query in test_queries:
    print(f"\n测试：{query}")
    r = requests.post('http://localhost:8005/api/v1/smart-query-v25/query', json={'query': query})
    result = r.json()
    print(f"  返回类型：{result.get('data_type')}")
    print(f"  有追问建议：{'follow_up' in result}")
    if result.get('answer'):
        print(f"  回答摘要：{result.get('answer')[:80]}...")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)
