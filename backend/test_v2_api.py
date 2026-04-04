import requests
import json

test_queries = [
    "显示本周销售趋势",
    "查询 Top 10 客户",
    "显示库存预警商品",
    "查看本周付款单",
    "统计各产品类别销售额"
]

for query in test_queries:
    print(f"\n测试：{query}")
    r = requests.post('http://localhost:8005/api/v1/smart-query-v2/query', json={'query': query})
    result = r.json()
    print(f"  返回类型：{result.get('data_type')}")
    print(f"  有 follow_up: {'follow_up' in result}")
    if result.get('data_type') == 'text':
        print(f"  回答前 50 字：{result.get('answer', '')[:50]}...")
