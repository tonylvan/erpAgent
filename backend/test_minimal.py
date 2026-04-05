# -*- coding: utf-8 -*-
"""最小化测试 - 只测试 Agent API"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8005"

print("="*70)
print("端到端测试 - 风险检测 API")
print("="*70)

# 测试业务风险
print("\n[1/3] 测试业务风险检测...")
try:
    response = requests.get(f"{BASE_URL}/api/v1/agents/business-risk", timeout=10)
    print(f"状态码：{response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] 成功！检测到 {data.get('summary', {}).get('total', 0)} 个风险")
        for finding in data.get('findings', [])[:2]:
            desc = finding.get('description', '')[:50]
            print(f"  - {finding.get('risk_type')}: {desc}")
    else:
        print(f"[ERROR] 失败：{response.text[:200]}")
except Exception as e:
    print(f"[ERROR] 异常：{e}")

# 测试财务风险
print("\n[2/3] 测试财务风险检测...")
try:
    response = requests.get(f"{BASE_URL}/api/v1/agents/financial-risk", timeout=10)
    print(f"状态码：{response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"[OK] 成功！检测到 {data.get('summary', {}).get('total', 0)} 个风险")
        for finding in data.get('findings', [])[:2]:
            desc = finding.get('description', '')[:50]
            print(f"  - {finding.get('risk_type')}: {desc}")
    else:
        print(f"[ERROR] 失败：{response.text[:200]}")
except Exception as e:
    print(f"[ERROR] 异常：{e}")

# 测试全量
print("\n[3/3] 测试全量风险检测...")
try:
    response = requests.get(f"{BASE_URL}/api/v1/agents/all", timeout=10)
    print(f"状态码：{response.status_code}")
    if response.status_code == 200:
        data = response.json()
        summary = data.get('summary', {})
        print(f"[OK] 成功！")
        print(f"  业务风险：{summary.get('business_total', 0)}")
        print(f"  财务风险：{summary.get('financial_total', 0)}")
        print(f"  用户操作：{summary.get('user_operation_total', 0)}")
        print(f"  总计：{summary.get('grand_total', 0)}")
    else:
        print(f"[ERROR] 失败：{response.text[:200]}")
except Exception as e:
    print(f"[ERROR] 异常：{e}")

print("\n" + "="*70)
print("测试完成！")
print("="*70)
