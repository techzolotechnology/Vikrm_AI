"""
Platform Service Launcher & Health Check.
Spawns Redis, Ollama, FastAPI Backend, and React/Vite Frontend as persistent independent background processes on Windows.
"""
import os
import sys
import time
import subprocess
import urllib.request
import json

backend_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(backend_dir, ".."))
frontend_dir = os.path.join(root_dir, "frontend")
python_exe = sys.executable

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0

def start_services():
    print("=" * 80)
    print(" LAUNCHING ALL VIKRM AI PLATFORM SERVICES")
    print("=" * 80)

    # 1. Redis
    print("\n[1/4] Starting Redis Server...")
    try:
        subprocess.Popen(["redis-server.exe"], cwd=root_dir, creationflags=CREATE_NO_WINDOW)
        print("  -> Redis process spawned.")
    except Exception as e:
        print(f"  -> Redis launch error: {e}")

    time.sleep(2)

    # 2. Ollama
    print("\n[2/4] Starting Ollama Serve...")
    try:
        subprocess.Popen(["ollama", "serve"], cwd=root_dir, creationflags=CREATE_NO_WINDOW)
        print("  -> Ollama process spawned.")
    except Exception as e:
        print(f"  -> Ollama launch error: {e}")

    time.sleep(2)

    # 3. FastAPI Backend
    print("\n[3/4] Starting FastAPI Backend (port 8000)...")
    try:
        subprocess.Popen(
            [python_exe, "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
            cwd=backend_dir,
            creationflags=CREATE_NO_WINDOW
        )
        print("  -> FastAPI Backend process spawned.")
    except Exception as e:
        print(f"  -> FastAPI Backend launch error: {e}")

    time.sleep(3)

    # 4. Vite Frontend
    print("\n[4/4] Starting React/Vite Frontend (port 5173)...")
    try:
        npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
        subprocess.Popen(
            [npm_cmd, "run", "dev"],
            cwd=frontend_dir,
            creationflags=CREATE_NO_WINDOW
        )
        print("  -> Vite Frontend process spawned.")
    except Exception as e:
        print(f"  -> Vite Frontend launch error: {e}")

    print("\nWaiting 6 seconds for services to complete initialization...")
    time.sleep(6)

def check_endpoints():
    print("\n" + "=" * 80)
    print(" VERIFYING SERVICE HEALTH ENDPOINTS")
    print("=" * 80)

    endpoints = [
        ("FastAPI Health Check", "http://localhost:8000/api/v1/health"),
        ("Swagger OpenAPI Docs", "http://localhost:8000/docs"),
        ("Ollama Models API", "http://127.0.0.1:11434/api/tags"),
        ("React/Vite Frontend", "http://localhost:5173"),
    ]

    results = {}
    for name, url in endpoints:
        status = "FAILED"
        for _ in range(5):
            try:
                req = urllib.request.urlopen(url, timeout=3)
                if req.getcode() == 200:
                    status = "HTTP 200 OK"
                    break
                else:
                    status = f"HTTP {req.getcode()}"
            except Exception:
                time.sleep(2)
        results[name] = status
        print(f"  [{'✓' if '200' in status else '❌'}] {name} ({url}) -> {status}")

    print("\n--- Redis Connection Check ---")
    try:
        res = subprocess.run(["redis-cli", "ping"], capture_output=True, text=True, timeout=3)
        if "PONG" in res.stdout:
            print("  [✓] Redis PING -> PONG")
            results["Redis PING"] = "PONG"
        else:
            print(f"  [❌] Redis PING output: {res.stdout.strip()}")
            results["Redis PING"] = res.stdout.strip()
    except Exception as e:
        print(f"  [❌] Redis PING failed: {e}")
        results["Redis PING"] = f"Failed: {e}"

    return results

if __name__ == "__main__":
    start_services()
    res = check_endpoints()
    print("\n" + "=" * 80)
    print(" INITIALIZATION SUMMARY")
    print("=" * 80)
    print(json.dumps(res, indent=2))
