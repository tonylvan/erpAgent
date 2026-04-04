import requests
import time
import json

print("="*60)
print("GSD 智能问数 - Redis 缓存测试")
print("="*60)

# 测试查询
query = "查最近一笔付款单"
print(f"\n查询：{query}")

# 第一次查询（未缓存）
print("\n[1/3] 第一次查询（未缓存）...")
start = time.time()
r1 = requests.post('http://localhost:8005/api/v1/smart-query-v25/query', json={'query': query})
t1 = (time.time() - start) * 1000
print(f"  响应时间：{t1:.0f}ms")
print(f"  状态码：{r1.status_code}")

if r1.status_code == 200:
    data = r1.json()
    print(f"  返回类型：{data.get('data_type')}")
    print(f"  成功：{data.get('success')}")
    
    # 显示付款单数据
    if data.get('data'):
        rows = data.get('data', {}).get('rows', [])
        print(f"  付款单数量：{len(rows)}")
        if rows:
            print(f"  最近一笔：[已获取]")

# 第二次查询（缓存命中）
print("\n[2/3] 第二次查询（缓存命中）...")
start = time.time()
r2 = requests.post('http://localhost:8005/api/v1/smart-query-v25/query', json={'query': query})
t2 = (time.time() - start) * 1000
print(f"  响应时间：{t2:.0f}ms")

# 第三次查询（缓存命中）
print("\n[3/3] 第三次查询（缓存命中）...")
start = time.time()
r3 = requests.post('http://localhost:8005/api/v1/smart-query-v25/query', json={'query': query})
t3 = (time.time() - start) * 1000
print(f"  响应时间：{t3:.0f}ms")

# 计算性能提升
avg_cached = (t2 + t3) / 2
improvement = ((t1 - avg_cached) / max(t1, 0.001)) * 100

print("\n" + "="*60)
print("性能对比:")
print(f"  未缓存平均：{t1:.0f}ms")
print(f"  缓存命中平均：{avg_cached:.0f}ms")
print(f"  性能提升：{improvement:.1f}%")
print("="*60)

# 检查 Redis 缓存
print("\n检查 Redis 缓存:")
import subprocess
result = subprocess.run(['C:\\Program Files\\Redis\\redis-cli.exe', 'KEYS', 'gsd:*'], 
                       capture_output=True, text=True)
if result.stdout.strip():
    keys = result.stdout.strip().split('\r\n')
    print(f"  缓存 Key 数量：{len(keys)}")
    for key in keys[:3]:
        print(f"    - {key}")
else:
    print("  未找到缓存 Key")

print("\n[OK] 测试完成！")
