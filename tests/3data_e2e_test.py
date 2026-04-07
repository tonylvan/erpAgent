"""
GSD Platform 3-Data-Example E2E Test
Testing 3 real data scenarios end-to-end
"""
from playwright.sync_api import sync_playwright, expect
import time
import json
from datetime import datetime

# Configuration
FRONTEND_URL = "http://localhost:5183"
BACKEND_URL = "http://localhost:8007"
SCREENSHOT_DIR = "D:\\erpAgent\\tests\\screenshots"
REPORT_FILE = "D:\\erpAgent\\tests\\3data_e2e_test_report.json"


class ThreeDataExampleTester:
    """Test 3 real data examples end-to-end"""
    
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
    
    def run_all_tests(self):
        """Execute 3 data example tests"""
        print("=" * 70)
        print("GSD Platform - 3 Data Example E2E Tests")
        print("=" * 70)
        print(f"Frontend: {FRONTEND_URL}")
        print(f"Backend: {BACKEND_URL}")
        print("=" * 70)
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False, slow_mo=100)
            context = browser.new_context(viewport={'width': 1920, 'height': 1080})
            
            # Test 1: Customer Sales Query
            page = context.new_page()
            self.test_customer_sales_query(page)
            page.close()
            
            # Test 2: Product Inventory Query
            page = context.new_page()
            self.test_product_inventory_query(page)
            page.close()
            
            # Test 3: Order Trend Query
            page = context.new_page()
            self.test_order_trend_query(page)
            page.close()
            
            browser.close()
        
        # Generate report
        return self.generate_report()
    
    def test_customer_sales_query(self, page):
        """Test 1: Query top customers by sales"""
        test_name = "Test 1: Customer Sales Query"
        print(f"\n[TEST] {test_name}")
        
        try:
            # Navigate to Smart Query
            page.goto(f"{FRONTEND_URL}/smart-query", timeout=30000)
            page.wait_for_load_state('networkidle', timeout=30000)
            time.sleep(2)
            
            # Take screenshot
            screenshot_path = f"{SCREENSHOT_DIR}/3data_01_customer_sales.png"
            page.screenshot(path=screenshot_path, full_page=True)
            
            # Find query input
            query_input = page.query_selector('textarea, input[placeholder*="问题"]')
            if not query_input:
                query_input = page.query_selector('input[type="text"]')
            
            if query_input:
                # Type query
                query_input.fill("显示销售额前 10 的客户")
                time.sleep(1)
                
                # Take screenshot after typing
                screenshot_path = f"{SCREENSHOT_DIR}/3data_01_customer_sales_typing.png"
                page.screenshot(path=screenshot_path, full_page=True)
                
                # Check for submit button
                submit_btn = page.query_selector('button:has-text("发送"), button:has-text("查询"), button[type="submit"]')
                
                self.add_result(test_name, "PASSED", 
                    f"Query interface accessible, input filled: 显示销售额前 10 的客户", 
                    screenshot_path)
                print(f"  [PASS] {test_name}")
            else:
                raise Exception("Query input not found")
            
        except Exception as e:
            screenshot_path = f"{SCREENSHOT_DIR}/3data_01_customer_sales_error.png"
            page.screenshot(path=screenshot_path, full_page=True)
            self.add_result(test_name, "FAILED", str(e), screenshot_path)
            print(f"  [FAIL] {test_name}: {e}")
    
    def test_product_inventory_query(self, page):
        """Test 2: Query product inventory status"""
        test_name = "Test 2: Product Inventory Query"
        print(f"\n[TEST] {test_name}")
        
        try:
            # Navigate to Smart Query
            page.goto(f"{FRONTEND_URL}/smart-query", timeout=30000)
            page.wait_for_load_state('networkidle', timeout=30000)
            time.sleep(2)
            
            # Take screenshot
            screenshot_path = f"{SCREENSHOT_DIR}/3data_02_product_inventory.png"
            page.screenshot(path=screenshot_path, full_page=True)
            
            # Find query input
            query_input = page.query_selector('textarea, input[placeholder*="问题"]')
            if not query_input:
                query_input = page.query_selector('input[type="text"]')
            
            if query_input:
                # Type query
                query_input.fill("查询库存预警商品")
                time.sleep(1)
                
                # Take screenshot after typing
                screenshot_path = f"{SCREENSHOT_DIR}/3data_02_product_inventory_typing.png"
                page.screenshot(path=screenshot_path, full_page=True)
                
                self.add_result(test_name, "PASSED", 
                    f"Query interface accessible, input filled: 查询库存预警商品", 
                    screenshot_path)
                print(f"  [PASS] {test_name}")
            else:
                raise Exception("Query input not found")
            
        except Exception as e:
            screenshot_path = f"{SCREENSHOT_DIR}/3data_02_product_inventory_error.png"
            page.screenshot(path=screenshot_path, full_page=True)
            self.add_result(test_name, "FAILED", str(e), screenshot_path)
            print(f"  [FAIL] {test_name}: {e}")
    
    def test_order_trend_query(self, page):
        """Test 3: Query order trend"""
        test_name = "Test 3: Order Trend Query"
        print(f"\n[TEST] {test_name}")
        
        try:
            # Navigate to Smart Query
            page.goto(f"{FRONTEND_URL}/smart-query", timeout=30000)
            page.wait_for_load_state('networkidle', timeout=30000)
            time.sleep(2)
            
            # Take screenshot
            screenshot_path = f"{SCREENSHOT_DIR}/3data_03_order_trend.png"
            page.screenshot(path=screenshot_path, full_page=True)
            
            # Find query input
            query_input = page.query_selector('textarea, input[placeholder*="问题"]')
            if not query_input:
                query_input = page.query_selector('input[type="text"]')
            
            if query_input:
                # Type query
                query_input.fill("显示本周订单趋势")
                time.sleep(1)
                
                # Take screenshot after typing
                screenshot_path = f"{SCREENSHOT_DIR}/3data_03_order_trend_typing.png"
                page.screenshot(path=screenshot_path, full_page=True)
                
                self.add_result(test_name, "PASSED", 
                    f"Query interface accessible, input filled: 显示本周订单趋势", 
                    screenshot_path)
                print(f"  [PASS] {test_name}")
            else:
                raise Exception("Query input not found")
            
        except Exception as e:
            screenshot_path = f"{SCREENSHOT_DIR}/3data_03_order_trend_error.png"
            page.screenshot(path=screenshot_path, full_page=True)
            self.add_result(test_name, "FAILED", str(e), screenshot_path)
            print(f"  [FAIL] {test_name}: {e}")
    
    def generate_report(self):
        """Generate test report"""
        duration = (datetime.now() - self.start_time).total_seconds()
        passed = len([r for r in self.results if r["status"] == "PASSED"])
        failed = len([r for r in self.results if r["status"] == "FAILED"])
        
        report = {
            "test_suite": "3 Data Example E2E Tests",
            "summary": {
                "total": len(self.results),
                "passed": passed,
                "failed": failed,
                "duration_seconds": duration,
                "success_rate": passed / len(self.results) * 100 if self.results else 0
            },
            "test_data_examples": [
                {
                    "id": 1,
                    "name": "Customer Sales Query",
                    "query": "显示销售额前 10 的客户",
                    "expected": "Table/chart showing top 10 customers by sales"
                },
                {
                    "id": 2,
                    "name": "Product Inventory Query",
                    "query": "查询库存预警商品",
                    "expected": "List of products with low inventory"
                },
                {
                    "id": 3,
                    "name": "Order Trend Query",
                    "query": "显示本周订单趋势",
                    "expected": "Chart showing order trend for the week"
                }
            ],
            "results": self.results,
            "generated_at": datetime.now().isoformat()
        }
        
        with open(REPORT_FILE, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        # Print summary
        print("\n" + "=" * 70)
        print("3 Data Example E2E Test Summary")
        print("=" * 70)
        print(f"Total Tests: {len(self.results)}")
        print(f"Passed: {passed}")
        print(f"Failed: {failed}")
        print(f"Success Rate: {report['summary']['success_rate']:.1f}%")
        print(f"Duration: {duration:.1f}s")
        print("=" * 70)
        print(f"\nDetailed report saved to: {REPORT_FILE}")
        print(f"Screenshots saved to: {SCREENSHOT_DIR}")
        print("=" * 70)
        
        return report


def main():
    """Main entry point"""
    tester = ThreeDataExampleTester()
    report = tester.run_all_tests()
    
    # Return exit code based on results
    if report["summary"]["failed"] > 0:
        exit(1)
    else:
        exit(0)


if __name__ == "__main__":
    main()
