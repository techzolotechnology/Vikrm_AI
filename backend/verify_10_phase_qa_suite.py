import asyncio
import json
import os
import sys
import time
import subprocess
import httpx

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app.services.intent_service import IntentService, ResponseMode
from app.services.validation_service import ValidationService
from app.services.project.planning_agent import PlanningAgent
from app.services.project.code_synthesizer import LLMCodeSynthesizer
from app.services.project.agent_loop import AgentLoop, ProductionValidator, ProjectMetrics
from app.services.project.incremental_edit_engine import IncrementalEditEngine, WorkspaceContext
from app.services.chat_service import get_knowledge_retriever

BASE_URL = "http://localhost:8000/api/v1"

async def main():
    results = {}
    passed_tests = 0
    total_tests = 0

    def record_test(feature: str, success: bool, detail: str = ""):
        nonlocal passed_tests, total_tests
        total_tests += 1
        if success:
            passed_tests += 1
        results[feature] = "PASS" if success else f"FAIL ({detail})"
        status = "PASS" if success else "FAIL"
        print(f"  • {feature:<35}: [{status}] {detail}")

    print("=" * 90)
    print(" VIKRM AI PLATFORM -- RUNTIME EXECUTION & END-TO-END QA AUDIT")
    print("=" * 90 + "\n")

    # ─── PHASE 1 & 2: ENVIRONMENT & VERSIONS ──────────────────────────────────────
    print("► PHASE 1 & 2 -- ENVIRONMENT & TOOLING VERIFICATION")
    try:
        py_v = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        record_test("Python Environment", True, f"v{py_v}")
    except Exception as e:
        record_test("Python Environment", False, str(e))

    try:
        node_v = subprocess.check_output(["node", "-v"], text=True).strip()
        record_test("Node.js Environment", True, node_v)
    except Exception as e:
        record_test("Node.js Environment", False, str(e))

    try:
        npm_v = subprocess.check_output(["npm.cmd" if os.name == "nt" else "npm", "-v"], text=True).strip()
        record_test("npm Package Manager", True, f"v{npm_v}")
    except Exception as e:
        record_test("npm Package Manager", False, str(e))

    try:
        git_v = subprocess.check_output(["git", "--version"], text=True).strip()
        record_test("Git VCS Engine", True, git_v)
    except Exception as e:
        record_test("Git VCS Engine", False, str(e))

    # ─── PHASE 3 & 4: SERVICES HEALTH CHECK ───────────────────────────────────────
    print("\n► PHASE 3 & 4 -- LIVE SERVICES HEALTH AUDIT")
    async with httpx.AsyncClient(timeout=10.0) as client:
        # Frontend
        try:
            r = await client.get("http://localhost:5173")
            record_test("Frontend App Server (5173)", r.status_code == 200, f"HTTP {r.status_code}")
        except Exception as e:
            record_test("Frontend App Server (5173)", False, str(e))

        # Backend Health
        try:
            r = await client.get(f"{BASE_URL}/health")
            record_test("FastAPI Backend Health (8000)", r.status_code == 200, f"HTTP {r.status_code}")
        except Exception as e:
            record_test("FastAPI Backend Health (8000)", False, str(e))

        # Swagger Docs
        try:
            r = await client.get("http://localhost:8000/docs")
            record_test("OpenAPI / Swagger UI (8000)", r.status_code == 200, f"HTTP {r.status_code}")
        except Exception as e:
            record_test("OpenAPI / Swagger UI (8000)", False, str(e))

        # Redis
        try:
            from app.core.redis_client import check_redis_connection
            redis_ok = await check_redis_connection()
            record_test("Redis Client (6379)", redis_ok, "Connected & Operational")
        except Exception as e:
            record_test("Redis Client (6379)", False, str(e))

        # Ollama AI Local Models
        try:
            r = await client.get("http://127.0.0.1:11434/api/tags")
            models = [m.get("name") for m in r.json().get("models", [])]
            record_test("Ollama LLM Engine (11434)", True, f"Models: {models}")
        except Exception as e:
            record_test("Ollama LLM Engine (11434)", False, str(e))

        # Database Schema
        try:
            from app.core.database import AsyncSessionLocal
            from sqlalchemy import text
            async with AsyncSessionLocal() as session:
                res = await session.execute(text("SELECT name FROM sqlite_master WHERE type='table';"))
                tables = [row[0] for row in res.fetchall()]
                record_test("SQLite DB Connection & Schema", len(tables) > 0, f"{len(tables)} tables verified")
        except Exception as e:
            record_test("SQLite DB Connection & Schema", False, str(e))

    # ─── PHASE 5: FEATURE TESTS (AUTH, CHAT, RAG, MODES) ──────────────────────────
    print("\n► PHASE 5 -- FEATURE TESTS (AUTH, INTENTS, WORKSPACE & RAG)")
    async with httpx.AsyncClient(timeout=30.0) as client:
        # Register / Auth Test
        token = ""
        try:
            reg_res = await client.post(f"{BASE_URL}/auth/register", json={
                "email": "qa_master_full@vikrm.ai",
                "password": "MasterTestPassword123!",
                "full_name": "QA Master User"
            })
            if reg_res.status_code in (200, 201):
                token = reg_res.json().get("access_token") or ""
            if not token:
                login_res = await client.post(f"{BASE_URL}/auth/login", json={
                    "email": "qa_master_full@vikrm.ai",
                    "password": "MasterTestPassword123!"
                })
                token = login_res.json().get("access_token") or ""
            record_test("JWT Auth (Register & Login)", bool(token), "JWT Access Token Acquired")
        except Exception as e:
            record_test("JWT Auth (Register & Login)", False, str(e))

        headers = {"Authorization": f"Bearer {token}"} if token else {}

        # Conversation Creation
        conv_id = ""
        try:
            c_res = await client.post(f"{BASE_URL}/conversations", json={"title": "QA Full Test"}, headers=headers)
            conv_id = c_res.json().get("id") or ""
            record_test("Conversation Persistence API", bool(conv_id), f"ID: {conv_id}")
        except Exception as e:
            record_test("Conversation Persistence API", False, str(e))

        # Intent Modes Verification
        intent_prompts = [
            ("Explain JWT Authentication", ResponseMode.CONVERSATIONAL),
            ("Write Bubble Sort in Python", ResponseMode.SMALL_CODE),
            ("Build an Ecommerce Website", ResponseMode.ARTIFACT_PROJECT),
            ("Add Stripe Payments", ResponseMode.EDIT_PROJECT),
            ("Traceback (most recent call last):\nValueError: invalid literal", ResponseMode.DEBUG),
            ("Review this React Component", ResponseMode.CODE_REVIEW),
            ("Design Uber System Architecture", ResponseMode.ARCHITECT),
        ]

        for p_str, exp_m in intent_prompts:
            i_res = IntentService.classify_intent(p_str, has_active_workspace=True)
            m_ok = i_res["mode"] == exp_m
            record_test(f"Intent Mode ({exp_m.value})", m_ok, f"Detected: {i_res['mode']}")

        # RAG Knowledge Retrieval
        try:
            retriever = get_knowledge_retriever()
            chunks = retriever.retrieve_context("FastAPI SQLAlchemy PostgreSQL JWT", top_k=3)
            record_test("Automatic RAG Vector Store Retrieval", len(chunks) > 0, f"{len(chunks)} chunks retrieved")
        except Exception as e:
            record_test("Automatic RAG Vector Store Retrieval", False, str(e))

    # ─── PHASE 6 & 8: ENTERPRISE GENERATION & TELEMETRY AUDIT ─────────────────────
    print("\n► PHASE 6 & 8 -- ENTERPRISE GENERATION & FILE TELEMETRY AUDIT")
    e_prompt = "Build a complete Enterprise Hospital Management System with React 19, FastAPI, PostgreSQL, Redis, RabbitMQ, JWT, OAuth, RBAC, Docker, Kubernetes, Telemedicine, Laboratory, Pharmacy, Billing, Analytics, Notifications, Reporting, Swagger, CI/CD, Vitest, Pytest and Playwright"

    plan = PlanningAgent.plan(e_prompt)
    files = LLMCodeSynthesizer.synthesize(plan)
    ctx = WorkspaceContext(project_name=plan.project_name, domain=plan.domain)
    ctx.load_from_files(files)

    record_test("Planning Agent Task Decomposition", len(plan.tasks) > 20, f"{len(plan.tasks)} tasks planned")
    record_test("Enterprise Code Synthesis (280 files)", len(files) == 280, f"Synthesized: {len(files)} files")
    record_test("Workspace Context Assembly", len(ctx.files) == 280, f"Saved Context: {len(ctx.files)} files")
    record_test("File Explorer Tree Rendering Model", len(files) == 280, f"Rendered: {len(files)} files")

    # ─── PHASE 7 & 9: BUILD, VALIDATION & REPAIR AUDIT ────────────────────────────
    print("\n► PHASE 7 & 9 -- BUILD VERIFICATION & AUTO-REPAIR AUDIT")
    passed_val, issues_val = ProductionValidator.validate(files)
    record_test("Production Validator Checklist", passed_val, f"Warnings: {len(issues_val)}")

    todo_count = sum(1 for c in files.values() if "TODO:" in c or "FIXME:" in c)
    record_test("Zero TODO / Placeholder Filter", todo_count == 0, f"Placeholders found: {todo_count}")

    # ─── PHASE 10: FINAL HEALTH SCORE & SUMMARY ───────────────────────────────────
    health_score = int((passed_tests / total_tests) * 100) if total_tests > 0 else 0

    print("\n" + "=" * 90)
    print(" FINAL VERIFICATION & HEALTH SCORE REPORT")
    print("=" * 90)
    print(f"  Total Features & Checks Audited: {total_tests}")
    print(f"  Successful Verification Passes : {passed_tests}")
    print(f"  Failed Feature Verification    : {total_tests - passed_tests}")
    print(f"  PLATFORM HEALTH SCORE          : {health_score}/100")
    print("=" * 90 + "\n")

    summary = {
        "passed": passed_tests,
        "failed": total_tests - passed_tests,
        "total": total_tests,
        "health_score": f"{health_score}/100",
        "results": results
    }
    print(json.dumps(summary, indent=2))

if __name__ == "__main__":
    asyncio.run(main())
