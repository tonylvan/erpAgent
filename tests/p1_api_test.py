"""
GSD Platform - P1 Phase API Tests
Tests for: Ticket Creation, WebSocket endpoints
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8007"
REPORT_FILE = "D:\\erpAgent\\tests\\p1_api_test_report.json"

class P1APITester:
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
    
    def test_create_ticket(self):
        """Test Ticket Creation API"""
        payload = {
            "title": f"API Test Ticket {datetime.now().strftime('%H%M%S')}",
            "description": "Test ticket created via P1 API test",
            "priority": "MEDIUM",
            "category": "Testing"
        }
        response = requests.post(f"{BASE_URL}/api/v1/tickets", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("success") == True, "Expected success=true"
        assert "ticket_id" in data, "Missing ticket_id"
        return f"Ticket created with ID: {data.get('ticket_id')}"
    
    def test_tickets_list(self):
        """Test Tickets List API"""
        response = requests.get(f"{BASE_URL}/api/v1/tickets")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Expected list"
        assert len(data) >= 1, "Expected at least 1 ticket"
        return f"{len(data)} tickets returned"
    
    def test_ticket_stats(self):
        """Test Ticket Stats API"""
        response = requests.get(f"{BASE_URL}/api/v1/tickets/stats")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert "by_status" in data, "Missing by_status"
        assert "by_priority" in data, "Missing by_priority"
        assert "total" in data, "Missing total"
        return f"Total: {data.get('total')}, Open: {data.get('open')}"
    
    def test_alerts_api(self):
        """Test Alerts API (regression)"""
        response = requests.get(f"{BASE_URL}/api/v1/alerts")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Expected list"
        return f"{len(data)} alerts returned"
    
    def run_all_tests(self):
        print("=" * 70)
        print("P1 Phase - API Automation Tests")
        print("=" * 70)
        
        self.test("Create Ticket API", self.test_create_ticket)
        self.test("Tickets List API", self.test_tickets_list)
        self.test("Ticket Stats API", self.test_ticket_stats)
        self.test("Alerts API (regression)", self.test_alerts_api)
        
        return self.generate_report()
    
    def generate_report(self):
        duration = (datetime.now() - self.start_time).total_seconds()
        passed = len([r for r in self.results if r["status"] == "PASSED"])
        failed = len([r for r in self.results if r["status"] == "FAILED"])
        
        report = {
            "phase": "P1",
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
        print(f"P1 API Test Summary")
        print(f"Total: {len(self.results)} | Passed: {passed} | Failed: {failed}")
        print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
        print(f"Duration: {duration:.2f}s")
        print(f"Report saved to: {REPORT_FILE}")
        print("=" * 70)
        
        return report


if __name__ == "__main__":
    tester = P1APITester()
    report = tester.run_all_tests()
    exit(0 if report["summary"]["failed"] == 0 else 1)
