"""
Test Alert Center API data loading
"""
import urllib.request
import json

# Test stats endpoint
print("Testing /api/v1/alerts/stats...")
response = urllib.request.urlopen('http://localhost:8006/api/v1/alerts/stats')
data = json.loads(response.read().decode())
print(f"Stats: {data}")

# Test alerts list endpoint
print("\nTesting /api/v1/alerts...")
response = urllib.request.urlopen('http://localhost:8006/api/v1/alerts?page=1&size=20')
data = json.loads(response.read().decode())
print(f"Total alerts: {len(data)}")
if data:
    print(f"First alert: {data[0]['title']}")

print("\n✅ All API endpoints working!")
