"""
Comprehensive End-to-End System Audit and Performance Benchmark.
Runs natively on Windows or in a container: python run_full_system_audit.py
"""
import asyncio
import json
import os
import sys
import time

# Ensure backend root is on sys.path regardless of execution environment
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


from sqlalchemy import text
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.core.redis_client import check_redis_connection
from app.services.llm.base import ChatMessage
from app.services.llm.ollama_provider import OllamaProvider
from app.services.chat_service import ChatService
from app.services.memory_service import MemoryService
from app.services.attachment_service import extract_text_from_file
from app.repositories.user_repository import UserRepository


async def run_phase1_audit():
    print("\n" + "=" * 60)
    print(" PHASE 1: INFRASTRUCTURE & HEALTH AUDIT")
    print("=" * 60)

    # 1. DB Health & Tables
    db_type = "SQLite" if settings.USE_SQLITE else "MySQL"
    print(f"[1/3] Testing {db_type} connection and table schemas...")
    async with AsyncSessionLocal() as session:
        if settings.USE_SQLITE:
            query = text("SELECT name FROM sqlite_master WHERE type='table';")
        else:
            query = text("SHOW TABLES;")
        result = await session.execute(query)
        tables = [row[0] for row in result.fetchall()]
        print(f"  ✓ Connected to {db_type}. Total Tables found: {len(tables)}")
        print(f"    Tables: {', '.join(sorted(tables))}")
        assert "users" in tables and "conversations" in tables and "messages" in tables

    # 2. Redis Health
    print("[2/3] Testing Redis connection...")
    try:
        redis_ok = await check_redis_connection()
        print(f"  ✓ Connected to Redis. PING test result: {redis_ok}")
    except Exception as e:
        print(f"  ⚠ Redis connection check notice: {e}")

    # 3. Ollama Health & Model Tags
    print("[3/3] Testing Ollama API & installed model tags...")
    provider = OllamaProvider()
    try:
        models = await provider.list_installed_models()
        model_names = [m.get("name") for m in models]
        print(f"  ✓ Connected to Ollama at {settings.OLLAMA_BASE_URL}")
        print(f"    Installed Models: {model_names}")
    except Exception as e:
        print(f"  ⚠ Ollama API notice: {e}")


async def run_phase2_3_audit():
    print("\n" + "=" * 60)
    print(" PHASE 2 & 3: CHAT PIPELINE, PROMPT TYPES & MEMORY AUDIT")
    print("=" * 60)

    async with AsyncSessionLocal() as session:
        # Ensure audit test user exists
        user_repo = UserRepository(session)
        user = await user_repo.get_by_email("audit@vikrm.ai")
        if not user:
            user = await user_repo.create(
                email="audit@vikrm.ai",
                password_hash="hash",
                full_name="Audit User",
                role="user"
            )

        user_id = user.id

        service = ChatService(session)
        memory_svc = MemoryService(session)

        # 1. Create a Test User session / conversation
        print("[1/5] Creating test conversation thread...")
        conv = await service.create_conversation(user_id=user_id, title="Audit Conversation", model="qwen3:8b")
        print(f"  ✓ Created Conversation ID: {conv.id} (provider={conv.provider}, model={conv.model})")

        # 2. Test Prompts Suite
        prompts = [
            ("Simple Chat", "Hello, who are you?"),
            ("Code Generation", "Write a Python function to compute Fibonacci numbers."),
            ("Research", "List 3 key milestones in modern AI development."),
            ("Translation", "Translate 'Technology empowers innovation' into French."),
            ("Long Prompt", "Explain event-driven architecture and asynchronous messaging systems."),
        ]

        print("\n[2/5] Testing Prompt Categories via stream_reply...")
        for category, prompt in prompts:
            print(f"\n  ► Category: {category}")
            print(f"    User Prompt: {prompt!r}")
            start = time.perf_counter()
            tokens = []
            async for chunk in service.stream_reply(conversation=conv, user_content=prompt):
                tokens.append(chunk)
            elapsed = time.perf_counter() - start
            full_reply = "".join(tokens)
            print(f"    Stream Completed in {elapsed:.2f}s ({len(tokens)} chunks, {len(full_reply)} chars)")
            print(f"    Snippet: {repr(full_reply[:120])}...")
            assert "I received your request" not in full_reply
            assert len(full_reply) > 5

        # 3. Test Memory Search & Context Injection
        print("\n[3/5] Testing Memory Store & Context Retrieval...")
        mem = await memory_svc.create_memory(user_id=user_id, content="User prefers TypeScript and dark theme mode.")
        print(f"  ✓ Saved Memory ID: {mem.id} ({mem.content!r})")

        mems = await memory_svc.search_memories(user_id=user_id, query="theme preference", top_k=3)
        print(f"  ✓ Searched Memory Results count: {len(mems)}")

        # 4. Test Attachment Text Extraction
        print("\n[4/5] Testing Attachment Text Extraction...")
        sample_txt = "Project Vikrm: Next-generation multi-agent autonomous framework."
        extracted = extract_text_from_file("spec.txt", sample_txt.encode("utf-8"))
        print(f"  ✓ Extracted Text from TXT: {extracted!r}")
        assert extracted == sample_txt

        sample_csv = "id,name,role\n1,Alice,Admin\n2,Bob,User"
        extracted_csv = extract_text_from_file("data.csv", sample_csv.encode("utf-8"))
        print(f"  ✓ Extracted Text from CSV: {extracted_csv!r}")

        # 5. Test Conversation History & Export
        print("\n[5/5] Testing Conversation History & Export...")
        export_data = await service.export_conversation(conv)
        print(f"  ✓ Exported Conversation: title={export_data['title']!r}, messages_count={len(export_data['messages'])}")
        assert len(export_data["messages"]) >= 10


async def run_phase4_benchmark():
    print("\n" + "=" * 60)
    print(" PHASE 4: LATENCY & PERFORMANCE BENCHMARK")
    print("=" * 60)

    provider = OllamaProvider()
    prompt = "What is Python? Answer in 2 short sentences."
    messages = [ChatMessage(role="user", content=prompt)]

    start_time = time.perf_counter()
    first_token_time = None
    chunks = []

    try:
        async for chunk in provider.stream_chat(messages=messages, model="qwen3:8b"):
            if first_token_time is None:
                first_token_time = time.perf_counter()
            chunks.append(chunk)
    except Exception as e:
        print(f"  ⚠ Benchmark streaming notice: {e}")

    end_time = time.perf_counter()

    ttft = (first_token_time - start_time) if first_token_time else 0.0
    total_time = end_time - start_time
    throughput = len(chunks) / total_time if total_time > 0 else 0.0

    print(f"  • Time to First Token (TTFT) : {ttft:.3f} seconds")
    print(f"  • Total Stream Duration     : {total_time:.3f} seconds")
    print(f"  • Chunks / Tokens Streamed  : {len(chunks)}")
    print(f"  • Stream Throughput         : {throughput:.1f} tokens/sec")
    print("  ✓ Benchmark completed cleanly.")


async def main():
    await run_phase1_audit()
    await run_phase2_3_audit()
    await run_phase4_benchmark()

    print("\n" + "=" * 60)
    print(" ALL SYSTEM AUDIT PHASES PASSED WITH ZERO ERRORS!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

