# Vikrm AI Platform — Enterprise Autonomous Agent & DAG Workflow Engine

[![License: MIT](https://img.shields.io/badge/License-MIT-purple.svg)](https://mit-license.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=fastapi)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19.0+-61DAFB.svg?style=flat&logo=react)](https://reactjs.org)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7+-3178C6.svg?style=flat&logo=typescript)](https://www.typescriptlang.org)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-4479A1.svg?style=flat&logo=mysql)](https://www.mysql.com)

**Vikrm** is an enterprise-grade autonomous AI orchestration platform that enables teams to construct, execute, and monitor multi-agent graph workflows, multi-modal RAG knowledge bases, and real-time streaming LLM applications.

---

## 🌟 Primary Features

- ⚡ **Claude Code–Level Autonomous Software Engineering**: Dynamic multi-stage requirement understanding, stack inference, entity graph planning, dynamic LLM code synthesis without static template fallback, surgical incremental workspace edits, and automated pre-flight self-repair validation loops.
- 🤖 **Agent Studio**: Create, execute, and live-test autonomous personas with granular system prompt tuning, model selection, temperature control, and customizable avatars.
- ⚡ **Interactive DAG Workflow Builder**: Graph orchestration canvas powered by `@xyflow/react` featuring animated node creation, drag-and-drop handles, node minimap, connection previews, step execution timing, and live debugging output panels.
- 💬 **Streaming AI Chat**: Real-time SSE response streaming with typing indicator, GFM Markdown code highlighting, Web Speech API voice input, file attachments, and auto-title generation.
- 🧠 **Persistent Long-Term Memory**: Vector-backed semantic memory bank storing user preferences, facts, and conversation context across execution sessions.
- 📄 **Multi-Format Document RAG Vault**: Drag-and-drop upload supporting PDF, DOCX, TXT, CSV, and Markdown files with vector chunk indexing, category tagging, and in-app content preview drawer.
- 📊 **Executive Control Center Dashboard**: Live telemetry metrics displaying system health pulse, active agent count, team orchestration statistics, and recent activity cards.
- 🔐 **Enterprise Security & Auth**: Google OAuth 2.0 multi-tier verification, JWT token pair rotation, strict email format validation, rate limiting, CORS configuration, and security middleware.

---

## 📐 Clean Architecture

```
                                 ┌─────────────────────────────────┐
                                 │      React 19 + Vite Frontend   │
                                 │   Linear / Raycast Dark Glass   │
                                 └────────────────┬────────────────┘
                                                  │ REST / SSE
                                                  ▼
                                 ┌─────────────────────────────────┐
                                 │     FastAPI Async Backend API   │
                                 └────────┬────────────────┬───────┘
                                          │                │
                      ┌───────────────────┘                └───────────────────┐
                      ▼                                                        ▼
         ┌─────────────────────────┐                              ┌─────────────────────────┐
         │     Service Layer       │                              │  Repositories & Models  │
         │ (Agents, Workflows, RAG)│                              │  (User, Tokens, Memory) │
         └────────────┬────────────┘                              └────────────┬────────────┘
                      │                                                        │
                      ▼                                                        ▼
         ┌─────────────────────────┐                              ┌─────────────────────────┐
         │ Ollama / External LLMs  │                              │  MySQL 8.0 Database     │
         └─────────────────────────┘                              └─────────────────────────┘
```

---

## 💻 Tech Stack

### Backend & AI Infrastructure
- **Framework**: Python 3.11+ / FastAPI
- **ORM & Migrations**: SQLAlchemy 2.0 (Async) + Alembic
- **Database**: MySQL 8.0 (Async Drivers)
- **Vector Search / Embedding**: Sentence Transformers & ChromaDB / Cosine similarity
- **LLM Integration**: Ollama (local) & OpenAI/Anthropic/Gemini API abstraction layer
- **Testing**: `pytest` + `asyncio`

### Frontend Application
- **Framework**: React 19 + TypeScript + Vite
- **Styling**: Tailwind CSS + Vanilla CSS Custom Glassmorphism System
- **Animations**: Framer Motion
- **DAG Canvas**: React Flow (`@xyflow/react`)
- **State Management**: Zustand + React Query (`@tanstack/react-query`)

---

## 📂 Folder Structure

```
vikrm-final-complete/
├── backend/
│   ├── app/
│   │   ├── api/             # FastAPI Routers (v1: Auth, Agents, Workflows, Chat, Memory, Documents, Analytics)
│   │   ├── core/            # Config, Security, DB Connections, Logging
│   │   ├── models/          # SQLAlchemy DB Schema Models
│   │   ├── repositories/    # Data Access Layer Repositories
│   │   ├── schemas/         # Pydantic Request & Response Models
│   │   └── services/        # Service Layer Business Logic
│   ├── alembic/             # Database Migration Scripts
│   ├── tests/               # Backend PyTest Test Suite
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/      # Glassmorphic Reusable Components
│   │   │   └── workflow/    # Node Palette, Node Config, Canvas Nodes
│   │   ├── hooks/           # Custom React Query & API Hooks
│   │   ├── pages/           # Application Pages (Dashboard, Agents, Workflows, Chat, Memory, Documents, Settings, Admin)
│   │   ├── store/           # Zustand Auth & System State
│   │   ├── types/           # TypeScript Type Declarations
│   │   └── index.css        # Core Design System & Tokens
│   ├── index.html
│   ├── tailwind.config.js
│   └── vite.config.ts
├── docker-compose.yml       # Dev Environment Compose
├── docker-compose.prod.yml  # Production Docker Compose
└── README.md
```

---

## 🚀 Quick Start Guide

### Prerequisites
- **Node.js**: v18.0.0 or higher
- **Python**: v3.11 or higher
- **MySQL**: v8.0+
- **Ollama**: (Optional for local LLM inference)

---

### Environment Variables Setup

#### Backend `.env` (`backend/.env`)
```env
APP_ENV=development
JWT_SECRET_KEY=your-super-secret-jwt-signing-key
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=vikrm
MYSQL_PASSWORD=vikrm_password
MYSQL_DATABASE=vikrm

GOOGLE_CLIENT_ID=your-google-oauth-client-id.apps.googleusercontent.com
OLLAMA_BASE_URL=http://localhost:11434
```

#### Frontend `.env` (`frontend/.env`)
```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_GOOGLE_CLIENT_ID=your-google-oauth-client-id.apps.googleusercontent.com
```

---

### 📦 Installation & Local Execution

#### 1. Setup & Run Backend

```bash
cd backend
python -m venv venv

# On Windows:
.\venv\Scripts\activate

# Install dependencies:
pip install -r requirements.txt

# Run Database Migrations:
alembic upgrade head

# Start FastAPI Dev Server:
uvicorn app.main:app --reload --port 8000
```

The interactive API documentation is available at: `http://localhost:8000/docs`.

#### 2. Setup & Run Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend application runs at `http://localhost:5173`.

---

## 🐳 Docker Deployment

To launch the full stack environment via Docker Compose:

```bash
docker-compose up --build -d
```

---

## 🧪 Testing & Quality Assurance

### Run Backend Unit Tests

```bash
cd backend
.\venv\Scripts\pytest
```

### Run Frontend Type Check & Production Build

```bash
cd frontend
npm run build
```

---

## 🛠️ API & Workflow Overview

### Core Endpoint Summary

| Category | Endpoint | Method | Description |
| :--- | :--- | :--- | :--- |
| **Auth** | `/api/v1/auth/register` | `POST` | Email/password registration |
| **Auth** | `/api/v1/auth/login` | `POST` | Authenticate & return JWT token pair |
| **Auth** | `/api/v1/auth/google` | `POST` | Google OAuth token verification |
| **Agents** | `/api/v1/agents` | `GET/POST` | List and create autonomous agents |
| **Agents** | `/api/v1/agents/{id}/test` | `POST` | Execute agent persona live test |
| **Workflows** | `/api/v1/workflows` | `GET/POST` | Graph DAG definitions and execution |
| **Chat** | `/api/v1/conversations/{id}/messages/stream` | `POST` | Token-by-token SSE streaming completions |
| **Documents**| `/api/v1/documents/upload` | `POST` | RAG document parsing & chunk vectorization |

---

## 📄 License & Author

- **License**: MIT License
- **Author**: Vikrm Platform Engineering Team
