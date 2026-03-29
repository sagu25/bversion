"""
TARE - Single-command launcher
Run: python run.py
Starts server, opens browser, then launches narrated demo automatically.
"""
import subprocess
import sys
import os
import socket
import webbrowser
import threading
import time

ROOT = os.path.dirname(os.path.abspath(__file__))

def find_free_port(start=8050, end=8100):
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    raise RuntimeError("No free port found between 8050 and 8100")

port = find_free_port()

print("=" * 55)
print("  TARE - Trusted Access Response Engine")
print("=" * 55)
print()
print(f"  Starting server on port {port}...")
print(f"  Browser will open at:  http://localhost:{port}")
print()
print("  Narrated demo will start automatically in 5 seconds.")
print("  Press Ctrl+C to stop.")
print()

def open_browser_and_narrate():
    time.sleep(3)
    webbrowser.open(f"http://localhost:{port}")
    time.sleep(4)  # give browser time to load
    narrate_script = os.path.join(ROOT, "narrate.py")
    if os.path.exists(narrate_script):
        subprocess.Popen([sys.executable, narrate_script])

threading.Thread(target=open_browser_and_narrate, daemon=True).start()

os.chdir(os.path.join(ROOT, "backend"))
subprocess.run([
    sys.executable, "-m", "uvicorn",
    "main:app",
    "--port", str(port),
    "--host", "0.0.0.0",
], check=True)
