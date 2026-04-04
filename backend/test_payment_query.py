import requests
import json

print("="*60)
print("GSD 智能问数测试 - 查最近一笔付款单")
print("="*60)

# 测试查询
query = "查最近一笔付款单"
print(f"\n查询：{query}")

r = requests.post('http://localhost:8005/api/v1/smart-query-v25/query', json={'query': query})
print(f"状态码：{r.status_code}")

if r.status_code == 200:
    data = r.json()
    print(f"返回类型：{data.get('data_type')}")
    print(f"成功：{data.get('success')}")
    print(f"有追问建议：{'follow_up' in data}")
    
    # 显示回答摘要
    answer = data.get('answer', '')
    print(f"\n回答摘要：[已获取]")
    
    # 显示数据
    if data.get('data'):
        print(f"\n数据内容：[已获取]")
        rows = data.get('data', {}).get('rows', [])
        print(f"付款单数量：{len(rows)}")
        if rows:
            print(f"最近一笔：{rows[0]}")
    
    print("\n[OK] 查询成功！")
else:
    print(f"[FAIL] 查询失败")

print("\n" + "="*60)
