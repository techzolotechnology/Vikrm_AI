"""
Verification script for Vikrm Ollama integration and backend AI response flow.
Runs inside backend container: python /app/verify_ollama_fix.py
"""
import os
import asyncio
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.services.llm.base import ChatMessage
from app.services.llm.ollama_provider import OllamaProvider


async def verify():
    print("==================================================")
    print("     VIKRM BACKEND OLLAMA INTEGRATION VERIFICATION")
    print("==================================================")
    print(f"OLLAMA_BASE_URL      : {settings.OLLAMA_BASE_URL}")
    print(f"DEFAULT_LLM_PROVIDER : {settings.DEFAULT_LLM_PROVIDER}")
    print(f"DEFAULT_LLM_MODEL    : {settings.DEFAULT_LLM_MODEL}")

    provider = OllamaProvider()
    print("\n--- 1. Testing GET /api/tags via list_installed_models ---")
    models = await provider.list_installed_models()
    model_names = [m.get("name") for m in models]
    print(f"Installed Ollama models: {model_names}")
    assert any("llama3.2" in name for name in model_names), "llama3.2 model not found in Ollama installed tags!"
    print("[OK] Model llama3.2 verified in Ollama container.")

    test_prompts = [
        "Hello",
        "Explain FastAPI",
        "Explain ChatGPT",
        "Explain Tamil Literature",
        "What is AI?",
        "Generate Python code",
    ]

    responses = {}
    print("\n--- 2. Testing Real Ollama Generation & Streaming ---")

    for prompt in test_prompts:
        print(f"\nSending User Prompt: {prompt!r}")
        messages = [ChatMessage(role="user", content=prompt)]
        chunks = []
        try:
            async for chunk in provider.stream_chat(messages=messages, model="llama3.2", temperature=0.7):
                chunks.append(chunk)
            full_text = "".join(chunks).strip()
            responses[prompt] = full_text
            print(f"Response Received ({len(full_text)} chars):")
            print(f"  {repr(full_text[:150])}...")
            
            # Assertions to ensure NO placeholder/hardcoded response
            assert "I received your request" not in full_text, f"Found placeholder in response to {prompt!r}"
            assert "Local Ollama service is currently starting" not in full_text, f"Found placeholder in response to {prompt!r}"
            assert len(full_text) > 10, f"Response too short for {prompt!r}"

        except Exception as exc:
            print(f"[ERROR] Failed for prompt {prompt!r}: {type(exc).__name__}: {exc}")
            raise

    print("\n--- 3. Verifying Response Uniqueness & Authenticity ---")
    unique_responses = set(responses.values())
    print(f"Total Prompts Tested: {len(test_prompts)}")
    print(f"Total Unique Responses: {len(unique_responses)}")

    assert len(unique_responses) == len(test_prompts), "Error: Duplicate/identical responses detected!"
    print("[OK] All 6 responses are 100% distinct, unique, and real AI outputs from Ollama!")

    print("\n==================================================")
    print("     ALL VERIFICATION TESTS PASSED SUCCESSFULLY!")
    print("==================================================")


if __name__ == "__main__":
    asyncio.run(verify())
