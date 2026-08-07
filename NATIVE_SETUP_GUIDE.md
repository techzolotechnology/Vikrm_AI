# Native Windows Development Guide — Vikrm AI Platform

This guide outlines step-by-step instructions to run the **Vikrm AI Platform** natively on Windows without Docker.

---

## 🛠️ Required Software & Versions

| Tool | Minimum Version | Installation / Verification Command |
| :--- | :--- | :--- |
| **Python** | 3.11+ / 3.12 | `python --version` |
| **Node.js** | LTS (v18.0+) | `node -v` |
| **npm** | 9.0+ | `npm -v` |
| **MySQL** | 8.0+ | `sc.exe query MySQL80` |
| **Redis** | 5.0+ / 8.0+ | `redis-server --version` |
| **Ollama** | Latest Windows | `ollama --version` |
| **Git** | 2.40+ | `git --version` |
| **VS Code** | Latest | `code --version` |

---

## ⚙️ Environment Configuration

### Backend `.env` (`backend/.env`)

```env
APP_NAME=Vikrm
APP_VERSION=0.1.0
ENVIRONMENT=development
DEBUG=true

HOST=0.0.0.0
PORT=8000

CORS_ORIGINS=["http://localhost:5173","http://localhost:3000"]

# Database Option A: Native MySQL 8.0
USE_SQLITE=false
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=vikrm
MYSQL_PASSWORD=vikrm_password
MYSQL_DATABASE=vikrm

# Database Option B: Zero-Dependency Native SQLite
# USE_SQLITE=true

# Redis Cache & Celery Task Queue
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Security
JWT_SECRET_KEY=6huYjFIVcsmvAQebSBHpLnOPzqDlw47KG8M9X25f3gxaZrydtCNioEUkTRJ1W0
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Local LLM Integration
OLLAMA_BASE_URL=http://localhost:11434
DEFAULT_LLM_PROVIDER=ollama
DEFAULT_LLM_MODEL=llama3.2

# Vector Store / RAG Embeddings
CHROMA_PERSIST_DIR=./data/chroma
EMBEDDING_PROVIDER=sentence-transformers
EMBEDDING_MODEL=all-MiniLM-L6-v2
MEMORY_SEARCH_TOP_K=3
```

### Frontend `.env` (`frontend/.env`)

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_GOOGLE_CLIENT_ID=305006751516-r4a0m83b9u6nbliler1r5ha1uth3i077.apps.googleusercontent.com
```

---

## 🚀 How to Run Native Services

### 1. Verification Commands for Services

#### Verify Native Database (MySQL / SQLite)
```bash
# Check MySQL Windows service:
Get-Service MySQL80

# Test connection via Python:
python -c "import pymysql; print(pymysql.connect(host='localhost', user='vikrm', password='vikrm_password', database='vikrm'))"
```

#### Verify Native Redis
```bash
# Start Redis server:
redis-server

# Test ping response in another prompt:
python -c "import redis; print(redis.Redis(host='localhost', port=6379).ping())"
```

#### Verify Native Ollama
```bash
# Start Ollama server (or run Ollama Windows tray app):
ollama serve

# Pull default Llama model:
ollama pull llama3.2
```

---

## 💻 Starting the Application Stack

### Step 1: Run Database Migrations
```bash
cd backend
.\venv\Scripts\activate
python -m alembic upgrade head
```

### Step 2: Start Backend FastAPI Server
```bash
cd backend
.\venv\Scripts\activate
python -m uvicorn app.main:app --reload --port 8000
```
- Interactive API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

### Step 3: Start Frontend Dev Server
```bash
cd frontend
npm run dev
```
- Web Application: [http://localhost:5173](http://localhost:5173)

---

## 🧪 Testing Checklist

```bash
# Run full backend test suite:
cd backend
.\venv\Scripts\pytest

# Run full system audit:
python run_full_system_audit.py

# Verify frontend build:
cd frontend
npm run build
```
