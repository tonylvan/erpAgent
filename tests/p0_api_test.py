"""
GSD Platform - P0 Phase API Tests
Tests for: Database tables, Alerts API, Tickets API
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8007"
REPORT_FILE = "D:\\erpAgent\\tests\\p0_api_test_report.json"

class P0APITester:
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
    
    def test(self, name, func):
        try:
            result = func()
            self.results.append({
                "test": name,
                "status": "PASSED",
                "details": result
            })
            print(f"  [PASS] {name}")
            return True
        except Exception as e:
            self.results.append({
                "test": name,
                "status": "FAILED",
                "details": str(e)
            })
            print(f"  [FAIL] {name}: {e}")
            return False
    
    def test_alerts_api(self):
        """Test Alerts API"""
        response = requests.get(f"{BASE_URL}/api/v1/alerts")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Expected list"
        return f"{len(data)} alerts returned"
    
    def test_tickets_api(self):
        """Test Tickets API"""
        response = requests.get(f"{BASE_URL}/api/v1/tickets")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Expected list"
        return f"{len(data)} tickets returned"
    
    def test_alert_stats_api(self):
        """Test Alert Stats API"""
        response = requests.get(f"{BASE_URL}/api/v1/alerts/stats")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "critical" in data, "Missing critical field"
        assert "high" in data, "Missing high field"
        return f"Stats: {data['critical']} critical, {data['high']} high"
    
    def test_alert_rules_api(self):
        """Test Alert Rules API"""
        response = requests.get(f"{BASE_URL}/api/v1/alerts/rules")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("success") == True, "Expected success=true"
        return f"{data.get('total', 0)} rules returned"
    
    def run_all_tests(self):
        print("=" * 70)
        print("P0 Phase - API Automation Tests")
        print("=" * 70)
        
        self.test("Alerts API", self.test_alerts_api)
        self.test("Tickets API", self.test_tickets_api)
        self.test("Alert Stats API", self.test_alert_stats_api)
        self.test("Alert Rules API", self.test_alert_rules_api)
        
        return self.generate_report()
    
    def generate_report(self):
        duration = (datetime.now() - self.start_time).total_seconds()
        passed = len([r for r in self.results if r["status"] == "PASSED"])
        failed = len([r for r in self.results if r["status"] == "FAILED"])
        
        report = {
            "phase": "P0",
            "test_type": "API Automation",
            "summary": {
                "total": len(self.results),
                "passed": passed,
                "failed": failed,
                "success_rate": passed / len(self.results) * 100 if self.results else 0,
                "duration_seconds": duration
            },
            "results": self.results,
            "generated_at": datetime.now().isoformat()
        }
        
        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print("\n" + "=" * 70)
        print(f"P0 API Test Summary")
        print(f"Total: {len(self.results)} | Passed: {passed} | Failed: {failed}")
        print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
        print(f"Duration: {duration:.2f}s")
        print(f"Report saved to: {REPORT_FILE}")
        print("=" * 70)
        
        return report


if __name__ == "__main__":
    tester = P0APITester()
    report = tester.run_all_tests()
    exit(0 if report["summary"]["failed"] == 0 else 1)
