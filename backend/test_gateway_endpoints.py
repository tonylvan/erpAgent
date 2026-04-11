# -*- coding: utf-8 -*-
import requests
import json

# 测试 OpenClaw Gateway 连接
GATEWAY_URL = 'http://127.0.0.1:18789'
TOKEN = '3354bfe288d7b3d499d84d5b21d540ce21ff0c3e7dedbc18'

print("=" * 60)
print("测试 OpenClaw Gateway 连接")
print("=" * 60)

# 测试 1：检查 Gateway 是否可访问
print("\n1️⃣ 测试 Gateway 连接...")
try:
    r = requests.get(f"{GATEWAY_URL}/health", timeout=5)
    print(f"✅ /health 响应：{r.status_code}")
except Exception as e:
    print(f"❌ /health 失败：{e}")

# 测试 2：尝试不同的 API 端点
endpoints = [
    "/v1/chat/completions",
    "/api/v1/chat/completions",
    "/chat/completions",
    "/v1/completions"
]

print("\n2️⃣ 测试 API 端点...")
for endpoint in endpoints:
    try:
        headers = {"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"}
        data = {
            "model": "dashscope/glm-5",
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 10
        }
        r = requests.post(f"{GATEWAY_URL}{endpoint}", headers=headers, json=data, timeout=10)
        print(f"✅ {endpoint}: {r.status_code}")
        if r.status_code == 200:
            print(f"   响应：{r.json().get('choices', [{}])[0].get('message', {}).get('content', '')[:50]}...")
            break
    except Exception as e:
        print(f"❌ {endpoint}: {str(e)[:50]}")

print("\n" + "=" * 60)
print("✅ Gateway 测试完成！")
print("=" * 60)
