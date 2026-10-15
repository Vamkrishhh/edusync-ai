"""
Quick browser verification - essential UI checks only
"""
import sys
import time
from playwright.sync_api import sync_playwright

APP_URL = "http://localhost:8502"

print("=" * 60)
print("QUICK BROWSER VERIFICATION")
print("=" * 60)
print(f"URL: {APP_URL}\n")

def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Test 1: Can we load the app?
            print("1. Loading application...")
            page.goto(APP_URL, wait_until="networkidle", timeout=15000)
            time.sleep(3)  # Wait for Streamlit hydration
            
            if "EduSync" in page.content():
                print("   ✓ Application loads and renders")
            else:
                print("   ✗ Application content not found")
                return 1
            
            # Test 2: Check for fatal errors
            print("\n2. Checking for errors...")
            if "error" in page.content().lower() and "streamlit encountered an error" in page.content().lower():
                print("   ✗ Streamlit error detected")
                return 1
            else:
                print("   ✓ No fatal errors visible")
            
            # Test 3: Check key UI elements exist
            print("\n3. Checking UI elements...")
            
            # Sidebar should exist
            if page.locator('[data-testid="stSidebar"]').count() > 0:
                print("   ✓ Sidebar present")
            else:
                print("   ⚠ Sidebar not detected")
            
            # Some navigation options should be visible
            page_content = page.content()
            nav_found = 0
            for nav_item in ["Dashboard", "Document", "Quiz", "Performance", "Study", "Progress"]:
                if nav_item in page_content:
                    nav_found += 1
            
            if nav_found >= 4:
                print(f"   ✓ Navigation items visible ({nav_found}/6)")
            else:
                print(f"   ⚠ Few navigation items found ({nav_found}/6)")
            
            # Test 4: Screenshot capability
            print("\n4. Visual verification...")
            try:
                page.screenshot(path="app_screenshot.png", full_page=True)
                print("   ✓ Screenshot saved: app_screenshot.png")
                print("   ℹ Manual visual inspection recommended")
            except Exception as e:
                print(f"   ⚠ Screenshot failed: {e}")
            
            # Test 5: Check for content
            print("\n5. Content verification...")
            
            keywords = ["EduSync", "Multi-Tool", "SDG"]
            found_keywords = sum(1 for kw in keywords if kw in page_content)
            
            if found_keywords >= 2:
                print(f"   ✓ Expected content present ({found_keywords}/3 keywords)")
            else:
                print(f"   ⚠ Limited content detected ({found_keywords}/3 keywords)")
            
            print("\n" + "=" * 60)
            print("RESULT: Basic browser functionality confirmed ✓")
            print("=" * 60)
            print("\nNOTE: This confirms the app loads and renders.")
            print("Full interaction testing requires manual verification.")
            print("Screenshot saved for visual inspection.")
            
            return 0
            
        except Exception as e:
            print(f"\n✗ Browser test failed: {e}")
            return 1
        finally:
            browser.close()

if __name__ == "__main__":
    sys.exit(main())
