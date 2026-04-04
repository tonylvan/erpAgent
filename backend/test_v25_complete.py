import requests

print("="*60)
print("测试 v2.5 API - 新代码验证")
print("="*60)

# 测试 1: 健康检查
r = requests.get('http://localhost:8005/health')
print(f"\n1. 健康检查：[OK]" if r.status_code == 200 else "[FAIL]")

# 测试 2: 销售趋势查询
r = requests.post('http://localhost:8005/api/v1/smart-query-v25/query', json={'query': '显示本周销售趋势'})
data = r.json()
print(f"2. 销售趋势查询：[OK] (Type: {data.get('data_type')})" if r.status_code == 200 else "[FAIL]")

# 测试 3: 客户排行查询
r = requests.post('http://localhost:8005/api/v1/smart-query-v25/query', json={'query': '查询 Top 10 客户'})
data = r.json()
print(f"3. 客户排行查询：[OK] (Type: {data.get('data_type')})" if r.status_code == 200 else "[FAIL]")

# 测试 4: 缓存统计
r = requests.get('http://localhost:8005/api/v1/smart-query-v25/cache-stats')
data = r.json()
print(f"4. 缓存统计 API: [OK]" if r.status_code == 200 else "[FAIL]")

# 测试 5: 推荐问题
r = requests.get('http://localhost:8005/api/v1/smart-query/suggested-questions')
data = r.json()
print(f"5. 推荐问题 API: [OK] ({len(data.get('questions', []))} 个问题)" if r.status_code == 200 else "[FAIL]")

print("\n" + "="*60)
print("v2.5 API 验证完成！")
print("="*60)
