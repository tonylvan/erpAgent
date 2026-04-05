import requests
import time

print("测试后端 API 连接...")
print("="*60)

# 测试健康检查
try:
    r = requests.get("http://localhost:8005/health", timeout=5)
    print(f"[OK] 健康检查：{r.status_code}")
    print(f"     响应：{r.json()}")
except Exception as e:
    print(f"[FAIL] 健康检查：{e}")

time.sleep(1)

# 测试根路径
try:
    r = requests.get("http://localhost:8005/", timeout=5)
    print(f"[OK] 根路径：{r.status_code}")
    print(f"     响应：{r.json()}")
except Exception as e:
    print(f"[FAIL] 根路径：{e}")

time.sleep(1)

# 测试智能问数 API
try:
    r = requests.post(
        "http://localhost:8005/api/v1/smart-query-v40/query",
        json={"query": "查最近一笔付款单", "session_id": "test-001"},
        timeout=10
    )
    print(f"[OK] 智能问数 v4.0: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"     响应状态：{data.get('status', 'N/A')}")
        print(f"     数据类型：{data.get('data_type', 'N/A')}")
    else:
        print(f"     错误：{r.text[:200]}")
except Exception as e:
    print(f"[FAIL] 智能问数 v4.0: {e}")

print("\n" + "="*60)
print("API 测试完成")
