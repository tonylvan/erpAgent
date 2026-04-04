import requests
import time

print("=" * 60)
print("GSD 后端 API 健康检查")
print("=" * 60)

base_url = "http://localhost:8005"

# 测试 1: 健康检查
print("\n[1/6] 健康检查...")
try:
    r = requests.get(f"{base_url}/health", timeout=5)
    print(f"  状态：{'✅' if r.status_code == 200 else '❌'} {r.status_code}")
except Exception as e:
    print(f"  状态：❌ {e}")

# 测试 2: 智能问数 v2.5
print("\n[2/6] 智能问数 v2.5...")
try:
    r = requests.post(f"{base_url}/api/v1/smart-query-v25/query", 
                      json={"query": "测试查询"}, timeout=10)
    print(f"  状态：{'✅' if r.status_code == 200 else '❌'} {r.status_code}")
    if r.ok:
        data = r.json()
        print(f"  响应：{data.get('success', False)}")
except Exception as e:
    print(f"  状态：❌ {e}")

# 测试 3: 推荐问题
print("\n[3/6] 推荐问题...")
try:
    r = requests.get(f"{base_url}/api/v1/smart-query-v25/suggested-questions", timeout=5)
    print(f"  状态：{'✅' if r.status_code == 200 else '❌'} {r.status_code}")
    if r.ok:
        data = r.json()
        print(f"  问题数：{len(data.get('questions', []))}")
except Exception as e:
    print(f"  状态：❌ {e}")

# 测试 4: 缓存统计
print("\n[4/6] 缓存统计...")
try:
    r = requests.get(f"{base_url}/api/v1/smart-query-v25/cache-stats", timeout=5)
    print(f"  状态：{'✅' if r.status_code == 200 else '❌'} {r.status_code}")
    if r.ok:
        data = r.json()
        print(f"  Redis 连接：{data.get('redis_connected', False)}")
        print(f"  缓存命中率：{data.get('hit_rate', '0%')}")
except Exception as e:
    print(f"  状态：❌ {e}")

# 测试 5: 员工查询
print("\n[5/6] 员工查询...")
try:
    r = requests.post(f"{base_url}/api/v1/smart-query-v25/query", 
                      json={"query": "ERP 员工数量"}, timeout=15)
    print(f"  状态：{'✅' if r.status_code == 200 else '❌'} {r.status_code}")
    if r.ok:
        data = r.json()
        print(f"  数据类型：{data.get('data_type', 'unknown')}")
except Exception as e:
    print(f"  状态：❌ {e}")

# 测试 6: 审计日志（需要认证）
print("\n[6/6] 审计日志（需要认证）...")
try:
    r = requests.get(f"{base_url}/api/v1/auth/audit-logs?limit=5", timeout=5)
    print(f"  状态：{'✅' if r.status_code in [200, 401] else '❌'} {r.status_code}")
    if r.status_code == 401:
        print(f"  说明：需要认证（正常）")
    elif r.status_code == 200:
        print(f"  记录数：{len(r.json())}")
except Exception as e:
    print(f"  状态：❌ {e}")

print("\n" + "=" * 60)
print("测试完成！")
print("=" * 60)
