"""
Live end-to-end pipeline test.
Runs inside the backend container: python test_pipeline.py
"""
import asyncio
import sys

import os

backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from app.core.config import settings
from app.services.llm.base import ChatMessage
from app.services.llm.ollama_provider import OllamaProvider


async def test():
    print("=== Backend LLM Pipeline Test ===")
    print(f"DEFAULT_LLM_PROVIDER : {settings.DEFAULT_LLM_PROVIDER}")
    print(f"DEFAULT_LLM_MODEL    : {settings.DEFAULT_LLM_MODEL}")
    print(f"OLLAMA_BASE_URL      : {settings.OLLAMA_BASE_URL}")

    provider = OllamaProvider()
    print(f"Provider base_url    : {provider.base_url}")

    prompts = [
        "What is 2+2? Answer in one sentence.",
        "Explain FastAPI in one sentence.",
        "What is Tamil literature? One sentence.",
    ]

    for prompt in prompts:
        print(f"\n--- Prompt: {prompt!r} ---")
        messages = [ChatMessage(role="user", content=prompt)]
        chunks = []
        try:
            async for chunk in provider.stream_chat(messages=messages, model="qwen3:8b"):
                chunks.append(chunk)
            full = "".join(chunks)
            print(f"Response ({len(full)} chars): {full[:300]!r}")
        except Exception as exc:
            print(f"ERROR: {type(exc).__name__}: {exc}")


asyncio.run(test())
