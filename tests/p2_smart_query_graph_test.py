"""
GSD Platform - Smart Query & Knowledge Graph Tests
Tests for: Smart Query API, Knowledge Graph API
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8007"
REPORT_FILE = "D:\\erpAgent\\tests\\p2_smart_query_graph_test_report.json"

class SmartQueryGraphTester:
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
    
    def test_smart_query_suggested(self):
        """Test Smart Query Suggested Questions API"""
        response = requests.get(f"{BASE_URL}/api/v1/smart-query-v2/suggested-questions")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("success") == True, "Expected success=true"
        assert "questions" in data, "Missing questions field"
        return f"{len(data.get('questions', []))} suggested questions returned"
    
    def test_smart_query_query(self):
        """Test Smart Query Query API"""
        payload = {
            "query": "显示销售额前 10 的客户",
            "session_id": "test-session-1"
        }
        response = requests.post(f"{BASE_URL}/api/v1/smart-query-v2/query", json=payload)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("success") == True or "answer" in data, "Expected successful response"
        return "Smart query executed successfully"
    
    def test_graph_data(self):
        """Test Knowledge Graph Data API"""
        response = requests.get(f"{BASE_URL}/api/v1/graph")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("success") == True, "Expected success=true"
        assert "nodes" in data, "Missing nodes field"
        assert "edges" in data, "Missing edges field"
        nodes_count = len(data.get("nodes", []))
        edges_count = len(data.get("edges", []))
        return f"Graph data: {nodes_count} nodes, {edges_count} edges"
    
    def test_graph_stats(self):
        """Test Knowledge Graph Stats API"""
        response = requests.get(f"{BASE_URL}/api/v1/graph/stats")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("success") == True, "Expected success=true"
        assert "stats" in data, "Missing stats field"
        stats = data.get("stats", {})
        return f"Stats: {stats.get('total_nodes', 0)} nodes, {stats.get('total_edges', 0)} edges"
    
    def test_graph_nodes(self):
        """Test Knowledge Graph Nodes API"""
        response = requests.get(f"{BASE_URL}/api/v1/graph/nodes")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("success") == True, "Expected success=true"
        return f"{len(data.get('nodes', []))} nodes returned"
    
    def test_graph_edges(self):
        """Test Knowledge Graph Edges API"""
        response = requests.get(f"{BASE_URL}/api/v1/graph/edges")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get("success") == True, "Expected success=true"
        return f"{len(data.get('edges', []))} edges returned"
    
    def run_all_tests(self):
        print("=" * 70)
        print("Smart Query & Knowledge Graph - API Tests")
        print("=" * 70)
        
        self.test("Smart Query Suggested Questions", self.test_smart_query_suggested)
        self.test("Smart Query Query", self.test_smart_query_query)
        self.test("Knowledge Graph Data", self.test_graph_data)
        self.test("Knowledge Graph Stats", self.test_graph_stats)
        self.test("Knowledge Graph Nodes", self.test_graph_nodes)
        self.test("Knowledge Graph Edges", self.test_graph_edges)
        
        return self.generate_report()
    
    def generate_report(self):
        duration = (datetime.now() - self.start_time).total_seconds()
        passed = len([r for r in self.results if r["status"] == "PASSED"])
        failed = len([r for r in self.results if r["status"] == "FAILED"])
        
        report = {
            "phase": "P2",
            "test_type": "Smart Query & Knowledge Graph API",
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
    tester = SmartQueryGraphTester()
    report = tester.run_all_tests()
    exit(0 if report["summary"]["failed"] == 0 else 1)
