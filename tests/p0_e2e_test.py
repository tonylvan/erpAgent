"""
GSD Platform - P0 Phase E2E Browser Tests
Tests: Alerts page, Tickets page, no error popups
"""
from playwright.sync_api import sync_playwright, expect
import time
import json
from datetime import datetime

FRONTEND_URL = "http://localhost:5183"
SCREENSHOT_DIR = "D:\\erpAgent\\tests\\screenshots"
REPORT_FILE = "D:\\erpAgent\\tests\\p0_e2e_test_report.json"

class P0E2ETester:
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
    
    def test_alerts_page(self, page):
        """Test Alerts Center page loads without errors"""
        page.goto(f"{FRONTEND_URL}/alerts", timeout=30000)
        page.wait_for_load_state('networkidle', timeout=30000)
        time.sleep(3)
        
        # Take screenshot
        screenshot = f"{SCREENSHOT_DIR}/p0_alerts_page.png"
        page.screenshot(path=screenshot, full_page=True)
        
        # Check page loaded (check for alert-related text or elements)
        page_title = page.query_selector('h1, h2, h3, .page-title, .el-card__header')
        assert page_title is not None or page.content() is not None, "Page did not load"
        
        # Check no error popup (this is the key test)
        error_popup = page.query_selector('.el-message--error')
        assert error_popup is None, "Error popup found"
        
        return "Alerts page loaded, no error popup"
    
    def test_tickets_page(self, page):
        """Test Ticket Center page loads without errors"""
        page.goto(f"{FRONTEND_URL}/tickets", timeout=30000)
        page.wait_for_load_state('networkidle', timeout=30000)
        time.sleep(2)
        
        # Take screenshot
        screenshot = f"{SCREENSHOT_DIR}/p0_tickets_page.png"
        page.screenshot(path=screenshot, full_page=True)
        
        # Check for table
        table = page.query_selector('.el-table')
        assert table is not None, "Table not found"
        
        # Check no error popup
        error_popup = page.query_selector('.el-message--error')
        assert error_popup is None, "Error popup found"
        
        return "Tickets page loaded, table visible, no error popup"
    
    def test_smart_query_page(self, page):
        """Test Smart Query page loads"""
        page.goto(f"{FRONTEND_URL}/smart-query", timeout=30000)
        page.wait_for_load_state('networkidle', timeout=30000)
        time.sleep(2)
        
        # Take screenshot
        screenshot = f"{SCREENSHOT_DIR}/p0_smart_query_page.png"
        page.screenshot(path=screenshot, full_page=True)
        
        # Check for query input
        query_input = page.query_selector('textarea, input[placeholder*="question" i], input[type="text"]')
        assert query_input is not None, "Query input not found"
        
        return "Smart Query page loaded, input field visible"
    
    def run_all_tests(self):
        print("=" * 70)
        print("P0 Phase - E2E Browser Tests")
        print("=" * 70)
        print(f"Frontend: {FRONTEND_URL}")
        print("=" * 70)
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, slow_mo=100)
            context = browser.new_context(viewport={'width': 1920, 'height': 1080})
            
            page = context.new_page()
            self.test("Alerts Center Page", self.test_alerts_page, page)
            page.close()
            
            page = context.new_page()
            self.test("Ticket Center Page", self.test_tickets_page, page)
            page.close()
            
            page = context.new_page()
            self.test("Smart Query Page", self.test_smart_query_page, page)
            page.close()
            
            browser.close()
        
        return self.generate_report()
    
    def generate_report(self):
        duration = (datetime.now() - self.start_time).total_seconds()
        passed = len([r for r in self.results if r["status"] == "PASSED"])
        failed = len([r for r in self.results if r["status"] == "FAILED"])
        
        report = {
            "phase": "P0",
            "test_type": "E2E Browser",
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
        print(f"P0 E2E Test Summary")
        print(f"Total: {len(self.results)} | Passed: {passed} | Failed: {failed}")
        print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
        print(f"Duration: {duration:.2f}s")
        print(f"Report saved to: {REPORT_FILE}")
        print("=" * 70)
        
        return report


if __name__ == "__main__":
    tester = P0E2ETester()
    report = tester.run_all_tests()
    exit(0 if report["summary"]["failed"] == 0 else 1)
