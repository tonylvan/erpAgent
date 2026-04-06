"""
验证工单分配 API 功能
"""
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

print("=" * 60)
print("工单分配 API 验证测试")
print("=" * 60)

# 测试 1: 分配成功的工单
print("\n1. 测试分配工单 (ticket_id=1)...")
response = client.post(
    "/api/v1/tickets/1/assign",
    json={"assigned_to": "user_test", "reason": "验证测试"}
)
print(f"   状态码：{response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"   [OK] 工单 ID: {data.get('id')}")
    print(f"   [OK] 状态：{data.get('status')}")
    print(f"   [OK] 分配给：{data.get('assigned_to')}")
    print(f"   [OK] 更新时间：{data.get('updated_at')}")
else:
    print(f"   ❌ 错误：{response.json()}")

# 测试 2: 工单不存在
print("\n2. 测试工单不存在 (ticket_id=99999)...")
response = client.post(
    "/api/v1/tickets/99999/assign",
    json={"assigned_to": "user_test", "reason": "测试"}
)
print(f"   状态码：{response.status_code}")
if response.status_code == 404:
    print(f"   [OK] 正确返回 404")
    print(f"   错误信息：{response.json().get('detail')}")
else:
    print(f"   ❌ 预期 404，实际：{response.status_code}")

# 测试 3: 重复分配
print("\n3. 测试重复分配...")
response1 = client.post(
    "/api/v1/tickets/1/assign",
    json={"assigned_to": "user_first", "reason": "第一次分配"}
)
response2 = client.post(
    "/api/v1/tickets/1/assign",
    json={"assigned_to": "user_second", "reason": "第二次分配"}
)
print(f"   第一次分配状态码：{response1.status_code}")
print(f"   第二次分配状态码：{response2.status_code}")
if response2.status_code == 200:
    data = response2.json()
    print(f"   [OK] 最终分配给：{data.get('assigned_to')}")
    print(f"   [OK] 状态：{data.get('status')}")

print("\n" + "=" * 60)
print("验证完成！")
print("=" * 60)
