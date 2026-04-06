"""
Test GSD Alert Center using Playwright
"""
import asyncio
import sys
import os

# Set UTF-8 encoding
sys.stdout.reconfigure(encoding='utf-8')

from playwright.async_api import async_playwright

async def test_alert_center():
    print("=" * 60)
    print("GSD Alert Center Browser Test")
    print("=" * 60)
    
    async with async_playwright() as p:
        # Launch browser
        print("\n[1/5] Launching browser...")
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = await context.new_page()
        
        # Enable console log capture
        console_logs = []
        page.on('console', lambda msg: console_logs.append(f"[{msg.type}] {msg.text}"))
        page.on('pageerror', lambda err: console_logs.append(f"[ERROR] {err}"))
        
        # Navigate to Alert Center
        print("[2/5] Navigating to http://localhost:5180...")
        response = await page.goto('http://localhost:5180', wait_until='networkidle')
        print(f"     Status: {response.status}")
        
        # Wait for Vue app to mount
        print("[3/5] Waiting for Vue app to mount...")
        await page.wait_for_timeout(3000)
        
        # Check for errors
        print("[4/5] Checking for errors...")
        errors = [log for log in console_logs if 'error' in log.lower() or 'failed' in log.lower()]
        
        if errors:
            print("\n[WARN] ERRORS FOUND:")
            for error in errors[:10]:
                print(f"   {error}")
        else:
            print("   [OK] No errors detected")
        
        # Check page content
        print("\n[5/5] Checking page content...")
        
        # Check if Vue app mounted
        vue_app = await page.query_selector('#app')
        if vue_app:
            print("   [OK] Vue app mounted")
        else:
            print("   [FAIL] Vue app NOT mounted")
        
        # Check for Alert Center title
        alert_title = await page.query_selector('text=Alert Center')
        if alert_title:
            print("   [OK] Alert Center title found")
        else:
            print("   [WARN] Alert Center title NOT found")
        
        # Check for statistics cards
        stats_cards = await page.query_selector('.stats-cards')
        if stats_cards:
            print("   [OK] Statistics cards found")
        else:
            print("   [WARN] Statistics cards NOT found")
        
        # Take screenshot
        print("\n[INFO] Taking screenshot...")
        await page.screenshot(path='D:\\erpAgent\\tests\\screenshots\\alert-center-test.png', full_page=True)
        print("   Screenshot saved to: D:\\erpAgent\\tests\\screenshots\\alert-center-test.png")
        
        # Show console logs
        print("\n" + "=" * 60)
        print("CONSOLE LOGS (first 20):")
        print("=" * 60)
        for log in console_logs[:20]:
            print(log)
        
        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        print(f"Page Status: {response.status}")
        print(f"Vue App: {'[OK] Mounted' if vue_app else '[FAIL] Not Mounted'}")
        print(f"Errors: {len(errors)} found")
        print(f"Console Logs: {len(console_logs)} total")
        
        await browser.close()
        
        return len(errors) == 0

if __name__ == "__main__":
    success = asyncio.run(test_alert_center())
    print("\n" + ("=" * 60))
    if success:
        print("[PASS] TEST PASSED - No critical errors")
    else:
        print("[FAIL] TEST FAILED - Errors detected")
    print("=" * 60)
