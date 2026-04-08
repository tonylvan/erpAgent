import requests
import json

url = "http://localhost:8007/api/v1/smart-query-v2/query"

queries = [
    "客户回款排行 Top10",
    "客户排行榜 Top10"
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
        
        if result.get('data'):
            rows = result.get('data', {}).get('rows', [])
            print(f"Data rows: {len(rows)}")
            for r in rows[:3]:
                print(f"  {r}")
            
    except Exception as e:
        print(f"Error: {e}")