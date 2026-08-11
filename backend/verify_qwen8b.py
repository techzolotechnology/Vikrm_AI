import os
import sys
import json
import urllib.request
import asyncio

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings
from app.services.llm.ollama_provider import OllamaProvider
from app.services.llm.base import ChatMessage

async def main():
    print("=" * 60)
    print("      OLLAMA & QWEN MODEL CONNECTION VERIFICATION")
    print("=" * 60)
    print(f"Ollama Base URL   : {settings.OLLAMA_BASE_URL}")
    print(f"Default Model Configured : {settings.effective_default_model}")
    
    provider = OllamaProvider()
    print("\n1. Checking Installed Ollama Models...")
    models = await provider.list_installed_models()
    model_names = [m.get("name") for m in models]
    print(f"   Found models: {model_names}")
    
    matched_model = None
    for name in model_names:
        if "qwen" in name.lower():
            matched_model = name
            break
            
    if not matched_model:
        print("❌ Error: No Qwen model found in Ollama!")
        sys.exit(1)
        
    print(f"✓ Matched Qwen Model in Ollama: '{matched_model}'")
    
    print("\n2. Testing Chat Streaming Generation via OllamaProvider...")
    prompt = "Hello! Please confirm in one short sentence that you are Qwen and ready to assist."
    print(f"   Sending Prompt: {prompt!r}")
    
    messages = [ChatMessage(role="user", content=prompt)]
    chunks = []
    async for chunk in provider.stream_chat(messages=messages, model=matched_model, temperature=0.7):
        chunks.append(chunk)
        print(chunk, end="", flush=True)
    print("\n")
    
    full_response = "".join(chunks).strip()
    print(f"✓ Total response length: {len(full_response)} characters")
    
    if len(full_response) > 5:
        print("\n==================================================")
        print("   SUCCESS: Ollama is connected & streaming from Qwen!")
        print("==================================================")
    else:
        print("\n❌ Error: Received empty or invalid response from model.")

if __name__ == "__main__":
    asyncio.run(main())
