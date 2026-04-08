import requests
import json
import time

url = "http://localhost:8007/api/v1/smart-query-v2/query"

# 清除缓存 - 使用不同的查询
queries = [
    "分析本周销售趋势数据" + str(time.time()),
    "查询客户排行榜单" + str(time.time()),
    "显示库存预警信息" + str(time.time())
]

for query in queries:
    print(f"\n=== Testing: {query[:20]}... ===")
    data = {"query": query}
    
    try:
        response = requests.post(url, json=data, timeout=30)
        result = response.json()
        
        print(f"Success: {result.get('success')}")
        print(f"Data Type: {result.get('data_type')}")
        print(f"Has Data: {result.get('data') is not None}")
        print(f"Has Chart: {result.get('chart_config') is not None}")
        
        if result.get('data'):
            rows = result.get('data', {}).get('rows', [])
            print(f"Data rows: {len(rows)}")
        
        if result.get('chart_config'):
            chart = result.get('chart_config', {}).get('chart', {})
            print(f"Chart type: {chart.get('type')}")
            
    except Exception as e:
        print(f"Error: {e}")