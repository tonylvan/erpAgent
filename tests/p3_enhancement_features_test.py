"""
GSD Platform - Enhancement Features Tests
Tests for: Alert Escalation, Ticket-Alert Integration
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8007"
REPORT_FILE = "D:\\erpAgent\\tests\\p3_enhancement_features_test_report.json"

class EnhancementFeaturesTester:
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
    
    def test_escalation_rules(self):
        """Test Alert Escalation Rules API"""
        response = requests.get(f"{BASE_URL}/api/v1/escalation-rules")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Expected list"
        assert len(data) >= 1, "Expected at least 1 rule"
        return f"{len(data)} escalation rules returned"
    
    def test_execute_escalation(self):
        """Test Execute Escalation API"""
        response = requests.post(f"{BASE_URL}/api/v1/execute-escalation")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("success") == True, "Expected success=true"
        return f"Escalated {data.get('escalated_count', 0)} alerts"
    
    def test_escalation_stats(self):
        """Test Escalation Stats API"""
        response = requests.get(f"{BASE_URL}/api/v1/escalation-stats")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("success") == True, "Expected success=true"
        assert "stats" in data, "Missing stats field"
        return f"Stats retrieved successfully"
    
    def test_link_alert_to_ticket(self):
        """Test Link Alert to Ticket API"""
        payload = {
            "alert_id": 1,
            "ticket_id": 1,
            "relationship_type": "related_to"
        }
        response = requests.post(f"{BASE_URL}/api/v1/link-alert-to-ticket", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("success") == True, "Expected success=true"
        return f"Linked alert {data.get('alert_id')} to ticket {data.get('ticket_id')}"
    
    def test_ticket_alerts(self):
        """Test Get Ticket Alerts API"""
        response = requests.get(f"{BASE_URL}/api/v1/ticket/1/alerts")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("success") == True, "Expected success=true"
        return f"{len(data.get('alerts', []))} alerts linked to ticket"
    
    def test_alert_tickets(self):
        """Test Get Alert Tickets API"""
        response = requests.get(f"{BASE_URL}/api/v1/alert/1/tickets")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("success") == True, "Expected success=true"
        return f"{len(data.get('tickets', []))} tickets linked to alert"
    
    def run_all_tests(self):
        print("=" * 70)
        print("Enhancement Features - API Tests")
        print("=" * 70)
        
        self.test("Escalation Rules", self.test_escalation_rules)
        self.test("Execute Escalation", self.test_execute_escalation)
        self.test("Escalation Stats", self.test_escalation_stats)
        self.test("Link Alert to Ticket", self.test_link_alert_to_ticket)
        self.test("Get Ticket Alerts", self.test_ticket_alerts)
        self.test("Get Alert Tickets", self.test_alert_tickets)
        
        return self.generate_report()
    
    def generate_report(self):
        duration = (datetime.now() - self.start_time).total_seconds()
        passed = len([r for r in self.results if r["status"] == "PASSED"])
        failed = len([r for r in self.results if r["status"] == "FAILED"])
        
        report = {
            "phase": "P3",
            "test_type": "Enhancement Features API",
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
        print(f"Test Summary")
        print(f"Total: {len(self.results)} | Passed: {passed} | Failed: {failed}")
        print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
        print(f"Duration: {duration:.2f}s")
        print(f"Report saved to: {REPORT_FILE}")
        print("=" * 70)
        
        return report


if __name__ == "__main__":
    tester = EnhancementFeaturesTester()
    report = tester.run_all_tests()
    exit(0 if report["summary"]["failed"] == 0 else 1)
