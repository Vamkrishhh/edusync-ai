"""
Capture live screenshots of EduSync AI pages using Playwright.
"""
import os
import time
from playwright.sync_api import sync_playwright

ARTIFACT_DIR = r"C:\Users\vamsi\.gemini\antigravity-ide\brain\dce2512a-fc54-44df-9021-1e2e0ab2b213"
os.makedirs(ARTIFACT_DIR, exist_ok=True)

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if not os.path.exists(EDGE_PATH):
    EDGE_PATH = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path=EDGE_PATH if os.path.exists(EDGE_PATH) else None,
            headless=True
        )
        page = browser.new_page(viewport={"width": 1440, "height": 960})
        
        # 1. Dashboard
        print("Navigating to Dashboard...")
        page.goto("http://localhost:8501", wait_until="networkidle", timeout=30000)
        time.sleep(3.0)
        dash_path = os.path.join(ARTIFACT_DIR, "preview_dashboard.png")
        page.screenshot(path=dash_path)
        print("Dashboard screenshot captured:", dash_path, os.path.getsize(dash_path))
        
        # 2. Document Library
        print("Navigating to Document Library...")
        try:
            doc_lib_radio = page.locator("text=📚 Document Library").first
            doc_lib_radio.click()
            time.sleep(2.0)
            doc_path = os.path.join(ARTIFACT_DIR, "preview_knowledge.png")
            page.screenshot(path=doc_path)
            print("Document library screenshot captured:", doc_path, os.path.getsize(doc_path))
        except Exception as e:
            print("Error navigating to doc lib:", e)

        # 3. AI Study Assistant
        print("Navigating to AI Study Assistant...")
        try:
            ai_radio = page.locator("text=🤖 AI Study Assistant").first
            ai_radio.click()
            time.sleep(2.0)
            ai_path = os.path.join(ARTIFACT_DIR, "preview_ai_agent.png")
            page.screenshot(path=ai_path)
            print("AI Assistant screenshot captured:", ai_path, os.path.getsize(ai_path))
        except Exception as e:
            print("Error navigating to AI assistant:", e)

        # 4. Study Planner
        print("Navigating to Study Planner...")
        try:
            planner_radio = page.locator("text=📅 Study Planner").first
            planner_radio.click()
            time.sleep(2.0)
            planner_path = os.path.join(ARTIFACT_DIR, "preview_planner.png")
            page.screenshot(path=planner_path)
            print("Study Planner screenshot captured:", planner_path, os.path.getsize(planner_path))
        except Exception as e:
            print("Error navigating to Study Planner:", e)

        browser.close()

if __name__ == "__main__":
    run()
