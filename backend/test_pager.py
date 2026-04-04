"""
测试分页功能
"""
import requests
import json

# 测试大数据集查询
url = 'http://localhost:8005/api/v1/smart-query-v25/query'

print("=" * 60)
print("测试分页功能 - 后端 API")
print("=" * 60)

# 测试查询
queries = [
    "查询所有客户",
    "查询所有产品",
    "统计概览"
]

for q in queries:
    print(f"\nQuery: {q}")
    try:
        response = requests.post(url, json={'query': q}, timeout=10)
        data = response.json()
        
        if data.get('success'):
            data_obj = data.get('data')
            if data_obj and isinstance(data_obj, dict):
                records = data_obj.get('rows', [])
                if records:
                    print(f"  [OK] Returned {len(records)} records")
                    print(f"  First 3: {json.dumps(records[:3], ensure_ascii=False, indent=2)[:500]}")
                else:
                    print(f"  [WARN] No table data (text response)")
            else:
                print(f"  [WARN] No data object")
        else:
            print(f"  [FAIL] {str(data.get('answer', 'Unknown error'))[:100]}")
    except Exception as e:
        print(f"  [ERROR] {e}")

print("\n" + "=" * 60)
print("前端分页已集成 vue-pager 组件")
print("访问：http://localhost:5176 查看效果")
print("=" * 60)
