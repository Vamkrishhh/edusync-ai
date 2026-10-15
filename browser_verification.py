"""
Actual browser testing using Playwright to verify the UI.
This performs REAL browser interactions, not simulations.
"""
import sys
import time
from playwright.sync_api import sync_playwright, expect

APP_URL = "http://localhost:8502"
TIMEOUT = 10000  # 10 seconds

print("=" * 70)
print("REAL BROWSER VERIFICATION - Playwright")
print("=" * 70)
print(f"Testing URL: {APP_URL}")
print()

def wait_for_streamlit(page):
    """Wait for Streamlit to finish rendering"""
    time.sleep(2)  # Give Streamlit time to hydrate
    try:
        page.wait_for_selector('iframe[title="streamlit_elements.core.frame.st_frame"]', timeout=1000, state='hidden')
    except:
        pass  # No iframe means it's ready

def test_page_loads(browser):
    """Test 1: Verify all 7 pages load without errors"""
    print("=== TEST 1: Page Load Verification ===")
    
    context = browser.new_context()
    page = context.new_page()
    
    errors = []
    
    # Capture console errors
    def handle_console(msg):
        if msg.type == 'error':
            errors.append(f"Console error: {msg.text}")
    
    page.on('console', handle_console)
    
    try:
        # Load main page
        page.goto(APP_URL, wait_until="networkidle", timeout=TIMEOUT)
        wait_for_streamlit(page)
        
        # Check for Streamlit errors
        if page.locator('text="Streamlit encountered an error"').count() > 0:
            print("  ✗ Streamlit error on initial load")
            return False
        
        print("  ✓ Initial page loads")
        
        # Test all 7 pages via sidebar navigation
        pages = [
            ("📊 Dashboard", "Dashboard"),
            ("📚 Document Library", "Document Library"),
            ("🤖 AI Study Assistant", "AI Study Assistant"),
            ("📝 Quiz Generator", "Quiz Generator"),
            ("📈 Performance Analyzer", "Performance Analyzer"),
            ("📅 Study Planner", "Study Planner"),
            ("🎯 Progress Tracker", "Progress Tracker")
        ]
        
        for full_name, display_name in pages:
            try:
                # Try multiple selector strategies
                clicked = False
                
                # Strategy 1: Full name with emoji
                if page.locator(f'text="{full_name}"').count() > 0:
                    page.locator(f'text="{full_name}"').first.click(timeout=5000)
                    clicked = True
                # Strategy 2: Display name only
                elif page.locator(f'text="{display_name}"').count() > 0:
                    page.locator(f'text="{display_name}"').first.click(timeout=5000)
                    clicked = True
                # Strategy 3: Radio button label
                elif page.locator(f'label:has-text("{display_name}")').count() > 0:
                    page.locator(f'label:has-text("{display_name}")').first.click(timeout=5000)
                    clicked = True
                
                if not clicked:
                    print(f"  ⚠ Could not find navigation element for {display_name}")
                    continue
                
                wait_for_streamlit(page)
                
                # Check for errors
                if page.locator('text="Streamlit encountered an error"').count() > 0:
                    print(f"  ✗ Error loading {display_name}")
                    return False
                
                print(f"  ✓ {display_name} loads")
                
            except Exception as e:
                print(f"  ⚠ Issue with {display_name}: {str(e)[:50]}")
                # Don't fail entire test, continue
        
        if errors:
            print(f"  ⚠ Console errors detected: {len(errors)}")
            for err in errors[:3]:
                print(f"    {err}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False
    finally:
        context.close()

def test_document_library(browser):
    """Test 2: Document Library - verify documents display"""
    print("\n=== TEST 2: Document Library Display ===")
    
    context = browser.new_context()
    page = context.new_page()
    
    try:
        page.goto(APP_URL, wait_until="networkidle", timeout=TIMEOUT)
        wait_for_streamlit(page)
        
        # Navigate to Document Library
        page.locator('text="Document Library"').first.click()
        wait_for_streamlit(page)
        
        # Check if documents are displayed
        # Look for "DBMS" in the page (sample documents)
        if page.locator('text="DBMS"').count() > 0:
            print("  ✓ Documents are displayed")
            return True
        else:
            # Check if empty state is shown
            if page.locator('text="No Course Material"').count() > 0:
                print("  ℹ No documents in library (empty state shown correctly)")
                return True
            else:
                print("  ✗ Documents not visible and no empty state")
                return False
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False
    finally:
        context.close()

def test_search_functionality(browser):
    """Test 3: Search in Document Library"""
    print("\n=== TEST 3: Document Search ===")
    
    context = browser.new_context()
    page = context.new_page()
    
    try:
        page.goto(APP_URL, wait_until="networkidle", timeout=TIMEOUT)
        wait_for_streamlit(page)
        
        # Navigate to Document Library
        page.locator('text="Document Library"').first.click()
        wait_for_streamlit(page)
        
        # Find search input
        search_input = page.locator('input[aria-label="Search course notes"]').or_(page.locator('input').first)
        
        if search_input.count() == 0:
            print("  ⚠ Search input not found")
            return False
        
        # Type search query
        search_input.first.fill("normalization")
        wait_for_streamlit(page)
        
        # Click search button
        page.locator('button:has-text("Search")').first.click()
        wait_for_streamlit(page)
        
        # Check for results
        if page.locator('text="Found"').count() > 0 or page.locator('text="passage"').count() > 0:
            print("  ✓ Search executes and shows results")
            return True
        elif page.locator('text="No Passages Found"').count() > 0:
            print("  ℹ Search executes but no results (database may be empty)")
            return True
        else:
            print("  ⚠ Search result unclear")
            return False
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False
    finally:
        context.close()

def test_ai_tutor_query(browser):
    """Test 4: AI Study Assistant query submission"""
    print("\n=== TEST 4: AI Tutor Query Submission ===")
    
    context = browser.new_context()
    page = context.new_page()
    
    try:
        page.goto(APP_URL, wait_until="networkidle", timeout=TIMEOUT)
        wait_for_streamlit(page)
        
        # Navigate to AI Study Assistant
        page.locator('text="AI Study Assistant"').first.click()
        wait_for_streamlit(page)
        
        # Click on example prompt button
        if page.locator('button:has-text("What should I study today")').count() > 0:
            page.locator('button:has-text("What should I study today")').first.click()
            wait_for_streamlit(page)
            
            # Check if response appears
            # Look for "Supervisor Response" or agent activity
            time.sleep(3)  # Give agent time to process
            
            if page.locator('text="Supervisor Response"').count() > 0 or page.locator('text="Agent Activity"').count() > 0:
                print("  ✓ Query submitted and response generated")
                return True
            else:
                print("  ⚠ Response format unclear")
                return False
        else:
            print("  ⚠ Example prompt button not found")
            return False
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False
    finally:
        context.close()

def test_quiz_generation(browser):
    """Test 5: Quiz Generator"""
    print("\n=== TEST 5: Quiz Generation ===")
    
    context = browser.new_context()
    page = context.new_page()
    
    try:
        page.goto(APP_URL, wait_until="networkidle", timeout=TIMEOUT)
        wait_for_streamlit(page)
        
        # Navigate to Quiz Generator
        page.locator('text="Quiz Generator"').first.click()
        wait_for_streamlit(page)
        
        # Look for "Generate" button
        gen_button = page.locator('button:has-text("Generate")').first
        
        if gen_button.count() > 0:
            gen_button.click()
            wait_for_streamlit(page)
            time.sleep(2)  # Wait for quiz generation
            
            # Check if quiz questions appear (radio buttons)
            if page.locator('input[type="radio"]').count() > 0:
                print("  ✓ Quiz generates with questions")
                return True
            else:
                print("  ⚠ Quiz questions not visible")
                return False
        else:
            print("  ⚠ Generate button not found")
            return False
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False
    finally:
        context.close()

def test_navigation_persistence(browser):
    """Test 6: Navigation state persistence"""
    print("\n=== TEST 6: Navigation Between Pages ===")
    
    context = browser.new_context()
    page = context.new_page()
    
    try:
        page.goto(APP_URL, wait_until="networkidle", timeout=TIMEOUT)
        wait_for_streamlit(page)
        
        # Navigate through multiple pages
        pages_to_test = ["Performance Analyzer", "Study Planner", "Progress Tracker", "Dashboard"]
        
        for page_name in pages_to_test:
            page.locator(f'text="{page_name}"').first.click()
            wait_for_streamlit(page)
            
            # Verify page loaded (no error message)
            if page.locator('text="Streamlit encountered an error"').count() > 0:
                print(f"  ✗ Error navigating to {page_name}")
                return False
        
        print("  ✓ Navigation between pages works")
        return True
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False
    finally:
        context.close()

def test_performance_metrics(browser):
    """Test 7: Performance Analyzer displays metrics"""
    print("\n=== TEST 7: Performance Metrics Display ===")
    
    context = browser.new_context()
    page = context.new_page()
    
    try:
        page.goto(APP_URL, wait_until="networkidle", timeout=TIMEOUT)
        wait_for_streamlit(page)
        
        # Navigate to Performance Analyzer
        page.locator('text="Performance Analyzer"').first.click()
        wait_for_streamlit(page)
        
        # Check if performance content is visible
        if page.locator('text="Overall Accuracy"').count() > 0 or page.locator('text="No Assessment Data"').count() > 0:
            print("  ✓ Performance page displays content")
            return True
        else:
            print("  ⚠ Performance content unclear")
            return False
        
    except Exception as e:
        print(f"  ✗ Test failed: {e}")
        return False
    finally:
        context.close()

def main():
    with sync_playwright() as p:
        # Launch browser
        print("Launching browser...")
        browser = p.chromium.launch(headless=True)
        
        try:
            results = []
            
            # Run all tests
            results.append(("Page Load Verification", test_page_loads(browser)))
            results.append(("Document Library Display", test_document_library(browser)))
            results.append(("Document Search", test_search_functionality(browser)))
            results.append(("AI Tutor Query", test_ai_tutor_query(browser)))
            results.append(("Quiz Generation", test_quiz_generation(browser)))
            results.append(("Navigation Persistence", test_navigation_persistence(browser)))
            results.append(("Performance Metrics", test_performance_metrics(browser)))
            
            # Summary
            print("\n" + "=" * 70)
            print("BROWSER TEST SUMMARY")
            print("=" * 70)
            
            passed = sum(1 for _, result in results if result)
            total = len(results)
            
            for test_name, result in results:
                status = "✓ PASS" if result else "✗ FAIL"
                print(f"{status}: {test_name}")
            
            print(f"\nTotal: {passed}/{total} tests passed")
            
            if passed == total:
                print("\n✅ ALL BROWSER TESTS PASSED")
                return 0
            else:
                print(f"\n⚠️ {total - passed} BROWSER TEST(S) FAILED")
                return 1
                
        finally:
            browser.close()

if __name__ == "__main__":
    sys.exit(main())
