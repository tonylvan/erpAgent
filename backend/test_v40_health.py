# -*- coding: utf-8 -*-
import sys
sys.stdout.reconfigure(encoding='utf-8')
import requests
import json

print("Testing v4.0 API...")

# 健康检查
r = requests.get("http://localhost:8005/api/v1/smart-query-v40/health", timeout=10)
print(f"Health Status: {r.status_code}")
print(f"Response: {json.dumps(r.json(), indent=2, ensure_ascii=False)}")
