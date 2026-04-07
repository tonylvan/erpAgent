"""
GSD Platform Simple E2E Test
Quick browser automation test
"""
from playwright.sync_api import sync_playwright
import time
import os

FRONTEND_URL = "http://localhost:5183"
SCREENSHOT_DIR = "D:\\erpAgent\\tests\\screenshots"

def main():
    print("=" * 70)
    print("GSD Platform E2E Test")
    print("=" * 70)
    
    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=50)
        context = browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = context.new_page()
        
        # Test 1: Homepage
        print("\n[TEST] Homepage")
        try:
            page.goto(FRONTEND_URL, timeout=30000)
            page.wait_for_load_state('networkidle', timeout=30000)
            
            screenshot_path = f"{SCREENSHOT_DIR}/e2e_homepage.png"
            page.screenshot(path=screenshot_path, full_page=True)
            
            title = page.title()
            print(f"  Title: {title}")
            print(f"  Screenshot: {screenshot_path}")
            print("  [PASS] Homepage loaded")
        except Exception as e:
            print(f"  [FAIL] {e}")
        
        # Test 2: Smart Query Page
        print("\n[TEST] Smart Query")
        try:
            page.goto(f"{FRONTEND_URL}/smart-query", timeout=30000)
            page.wait_for_load_state('networkidle', timeout=30000)
            
            screenshot_path = f"{SCREENSHOT_DIR}/e2e_smartquery.png"
            page.screenshot(path=screenshot_path, full_page=True)
            
            print(f"  Screenshot: {screenshot_path}")
            print("  [PASS] Smart Query page loaded")
        except Exception as e:
            print(f"  [FAIL] {e}")
        
        # Test 3: Ticket Center
        print("\n[TEST] Ticket Center")
        try:
            page.goto(f"{FRONTEND_URL}/tickets", timeout=30000)
            page.wait_for_load_state('networkidle', timeout=30000)
            
            screenshot_path = f"{SCREENSHOT_DIR}/e2e_tickets.png"
            page.screenshot(path=screenshot_path, full_page=True)
            
            print(f"  Screenshot: {screenshot_path}")
            print("  [PASS] Ticket Center loaded")
        except Exception as e:
            print(f"  [FAIL] {e}")
        
        # Test 4: Alert Center
        print("\n[TEST] Alert Center")
        try:
            page.goto(f"{FRONTEND_URL}/alerts", timeout=30000)
            page.wait_for_load_state('networkidle', timeout=30000)
            
            screenshot_path = f"{SCREENSHOT_DIR}/e2e_alerts.png"
            page.screenshot(path=screenshot_path, full_page=True)
            
            print(f"  Screenshot: {screenshot_path}")
            print("  [PASS] Alert Center loaded")
        except Exception as e:
            print(f"  [FAIL] {e}")
        
        # Test 5: Knowledge Graph
        print("\n[TEST] Knowledge Graph")
        try:
            page.goto(f"{FRONTEND_URL}/graph", timeout=30000)
            page.wait_for_load_state('networkidle', timeout=30000)
            
            screenshot_path = f"{SCREENSHOT_DIR}/e2e_graph.png"
            page.screenshot(path=screenshot_path, full_page=True)
            
            print(f"  Screenshot: {screenshot_path}")
            print("  [PASS] Knowledge Graph loaded")
        except Exception as e:
            print(f"  [FAIL] {e}")
        
        browser.close()
    
    print("\n" + "=" * 70)
    print("E2E Test Complete")
    print("=" * 70)

if __name__ == "__main__":
    main()
