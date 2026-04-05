"""
测试 Neo4j 预警服务
"""
import sys
sys.path.insert(0, r'D:\erpAgent\backend')

from app.services.alert_service import AlertService

# 创建服务实例
service = AlertService()

# 获取所有预警
print("=" * 50)
print("📊 测试 Neo4j 预警服务")
print("=" * 50)

result = service.get_all_alerts()

print(f"\n✅ 获取预警成功！")
print(f"统计信息:")
print(f"  总预警数：{result['stats']['total']}")
print(f"  高危预警：{result['stats']['by_severity'].get('RED', 0)}")
print(f"  警告预警：{result['stats']['by_severity'].get('ORANGE', 0)}")
print(f"  提示预警：{result['stats']['by_severity'].get('YELLOW', 0)}")
print(f"  财务风险：{result['stats']['financial_risks']}")
print(f"  业务预警：{result['stats']['business_alerts']}")

print(f"\n预警详情:")
for alert_type, alerts in result['alerts'].items():
    if alerts:
        print(f"\n  {alert_type.upper()}: {len(alerts)} 条")
        for alert in alerts[:3]:  # 只显示前 3 条
            print(f"    - {alert.get('description', 'N/A')}")

print("\n" + "=" * 50)
print("✅ 测试完成！")
print("=" * 50)
