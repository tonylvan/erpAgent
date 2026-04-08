import requests
import json
import sys

# Test the smart query API
url = "http://localhost:8007/api/v1/smart-query-v2/query"

queries = [
    "本周销售趋势",
    "客户排行",
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
            print(f"Data rows: {len(result.get('data', {}).get('rows', []))}")
        
        if result.get('chart_config'):
            print(f"Chart type: {result.get('chart_config', {}).get('chart', {}).get('type')}")
            
    except Exception as e:
        print(f"Error: {e}")