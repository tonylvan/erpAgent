import requests

print("="*70)
print("API CORS 测试")
print("="*70)

API_BASE = "http://localhost:8005"

# 测试 1: 健康检查
print("\n[1] 健康检查...")
try:
    r = requests.get(f"{API_BASE}/health", timeout=5)
    print(f"    状态：{r.status_code}")
    print(f"    响应：{r.json()}")
except Exception as e:
    print(f"    失败：{e}")

# 测试 2: CORS 预检
print("\n[2] CORS 预检请求...")
try:
    r = requests.options(
        f"{API_BASE}/api/v1/smart-query-v40/query",
        headers={
            'Origin': 'http://localhost:5176',
            'Access-Control-Request-Method': 'POST'
        },
        timeout=5
    )
    print(f"    状态：{r.status_code}")
    print(f"    Access-Control-Allow-Origin: {r.headers.get('Access-Control-Allow-Origin', 'NOT SET')}")
except Exception as e:
    print(f"    失败：{e}")

# 测试 3: 实际 API 调用
print("\n[3] 智能问数 API 调用...")
try:
    r = requests.post(
        f"{API_BASE}/api/v1/smart-query-v40/query",
        json={"query": "你好", "session_id": "test"},
        headers={"Origin": "http://localhost:5176"},
        timeout=10
    )
    print(f"    状态：{r.status_code}")
    print(f"    Content-Type: {r.headers.get('Content-Type')}")
    if r.status_code == 200:
        data = r.json()
        print(f"    成功：success={data.get('success')}")
        print(f"    route={data.get('route')}")
        print(f"    answer={data.get('answer', '')[:50]}...")
    else:
        print(f"    错误：{r.text[:200]}")
except Exception as e:
    print(f"    失败：{e}")

print("\n" + "="*70)
print("测试完成！")
print("="*70)
