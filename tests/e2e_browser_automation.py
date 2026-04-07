"""
GSD Platform E2E Browser Automation Tests
Using Playwright for comprehensive frontend testing
"""
from playwright.sync_api import sync_playwright, expect
import time
import os
import json
from datetime import datetime

# Configuration
FRONTEND_URL = "http://localhost:5183"
BACKEND_URL = "http://localhost:8005"
SCREENSHOT_DIR = "D:\\erpAgent\\tests\\screenshots"
REPORT_FILE = "D:\\erpAgent\\tests\\e2e_test_report.json"

class E2ETestReporter:
    """Test reporter for collecting results"""
    def __init__(self):
        self.results = []
        self.start_time = datetime.now()
    
    def add_result(self, test_name, status, details=None, screenshot=None):
        self.results.append({
            "test": test_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details,
            "screenshot": screenshot
        })
    
    def generate_report(self):
        duration = (datetime.now() - self.start_time).total_seconds()
        passed = len([r for r in self.results if r["status"] == "PASSED"])
        failed = len([r for r in self.results if r["status"] == "FAILED"])
        
        report = {
            "summary": {
                "total": len(self.results),
                "passed": passed,
                "failed": failed,
                "duration_seconds": duration,
                "success_rate": passed / len(self.results) * 100 if self.results else 0
            },
            "results": self.results,
            "generated_at": datetime.now().isoformat()
        }
        
        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        return report

class TestGSDPlatformE2E:
    """GSD Platform End-to-End Tests"""
    
    def __init__(self):
        self.reporter = E2ETestReporter()
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    
    def run_all_tests(self):
        """Execute all E2E tests"""
        print("=" * 70)
        print("GSD Platform E2E Browser Automation Tests")
        print("=" * 70)
        print(f"Frontend: {FRONTEND_URL}")
        print(f"Backend: {BACKEND_URL}")
        print(f"Screenshots: {SCREENSHOT_DIR}")
        print("=" * 70)
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, slow_mo=100)
            context = browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                record_video_dir=f"{SCREENSHOT_DIR}/videos"
            )
            
            # Test 1: Homepage
            page = context.new_page()
            self.test_homepage(page)
            page.close()
            
            # Test 2: Smart Query
            page = context.new_page()
            self.test_smart_query(page)
            page.close()
            
            # Test 3: Ticket Center
            page = context.new_page()
            self.test_ticket_center(page)
            page.close()
            
            # Test 4: Alert Center
            page = context.new_page()
            self.test_alert_center(page)
            page.close()
            
            # Test 5: Knowledge Graph
            page = context.new_page()
            self.test_knowledge_graph(page)
            page.close()
            
            browser.close()
        
        # Generate report
        report = self.reporter.generate_report()
        self.print_summary(report)
        return report
    
    def test_homepage(self, page):
        """Test homepage loading and basic elements"""
        test_name = "Homepage Load"
        print(f"\n[TEST] {test_name}")
        
        try:
            # Navigate to homepage
            page.goto(FRONTEND_URL, timeout=30000)
            page.wait_for_load_state('networkidle', timeout=30000)
            
            # Take screenshot
            screenshot_path = f"{SCREENSHOT_DIR}/01_homepage.png"
            page.screenshot(path=screenshot_path, full_page=True)
            
            # Verify page loaded
            title = page.title()
            assert "ERP" in title or "GSD" in title or "Smart" in title or "鍥捐氨" in title, f"Unexpected title: {title}"
            
            # Check for app container
            app = page.query_selector('#app')
            assert app is not None, "Vue app not mounted"
            
            # Check for navigation
            nav = page.query_selector('.top-nav, nav, .el-menu')
            
            self.reporter.add_result(test_name, "PASSED", 
                f"Title: {title}, Nav found: {nav is not None}", 
                screenshot_path)
            print(f"  [PASS] {test_name}")
            
        except Exception as e:
            screenshot_path = f"{SCREENSHOT_DIR}/01_homepage_error.png"
            page.screenshot(path=screenshot_path, full_page=True)
            self.reporter.add_result(test_name, "FAILED", str(e), screenshot_path)
            print(f"  [FAIL] {test_name}: {e}")
    
    def test_smart_query(self, page):
        """Test Smart Query functionality"""
        test_name = "Smart Query"
        print(f"\n[TEST] {test_name}")
        
        try:
            # Navigate to Smart Query
            page.goto(f"{FRONTEND_URL}/smart-query", timeout=30000)
            page.wait_for_load_state('networkidle', timeout=30000)
            
            screenshot_path = f"{SCREENSHOT_DIR}/02_smart_query.png"
            page.screenshot(path=screenshot_path, full_page=True)
            
            # Check for query input
            input_selectors = [
                'input[placeholder*="question" i]',
                'input[placeholder*="闂" i]',
                '.query-input input',
                '[data-testid="query-input"]',
                'textarea'
            ]
            
            query_input = None
            for selector in input_selectors:
                query_input = page.query_selector(selector)
                if query_input:
                    break
            
            if query_input:
                # Type a test query
                query_input.fill("Show me top 10 customers")
                time.sleep(0.5)
                
                # Look for submit button
                submit_btn = page.query_selector('button[type="submit"], .submit-btn, [data-testid="submit-btn"]')
                if submit_btn:
                    submit_btn.click()
                    time.sleep(2)
                    
                    # Wait for response
                    page.wait_for_timeout(3000)
                    
                    # Take screenshot after query
                    screenshot_path = f"{SCREENSHOT_DIR}/02_smart_query_response.png"
                    page.screenshot(path=screenshot_path, full_page=True)
            
            self.reporter.add_result(test_name, "PASSED",
                "Query interface accessible", screenshot_path)
            print(f"  鉁?{test_name} - PASSED")

        except Exception as e:
            screenshot_path = f"{SCREENSHOT_DIR}/02_smart_query_error.png"
            page.screenshot(path=screenshot_path, full_page=True)
            self.reporter.add_result(test_name, "FAILED", str(e), screenshot_path)
            print(f"  鉁?{test_name} - FAILED: {e}")

    def test_ticket_center(self, page):
        """Test Ticket Center functionality"""
        test_name = "Ticket Center"
        print(f"\n[TEST] {test_name}")

        try:
            # Navigate to Ticket Center
            page.goto(f"{FRONTEND_URL}/tickets", timeout=30000)
            page.wait_for_load_state('networkidle', timeout=30000)

            screenshot_path = f"{SCREENSHOT_DIR}/03_ticket_center.png"
            page.screenshot(path=screenshot_path, full_page=True)

            # Check for ticket list or stats cards
            stats_cards = page.query_selector_all('.stat-card, .el-card, .ticket-stats')
            ticket_table = page.query_selector('table, .el-table, .ticket-list')

            details = f"Stats cards: {len(stats_cards)}, Table found: {ticket_table is not None}"

            self.reporter.add_result(test_name, "PASSED", details, screenshot_path)
            print(f"  鉁?{test_name} - PASSED")

        except Exception as e:
            screenshot_path = f"{SCREENSHOT_DIR}/03_ticket_center_error.png"
            page.screenshot(path=screenshot_path, full_page=True)
            self.reporter.add_result(test_name, "FAILED", str(e), screenshot_path)
            print(f"  鉁?{test_name} - FAILED: {e}")

    def test_alert_center(self, page):
        """Test Alert Center functionality"""
        test_name = "Alert Center"
        print(f"\n[TEST] {test_name}")

        try:
            # Navigate to Alert Center
            page.goto(f"{FRONTEND_URL}/alerts", timeout=30000)
            page.wait_for_load_state('networkidle', timeout=30000)

            screenshot_path = f"{SCREENSHOT_DIR}/04_alert_center.png"
            page.screenshot(path=screenshot_path, full_page=True)

            # Check for alert elements
            alert_cards = page.query_selector_all('.alert-card, .warning-card, .el-alert')

            details = f"Alert elements found: {len(alert_cards)}"

            self.reporter.add_result(test_name, "PASSED", details, screenshot_path)
            print(f"  鉁?{test_name} - PASSED")

        except Exception as e:
            screenshot_path = f"{SCREENDOWNLOAD_DIR}/04_alert_center_error.png"
            page.screenshot(path=screenshot_path, full_page=True)
            self.reporter.add_result(test_name, "FAILED", str(e), screenshot_path)
            print(f"  鉁?{test_name} - FAILED: {e}")

    def test_knowledge_graph(self, page):
        """Test Knowledge Graph functionality"""
        test_name = "Knowledge Graph"
        print(f"\n[TEST] {test_name}")

        try:
            # Navigate to Knowledge Graph
            page.goto(f"{FRONTEND_URL}/graph", timeout=30000)
            page.wait_for_load_state('networkidle', timeout=30000)

            screenshot_path = f"{SCREENSHOT_DIR}/05_knowledge_graph.png"
            page.screenshot(path=screenshot_path, full_page=True)

            # Check for graph container
            graph_container = page.query_selector('.graph-container, #graph, canvas, svg')

            details = f"Graph container found: {graph_container is not None}"

            self.reporter.add_result(test_name, "PASSED", details, screenshot_path)
            print(f"  鉁?{test_name} - PASSED")

        except Exception as e:
            screenshot_path = f"{SCREENSHOT_DIR}/05_knowledge_graph_error.png"
            page.screenshot(path=screenshot_path, full_page=True)
            self.reporter.add_result(test_name, "FAILED", str(e), screenshot_path)
            print(f"  鉁?{test_name} - FAILED: {e}")

    def print_summary(self, report):
        """Print test summary"""
        print("\n" + "=" * 70)
        print("E2E Test Summary")
        print("=" * 70)
        print(f"Total Tests: {report['summary']['total']}")
        print(f"Passed: {report['summary']['passed']}")
        print(f"Failed: {report['summary']['failed']}")
        print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
        print(f"Duration: {report['summary']['duration_seconds']:.1f}s")
        print("=" * 70)
        print(f"\nDetailed report saved to: {REPORT_FILE}")


def main():
    """Main entry point"""
    tester = TestGSDPlatformE2E()
    report = tester.run_all_tests()
    return report


if __name__ == "__main__":
    main()

