import requests
import json

url = "http://localhost:8007/api/v1/smart-query-v2/query"

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
        print(f"Has Chart: {result.get('chart_config') is not None}")
        print(f"Has Data: {result.get('data') is not None}")
        
        if result.get('chart_config'):
            chart = result.get('chart_config', {})
            print(f"Chart type: {chart.get('chart', {}).get('type')}")
            if chart.get('xAxis'):
                print(f"X-Axis data: {chart.get('xAxis', {}).get('data', [])[:5]}")
            if chart.get('series'):
                print(f"Series count: {len(chart.get('series', []))}")
        
        if result.get('data'):
            rows = result.get('data', {}).get('rows', [])
            print(f"Data rows: {len(rows)}")
            
    except Exception as e:
        print(f"Error: {e}")