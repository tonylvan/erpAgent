"""
Test Neo4j Alert Service
"""
import sys
sys.path.insert(0, r'D:\erpAgent\backend')

from app.services.alert_service import AlertService

# Create service instance
service = AlertService()

# Get all alerts
print("=" * 50)
print("Testing Neo4j Alert Service")
print("=" * 50)

result = service.get_all_alerts()

print(f"\n[OK] Get alerts successful!")
print(f"Statistics:")
print(f"  Total: {result['stats']['total']}")
print(f"  RED: {result['stats']['by_severity'].get('RED', 0)}")
print(f"  ORANGE: {result['stats']['by_severity'].get('ORANGE', 0)}")
print(f"  YELLOW: {result['stats']['by_severity'].get('YELLOW', 0)}")
print(f"  Financial: {result['stats']['financial_risks']}")
print(f"  Business: {result['stats']['business_alerts']}")

print(f"\nAlert Details:")
for alert_type, alerts in result['alerts'].items():
    if alerts:
        print(f"\n  {alert_type.upper()}: {len(alerts)} alerts")
        for alert in alerts[:3]:  # Show first 3
            desc = alert.get('description', 'N/A')
            print(f"    - {desc}")

print("\n" + "=" * 50)
print("[OK] Test Complete!")
print("=" * 50)
