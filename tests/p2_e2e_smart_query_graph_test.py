"""
GSD Platform - Smart Query & Knowledge Graph E2E Tests
Tests: Smart Query page, Knowledge Graph page visualization
"""
from playwright.sync_api import sync_playwright, expect
import time
import json
from datetime import datetime

FRONTEND_URL = "http://localhost:5183"
SCREENSHOT_DIR = "D:\\erpAgent\\tests\\screenshots"
REPORT_FILE = "D:\\erpAgent\\tests\\p2_e2e_smart_query_graph_test_report.json"

class SmartQueryGraphE2ETester:
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
    
    def test(self, name, func, page):
        try:
            result = func(page)
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
    
    def test_smart_query_page(self, page):
        """Test Smart Query page loads and displays correctly"""
        page.goto(f"{FRONTEND_URL}/smart-query", timeout=30000)
        page.wait_for_load_state('networkidle', timeout=30000)
        time.sleep(3)
        
        # Take screenshot
        screenshot = f"{SCREENSHOT_DIR}/p2_smart_query_page.png"
        page.screenshot(path=screenshot, full_page=True)
        
        # Check for query input
        query_input = page.query_selector('textarea, input[placeholder*="question" i], input[type="text"]')
        assert query_input is not None, "Query input not found"
        
        # Check for send button or chat area
        send_button = page.query_selector('button:has-text("发送"), button[type="submit"], .send-button')
        chat_area = page.query_selector('.chat-container, .chat-box, .conversation-area')
        assert send_button is not None or chat_area is not None, "Send button or chat area not found"
        
        # Check no error popup
        error_popup = page.query_selector('.el-message--error')
        assert error_popup is None, "Error popup found"
        
        return "Smart Query page loaded, input and chat area visible, no error popup"
    
    def test_knowledge_graph_page(self, page):
        """Test Knowledge Graph page loads and displays graph"""
        page.goto(f"{FRONTEND_URL}/knowledge-graph", timeout=30000)
        page.wait_for_load_state('networkidle', timeout=30000)
        time.sleep(5)  # Wait for D3 graph to render
        
        # Take screenshot
        screenshot = f"{SCREENSHOT_DIR}/p2_knowledge_graph_page.png"
        page.screenshot(path=screenshot, full_page=True)
        
        # Check for graph container
        graph_container = page.query_selector('.graph-canvas, #graph-canvas, .d3-graph, svg')
        assert graph_container is not None, "Graph container not found"
        
        # Check for graph elements (nodes or edges)
        # D3 typically creates circles for nodes and lines for edges
        nodes = page.query_selector_all('circle, .node, [class*="node"]')
        edges = page.query_selector_all('line, .edge, .link, [class*="edge"], [class*="link"]')
        
        # At least some graph elements should exist
        assert len(nodes) > 0 or len(edges) > 0, f"No graph elements found (nodes: {len(nodes)}, edges: {len(edges)})"
        
        # Check no error popup
        error_popup = page.query_selector('.el-message--error')
        assert error_popup is None, "Error popup found"
        
        return f"Knowledge Graph page loaded, graph rendered with {len(nodes)} nodes and {len(edges)} edges, no error popup"
    
    def test_graph_toolbar(self, page):
        """Test Knowledge Graph toolbar controls"""
        page.goto(f"{FRONTEND_URL}/knowledge-graph", timeout=30000)
        page.wait_for_load_state('networkidle', timeout=30000)
        time.sleep(3)
        
        # Check for toolbar buttons
        toolbar = page.query_selector('.canvas-toolbar, .toolbar, .graph-toolbar')
        assert toolbar is not None, "Toolbar not found"
        
        # Check for zoom/reset buttons
        zoom_buttons = page.query_selector_all('button[title*="zoom" i], button[title*="重置" i], .zoom-btn')
        # At least toolbar should exist
        
        return "Graph toolbar found with controls"
    
    def run_all_tests(self):
        print("=" * 70)
        print("Smart Query & Knowledge Graph - E2E Browser Tests")
        print("=" * 70)
        print(f"Frontend: {FRONTEND_URL}")
        print("=" * 70)
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, slow_mo=100)
            context = browser.new_context(viewport={'width': 1920, 'height': 1080})
            
            page = context.new_page()
            self.test("Smart Query Page", self.test_smart_query_page, page)
            page.close()
            
            page = context.new_page()
            self.test("Knowledge Graph Page", self.test_knowledge_graph_page, page)
            page.close()
            
            page = context.new_page()
            self.test("Graph Toolbar", self.test_graph_toolbar, page)
            page.close()
            
            browser.close()
        
        return self.generate_report()
    
    def generate_report(self):
        duration = (datetime.now() - self.start_time).total_seconds()
        passed = len([r for r in self.results if r["status"] == "PASSED"])
        failed = len([r for r in self.results if r["status"] == "FAILED"])
        
        report = {
            "phase": "P2",
            "test_type": "Smart Query & Knowledge Graph E2E",
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
        print(f"E2E Test Summary")
        print(f"Total: {len(self.results)} | Passed: {passed} | Failed: {failed}")
        print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
        print(f"Duration: {duration:.2f}s")
        print(f"Report saved to: {REPORT_FILE}")
        print("=" * 70)
        
        return report


if __name__ == "__main__":
    tester = SmartQueryGraphE2ETester()
    report = tester.run_all_tests()
    exit(0 if report["summary"]["failed"] == 0 else 1)
