import subprocess
import time
import os

url = "https://project-52b2fab8-15a1-4b66-9f3.web.app/"
output = "ui_snapshot_ready.png"

print(f"Starting browser for {url}...")
# Wir nutzen chromium headless und geben ihm Zeit
process = subprocess.Popen([
    "chromium", "--headless", "--disable-gpu", "--no-sandbox",
    f"--screenshot={output}", "--window-size=1280,1024",
    "--virtual-time-budget=10000", # Simuliert 10 Sekunden Wartezeit für JS
    url
])

time.sleep(12) # Sicherheitspuffer
if os.path.exists(output):
    print(f"SUCCESS: Screenshot saved to {output}")
else:
    print("FAILED: No screenshot created.")
