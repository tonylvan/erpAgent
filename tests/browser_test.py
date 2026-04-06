"""
GSD Platform Browser Test Script
Tests the GSD web application using Playwright
"""
from playwright.sync_api import sync_playwright
import time
import os

def test_gsd_platform():
    """Test GSD platform functionality"""
    
    print("Starting GSD Platform Browser Test...")
    print("=" * 60)
    
    with sync_playwright() as p:
        # Launch browser
        print("\nLaunching browser...")
        browser = p.chromium.launch(headless=False, slow_mo=500)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()
        
        # Test 1: Access GSD homepage
        print("\nTesting homepage access...")
        url = "http://localhost:5180"
        page.goto(url, timeout=30000)
        page.wait_for_load_state('networkidle')
        
        # Take screenshot
        screenshot_path = "D:\\erpAgent\\tests\\screenshots\\01_homepage.png"
        os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot saved: {screenshot_path}")
        
        # Check for page title
        title = page.title()
        print(f"Page title: {title}")
        
        # Check for Vue app mount
        print("\nChecking Vue application...")
        try:
            # Wait for app to mount
            page.wait_for_selector('#app', timeout=5000)
            print("Vue app mounted successfully")
        except Exception as e:
            print(f"Vue app mount failed: {e}")
        
        # Test 2: Check for navigation elements
        print("\nChecking navigation elements...")
        nav_selectors = [
            ('Alert Center', '.top-nav'),
            ('Smart Query', '[href*="smart-query"]'),
            ('Knowledge Graph', '[href*="graph"]'),
        ]
        
        for name, selector in nav_selectors:
            try:
                element = page.query_selector(selector)
                if element:
                    print(f"{name}: Found")
                else:
                    print(f"{name}: Not found (selector: {selector})")
            except Exception as e:
                print(f"{name}: Error - {e}")
        
        # Test 3: Check for statistics cards
        print("\nChecking statistics cards...")
        card_selectors = [
            ('Critical Card', '.critical-card'),
            ('High Card', '.warning-card'),
            ('Medium Card', '.info-card'),
            ('Low Card', '.success-card'),
        ]
        
        for name, selector in card_selectors:
            try:
                element = page.query_selector(selector)
                if element:
                    print(f"{name}: Found")
                else:
                    print(f"{name}: Not found")
            except Exception as e:
                print(f"{name}: Error - {e}")
        
        # Test 4: Check console for errors
        print("\nChecking browser console...")
        console_messages = []
        page.on('console', lambda msg: console_messages.append({
            'type': msg.type,
            'text': msg.text
        }))
        
        # Reload to capture console messages
        page.reload(wait_until='networkidle')
        time.sleep(2)
        
        errors = [m for m in console_messages if m['type'] == 'error']
        if errors:
            print(f"Found {len(errors)} console error(s):")
            for error in errors[:5]:  # Show first 5 errors
                print(f"   - {error['type']}: {error['text'][:200]}")
        else:
            print("No console errors found")
        
        # Test 5: Check for CORS errors
        print("\nChecking for CORS errors...")
        cors_errors = [m for m in errors if 'CORS' in m['text'] or 'Access-Control' in m['text']]
        if cors_errors:
            print(f"Found {len(cors_errors)} CORS error(s)")
            for error in cors_errors:
                print(f"   - {error['text'][:300]}")
        else:
            print("No CORS errors found")
        
        # Take final screenshot
        final_screenshot = "D:\\erpAgent\\tests\\screenshots\\02_final.png"
        page.screenshot(path=final_screenshot, full_page=True)
        print(f"\nFinal screenshot saved: {final_screenshot}")
        
        # Close browser
        browser.close()
        
        print("\n" + "=" * 60)
        print("GSD Platform Browser Test Complete!")
        print("=" * 60)
        
        # Summary
        print("\nTest Summary:")
        has_app = bool(page.query_selector('#app'))
        has_nav = bool(page.query_selector('.top-nav'))
        print(f"   - Homepage: {'OK' if title else 'FAIL'}")
        print(f"   - Vue App: {'OK' if has_app else 'FAIL'}")
        print(f"   - Navigation: {'OK' if has_nav else 'FAIL'}")
        print(f"   - Console Errors: {'FAIL' if errors else 'OK'}")
        print(f"   - CORS Errors: {'FAIL' if cors_errors else 'OK'}")

if __name__ == "__main__":
    test_gsd_platform()
