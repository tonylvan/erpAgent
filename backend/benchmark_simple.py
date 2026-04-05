# -*- coding: utf-8 -*-
"""
GSD 智能问数平台 - 性能基准测试（简化版）
"""

import time
import statistics
import json
import requests
from datetime import datetime

CONFIG = {
    'backend_url': 'http://localhost:8005/api'
}

results = {}

print("="*70)
print("GSD 智能问数平台 - 性能基准测试")
print(f"开始时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("="*70)

# 测试 1: API 健康检查
print("\n测试 1: API 健康检查")
try:
    start = time.time()
    response = requests.get(f"{CONFIG['backend_url']}/api/health", timeout=5)
    latency = (time.time() - start) * 1000
    
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] 状态：{data.get('status', 'unknown')}")
        print(f"[OK] 延迟：{latency:.2f}ms")
        results['api_health'] = {'status': 'ok', 'latency_ms': round(latency, 2)}
    else:
        print(f"[FAIL] 状态码：{response.status_code}")
        results['api_health'] = {'status': 'error', 'code': response.status_code}
except Exception as e:
    print(f"[FAIL] 错误：{e}")
    results['api_health'] = {'status': 'error', 'message': str(e)}

# 测试 2: API 响应时间
print("\n测试 2: API 响应时间测试 (30 次请求)")
latencies = []

for i in range(30):
    try:
        start = time.time()
        response = requests.get(f"{CONFIG['backend_url']}/api/graph/nodes?limit=10", timeout=10)
        latency = (time.time() - start) * 1000
        if response.status_code == 200:
            latencies.append(latency)
    except:
        pass

if latencies:
    p50 = statistics.median(latencies)
    p90 = sorted(latencies)[int(len(latencies) * 0.9)]
    p99 = sorted(latencies)[int(len(latencies) * 0.99)]
    avg = statistics.mean(latencies)
    
    print(f"平均：{avg:.2f}ms | P50: {p50:.2f}ms | P90: {p90:.2f}ms | P99: {p99:.2f}ms")
    results['api_response'] = {
        'avg_ms': round(avg, 2),
        'p50_ms': round(p50, 2),
        'p90_ms': round(p90, 2),
        'p99_ms': round(p99, 2),
        'samples': len(latencies)
    }

# 测试 3: 并发查询
print("\n测试 3: 并发查询能力测试")
from concurrent.futures import ThreadPoolExecutor, as_completed

def make_query():
    try:
        start = time.time()
        response = requests.post(
            f"{CONFIG['backend_url']}/api/v4/query",
            json={'question': '查询前 5 个供应商', 'limit': 5},
            timeout=10
        )
        latency = (time.time() - start)
        return response.status_code == 200, latency
    except:
        return False, 0

for concurrency in [1, 5, 10]:
    success_count = 0
    latencies = []
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(make_query) for _ in range(concurrency * 5)]
        for future in as_completed(futures):
            success, latency = future.result()
            if success:
                success_count += 1
                latencies.append(latency)
    
    total_time = time.time() - start_time
    qps = success_count / total_time
    avg_latency = statistics.mean(latencies) * 1000 if latencies else 0
    
    print(f"并发数={concurrency}: QPS={qps:.2f}, 平均延迟={avg_latency:.2f}ms, 成功={success_count}/{concurrency*5}")
    results[f'concurrent_{concurrency}'] = {
        'qps': round(qps, 2),
        'avg_latency_ms': round(avg_latency, 2),
        'success': f"{success_count}/{concurrency*5}"
    }

# 生成报告
print("\n" + "="*70)
print("生成测试报告...")

report_path = 'docs/performance-benchmark-report.md'
with open(report_path, 'w', encoding='utf-8') as f:
    f.write("# GSD 智能问数平台 - 性能基准测试报告\n\n")
    f.write(f"**测试时间**: {datetime.now().isoformat()}\n")
    f.write(f"**版本**: v3.5.0\n\n")
    
    f.write("## 测试结果总览\n\n")
    
    if 'api_health' in results:
        status = results['api_health']['status']
        f.write(f"### API 健康状态：{'OK' if status == 'ok' else 'FAIL'}\n\n")
    
    if 'api_response' in results:
        f.write("### API 响应时间\n\n")
        f.write("| 指标 | 数值 |\n")
        f.write("|------|------|\n")
        r = results['api_response']
        f.write(f"| 平均 | {r['avg_ms']}ms |\n")
        f.write(f"| P50 | {r['p50_ms']}ms |\n")
        f.write(f"| P90 | {r['p90_ms']}ms |\n")
        f.write(f"| P99 | {r['p99_ms']}ms |\n\n")
    
    f.write("### 并发查询能力\n\n")
    f.write("| 并发数 | QPS | 平均延迟 | 成功率 |\n")
    f.write("|--------|-----|---------|--------|\n")
    for key, value in results.items():
        if key.startswith('concurrent_'):
            num = key.split('_')[1]
            f.write(f"| {num} | {value['qps']} | {value['avg_latency_ms']}ms | {value['success']} |\n")
    
    f.write("\n---\n\n*报告由 benchmark_performance.py 自动生成*\n")

print(f"报告已保存：{report_path}")

# 保存 JSON
json_path = 'docs/performance-benchmark-results.json'
with open(json_path, 'w', encoding='utf-8') as f:
    json.dump({
        'timestamp': datetime.now().isoformat(),
        'version': 'v3.5.0',
        'results': results
    }, f, indent=2, ensure_ascii=False)

print(f"JSON 已保存：{json_path}")

print("\n" + "="*70)
print("性能基准测试完成！")
print("="*70)
