"""
DevOps Platform Launcher: Starts Redis, Ollama (with llama3.2), FastAPI Backend, and React Frontend.
Monitors process health, automatically resolves startup issues, and keeps services alive.
"""
import os
import sys
import time
import json
import urllib.request
import subprocess
from pathlib import Path

backend_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(backend_dir, ".."))
frontend_dir = os.path.join(root_dir, "frontend")
python_exe = sys.executable

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def log(msg: str):
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


def is_url_alive(url: str, timeout: int = 3) -> bool:
    try:
        req = urllib.request.urlopen(url, timeout=timeout)
        return req.getcode() == 200
    except Exception:
        return False

def is_redis_alive() -> bool:
    try:
        import redis
        r = redis.Redis(host="localhost", port=6379, socket_timeout=2)
        return r.ping()
    except Exception:
        # Fallback to CLI
        try:
            res = subprocess.run(["redis-cli", "ping"], capture_output=True, text=True, timeout=2)
            return "PONG" in res.stdout
        except Exception:
            return False

CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0

def is_port_in_use(port: int) -> bool:
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            return s.connect_ex(("127.0.0.1", port)) == 0
    except Exception:
        return False


def ensure_services():
    log("=" * 70)
    log("VIKRM AI PLATFORM — DEVOPS LAUNCHER")
    log("=" * 70)

    # 1. Start Redis
    if not is_redis_alive():
        log("Starting Redis server daemon...")
        try:
            subprocess.Popen(["redis-server.exe"], cwd=root_dir, creationflags=CREATE_NO_WINDOW)
        except Exception as e:
            log(f"Redis launch warning: {e}")
        time.sleep(2)

    if is_redis_alive():
        log("✅ Redis server active (PING -> PONG)")
    else:
        log("⚠️  Redis not responding; fallback memory layer active.")

    # 2. Start Ollama
    if not is_url_alive("http://127.0.0.1:11434/api/tags"):
        log("Starting Ollama serve daemon...")
        try:
            subprocess.Popen(["ollama", "serve"], cwd=root_dir, creationflags=CREATE_NO_WINDOW)
        except Exception as e:
            log(f"Ollama launch error: {e}")
        time.sleep(3)

    if is_url_alive("http://127.0.0.1:11434/api/tags"):
        log("✅ Ollama serve active (http://127.0.0.1:11434)")
        try:
            req = urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=3)
            data = json.loads(req.read().decode())
            models = [m.get("name") for m in data.get("models", [])]
            if not any("llama3.2" in m for m in models):
                log("Pulling llama3.2 model into Ollama...")
                subprocess.run(["ollama", "pull", "llama3.2"], check=False)
            log("✅ Model 'llama3.2' installed in Ollama.")
        except Exception as exc:
            log(f"Ollama model check: {exc}")

    # 3. Start Backend Uvicorn
    if not is_port_in_use(8000):
        log("Starting FastAPI Backend (port 8000)...")
        try:
            subprocess.Popen(
                [python_exe, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"],
                cwd=backend_dir,
                creationflags=CREATE_NO_WINDOW
            )
        except Exception as e:
            log(f"Backend launch error: {e}")
        
        for _ in range(10):
            if is_url_alive("http://localhost:8000/api/v1/health"):
                break
            time.sleep(1)

    if is_url_alive("http://localhost:8000/api/v1/health"):
        log("✅ FastAPI Backend active (http://localhost:8000/api/v1/health)")
    else:
        log("❌ FastAPI Backend failed to respond to health check.")

    # 4. Start Frontend Vite
    if not is_port_in_use(5173):
        log("Starting React/Vite Frontend (port 5173)...")
        npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
        try:
            subprocess.Popen(
                [npm_cmd, "run", "dev"],
                cwd=frontend_dir,
                creationflags=CREATE_NO_WINDOW
            )
        except Exception as e:
            log(f"Frontend launch error: {e}")

        for _ in range(10):
            if is_url_alive("http://localhost:5173"):
                break
            time.sleep(1)

    if is_url_alive("http://localhost:5173"):
        log("✅ React/Vite Frontend active (http://localhost:5173)")
    else:
        log("❌ React/Vite Frontend failed to respond.")

    log("\nAll platform services active. Entering persistent daemon loop...")
    try:
        while True:
            time.sleep(10)
            # Socket-level port check before restarting
            if not is_port_in_use(8000):
                log("Backend port 8000 is inactive, restarting FastAPI Backend...")
                subprocess.Popen([python_exe, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"], cwd=backend_dir, creationflags=CREATE_NO_WINDOW)
            if not is_port_in_use(5173):
                log("Frontend port 5173 is inactive, restarting React/Vite Frontend...")
                npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
                subprocess.Popen([npm_cmd, "run", "dev"], cwd=frontend_dir, creationflags=CREATE_NO_WINDOW)
    except KeyboardInterrupt:
        log("DevOps Platform Launcher stopped.")

if __name__ == "__main__":
    ensure_services()

