import os, sys, threading, urllib.request, time

DB_PATH = "/app/data/master_v2.db"
URL = "https://github.com/sachinparamita-collab/meridian-api/releases/download/v0.1.0-data/master_v2.db"

def download_db():
    os.makedirs("/app/data", exist_ok=True)
    if not os.path.exists(DB_PATH) or os.path.getsize(DB_PATH) < 1_000_000:
        print("Downloading master_v2.db...", flush=True)
        urllib.request.urlretrieve(URL, DB_PATH)
        print(f"Download complete: {os.path.getsize(DB_PATH)/1024/1024:.1f} MB", flush=True)
    else:
        print(f"master_v2.db ready: {os.path.getsize(DB_PATH)/1024/1024:.1f} MB", flush=True)

t = threading.Thread(target=download_db, daemon=False)
t.start()

import subprocess
port = os.environ.get("PORT", "8000")
proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", port])
t.join()
proc.wait()