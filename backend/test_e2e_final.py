import requests
import time
import json

print("="*70)
print("GSD 智能问数 - 端到端测试")
print("="*70)

# 测试用例
test_cases = [
    {"query": "查最近一笔付款单", "expected_type": "table"},
    {"query": "显示本周销售趋势", "expected_type": "chart"},
    {"query": "查询 Top 10 客户", "expected_type": "table"},
    {"query": "显示库存预警商品", "expected_type": "table"},
    {"query": "统计各产品销售额", "expected_type": "stats"},
]

total_passed = 0
total_failed = 0

for i, case in enumerate(test_cases, 1):
    print(f"\n[测试 {i}/{len(test_cases)}] {case['query']}")
    print("-"*70)
    
    try:
        # 第一次查询（未缓存）
        start = time.time()
        r1 = requests.post('http://localhost:8005/api/v1/smart-query-v25/query', 
                          json={'query': case['query']}, timeout=30)
        t1 = (time.time() - start) * 1000
        
        if r1.status_code != 200:
            print(f"  [FAIL] HTTP 错误：{r1.status_code}")
            total_failed += 1
            continue
        
        data = r1.json()
        
        # 验证返回类型
        if data.get('data_type') != case['expected_type']:
            print(f"  [FAIL] 类型不匹配：期望 {case['expected_type']}, 实际 {data.get('data_type')}")
            total_failed += 1
            continue
        
        # 验证成功标志
        if not data.get('success'):
            print(f"  [FAIL] 查询失败")
            total_failed += 1
            continue
        
        # 验证有数据返回
        if case['expected_type'] == 'table' and data.get('data'):
            rows = data.get('data', {}).get('rows', [])
            if not rows:
                print(f"  [FAIL] 没有返回数据")
                total_failed += 1
                continue
            print(f"  [OK] 返回 {len(rows)} 条记录")
        
        # 验证有追问建议
        if not data.get('follow_up'):
            print(f"  [WARN] 没有追问建议")
        
        print(f"  [OK] 类型：{data.get('data_type')}")
        print(f"  [OK] 响应时间：{t1:.0f}ms")
        print(f"  [OK] 有追问建议：{len(data.get('follow_up', []))} 个")
        
        total_passed += 1
        
    except Exception as e:
        print(f"  [FAIL] 异常：{e}")
        total_failed += 1

# 汇总结果
print("\n" + "="*70)
print("测试结果汇总")
print("="*70)
print(f"通过：{total_passed}/{len(test_cases)}")
print(f"失败：{total_failed}/{len(test_cases)}")
print(f"通过率：{(total_passed/len(test_cases))*100:.1f}%")
print("="*70)

# 检查 Redis 缓存
print("\n检查 Redis 缓存:")
import subprocess
result = subprocess.run(['C:\\Program Files\\Redis\\redis-cli.exe', 'KEYS', 'gsd:*'], 
                       capture_output=True, text=True)
if result.stdout.strip():
    keys = result.stdout.strip().split('\r\n')
    print(f"  [OK] 缓存 Key 数量：{len(keys)}")
    for key in keys[:5]:
        print(f"    - {key}")
else:
    print(f"  [WARN] 未找到缓存 Key")

# 测试缓存命中
if total_passed > 0:
    print("\n测试缓存命中:")
    query = test_cases[0]['query']
    
    # 第一次
    start = time.time()
    requests.post('http://localhost:8005/api/v1/smart-query-v25/query', json={'query': query})
    t1 = (time.time() - start) * 1000
    
    # 第二次（应命中缓存）
    start = time.time()
    requests.post('http://localhost:8005/api/v1/smart-query-v25/query', json={'query': query})
    t2 = (time.time() - start) * 1000
    
    # 第三次（应命中缓存）
    start = time.time()
    requests.post('http://localhost:8005/api/v1/smart-query-v25/query', json={'query': query})
    t3 = (time.time() - start) * 1000
    
    avg_cached = (t2 + t3) / 2
    improvement = ((t1 - avg_cached) / max(t1, 0.001)) * 100
    
    print(f"  未缓存：{t1:.0f}ms")
    print(f"  缓存命中：{avg_cached:.0f}ms")
    print(f"  性能提升：{improvement:.1f}%")

print("\n[OK] 测试完成！")

if total_passed == len(test_cases):
    print("\n[SUCCESS] 所有测试通过！")
else:
    print(f"\n[WARNING] {total_failed} 个测试失败")
