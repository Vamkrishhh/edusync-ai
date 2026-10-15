import os
import sys
import time
import json
import asyncio
import subprocess
import urllib.request
import base64
import websockets

ARTIFACT_DIR = r"C:\Users\vamsi\.gemini\antigravity-ide\brain\dce2512a-fc54-44df-9021-1e2e0ab2b213"
OUTPUT_FILE = os.path.join(ARTIFACT_DIR, "edusync_preview.png")

EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
if not os.path.exists(EDGE_PATH):
    EDGE_PATH = r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"

PORT = 9223

async def capture():
    proc = subprocess.Popen([
        EDGE_PATH,
        "--headless=new",
        "--disable-gpu",
        f"--remote-debugging-port={PORT}",
        "--window-size=1400,950",
        "http://localhost:8501"
    ])
    
    # Wait for browser and Streamlit app to fully initialize
    await asyncio.sleep(4.0)
    
    try:
        with urllib.request.urlopen(f"http://localhost:{PORT}/json", timeout=5) as r:
            targets = json.loads(r.read().decode())
        
        ws_url = targets[0]["webSocketDebuggerUrl"]
        print("Connected to target:", ws_url)
        
        async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
            # Let Streamlit finish rendering widgets & styles
            await asyncio.sleep(2.0)
            
            # Send screenshot command
            msg_id = 1
            await ws.send(json.dumps({
                "id": msg_id,
                "method": "Page.captureScreenshot",
                "params": {"format": "png"}
            }))
            
            while True:
                resp = await ws.recv()
                data = json.loads(resp)
                if data.get("id") == msg_id:
                    img_data = base64.b64decode(data["result"]["data"])
                    with open(OUTPUT_FILE, "wb") as f:
                        f.write(img_data)
                    print(f"Screenshot successfully saved to {OUTPUT_FILE} ({len(img_data)} bytes)")
                    break
    finally:
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    asyncio.run(capture())
