# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests

print("🔍 GSD API 连接测试")
print("=" * 60)

try:
    # 健康检查
    r = requests.get("http://localhost:8005/api/v1/smart-query-v35/health", timeout=10)
    print(f"\n✅ 健康检查：{r.status_code}")
    print(f"   {r.json()}")
    
    # 测试查询
    r = requests.post("http://localhost:8005/api/v1/smart-query-v35/query", 
                      json={"query": "你好", "user_id": "admin"}, 
                      timeout=30)
    print(f"\n✅ API 查询：{r.status_code}")
    result = r.json()
    print(f"   Success: {result.get('success')}")
    print(f"   Route: {result.get('route')}")
    
except requests.exceptions.ConnectionError as e:
    print(f"\n❌ 连接错误：后端服务未启动")
    print(f"   请运行：cd D:\\erpAgent\\backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8005")
except requests.exceptions.Timeout:
    print(f"\n❌ 请求超时：后端服务响应慢")
except Exception as e:
    print(f"\n❌ 错误：{e}")

print("\n" + "=" * 60)
