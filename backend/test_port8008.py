import requests
import json

# 使用新端口
url = "http://localhost:8008/api/v1/smart-query-v2/query"

queries = [
    "本周销售趋势",
    "客户排行榜",
    "库存预警"
]

for query in queries:
    print(f"\n=== Testing: {query} ===")
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
            if rows:
                print(f"First row: {rows[0]}")
        
        if result.get('chart_config'):
            chart = result.get('chart_config', {}).get('chart', {})
            print(f"Chart type: {chart.get('type')}")
            print(f"Chart data: {result.get('chart_config', {}).get('series', [])[:1]}")
            
    except Exception as e:
        print(f"Error: {e}")