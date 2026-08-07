"""
Daemon script to start all platform services and keep them alive in background.
"""
import subprocess
import sys
import time
import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.abspath(os.path.join(backend_dir, ".."))
frontend_dir = os.path.join(root_dir, "frontend")
python_exe = sys.executable

print("Starting persistent services...")

# 1. Start Redis
p_redis = subprocess.Popen(["redis-server.exe"], cwd=root_dir)
print("Started Redis daemon.")

# 2. Start Ollama
p_ollama = subprocess.Popen(["ollama", "serve"], cwd=root_dir)
print("Started Ollama daemon.")

# 3. Start Backend Uvicorn
p_backend = subprocess.Popen([python_exe, "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"], cwd=backend_dir)
print("Started Backend Uvicorn daemon on port 8000.")

# 4. Start Frontend Vite
npm_cmd = "npm.cmd" if os.name == "nt" else "npm"
p_frontend = subprocess.Popen([npm_cmd, "run", "dev"], cwd=frontend_dir)
print("Started Frontend Vite daemon on port 5173.")

print("All processes launched. Entering keep-alive daemon loop...")

try:
    while True:
        time.sleep(10)
except KeyboardInterrupt:
    print("Stopping daemon services...")
    p_backend.terminate()
    p_frontend.terminate()
    p_ollama.terminate()
    p_redis.terminate()
