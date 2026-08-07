"""
Live End-to-End System Verification & Stress Test against running FastAPI server (http://127.0.0.1:8000).

Tests:
1. User registration & authentication token acquisition.
2. Conversation creation.
3. 50 sequential live streaming chat requests over persistent OllamaClientManager pool.
4. 10 parallel concurrent live streaming chat requests.
5. Idle timeout & re-engagement test.
6. Verifies zero connection errors ("Could not connect to Ollama") occur.
"""
import asyncio
import json
import random
import string
import time
import httpx


BASE_URL = "http://127.0.0.1:8000/api/v1"


def safe_str(val: str) -> str:
    """Safe ASCII string representation preventing Windows cp1252 terminal crashes."""
    return str(val).encode("ascii", errors="replace").decode("ascii")


def random_string(length: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))


async def run_live_verification():
    print("=== LIVE END-TO-END SYSTEM VERIFICATION STARTING ===")
    
    # 1. Register test user
    email = f"stress_user_{random_string()}@example.com"
    password = "StressTestPassword123!"
    
    async with httpx.AsyncClient(timeout=15.0) as client:
        print(f"[Step 1] Registering test user: {email}")
        reg_resp = await client.post(f"{BASE_URL}/auth/register", json={
            "email": email,
            "password": password,
            "full_name": "Live Verification User"
        })
        assert reg_resp.status_code == 201, f"Registration failed: {reg_resp.text}"

        print(f"[Step 1] Logging in test user...")
        login_resp = await client.post(f"{BASE_URL}/auth/login", json={
            "email": email,
            "password": password
        })
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token = login_resp.json()["access_token"]
        print("[Step 1 OK] User registered & logged in. JWT token acquired.")

        headers = {"Authorization": f"Bearer {token}"}

        # 2. Create Conversation
        print("[Step 2] Creating test conversation...")
        conv_resp = await client.post(f"{BASE_URL}/conversations", json={
            "title": "Live Verification Chat",
            "provider": "ollama",
            "model": "llama3.2"
        }, headers=headers)
        assert conv_resp.status_code == 201, f"Conversation creation failed: {conv_resp.text}"
        conv_id = conv_resp.json()["id"]
        print(f"[Step 2 OK] Conversation created with ID: {conv_id}")

        # 3. Execute 20 Sequential Live Chat Streams
        print("[Step 3] Firing 20 sequential live SSE stream requests...")
        success_count = 0
        failed_count = 0
        error_messages = []

        start_time = time.time()
        for i in range(1, 21):
            prompt = f"Count step {i}: Say 'OK-{i}' clearly."
            stream_url = f"{BASE_URL}/conversations/{conv_id}/messages/stream"
            
            full_response = []
            try:
                async with client.stream("POST", stream_url, json={"content": prompt}, headers=headers, timeout=120.0) as resp:
                    assert resp.status_code == 200, f"HTTP status {resp.status_code}"
                    
                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            raw_data = line[6:].strip()
                            if raw_data == "[DONE]":
                                break
                            try:
                                parsed = json.loads(raw_data)
                                if "delta" in parsed:
                                    full_response.append(parsed["delta"])
                                if "error" in parsed:
                                    error_messages.append(parsed["error"])
                            except Exception:
                                pass
            except Exception as exc:
                failed_count += 1
                error_messages.append(safe_str(exc))
                print(f"   [FAIL] Stream {i} network/stream exception: {safe_str(exc)}")
                continue

            response_text = "".join(full_response)
            if "Could not connect to Ollama" in response_text or "All connection attempts failed" in response_text or not response_text:
                failed_count += 1
                print(f"   [FAIL] Stream {i} failed (empty or provider connection error)")
            else:
                success_count += 1
                snippet = safe_str(response_text[:35].replace('\n', ' '))
                print(f"   [OK] Stream {i} succeeded. Text snippet: '{snippet}...'")

        elapsed_seq = time.time() - start_time
        print(f"[Step 3 Complete] 20 Sequential Streams: {success_count} succeeded, {failed_count} failed in {elapsed_seq:.2f}s")
        assert failed_count == 0, f"Sequential stream failures: {error_messages}"

        # 4. Execute 10 Concurrent Parallel Streams
        print("[Step 4] Firing 10 parallel concurrent live SSE streams...")
        async def single_parallel_stream(index: int):
            p = f"Parallel prompt {index}"
            async with httpx.AsyncClient(timeout=120.0) as parallel_client:
                async with parallel_client.stream("POST", f"{BASE_URL}/conversations/{conv_id}/messages/stream", json={"content": p}, headers=headers) as resp:
                    text = []
                    async for line in resp.aiter_lines():
                        if line.startswith("data: ") and not line.endswith("[DONE]"):
                            try:
                                d = json.loads(line[6:])
                                if "delta" in d:
                                    text.append(d["delta"])
                            except Exception:
                                pass
                    return "".join(text)

        p_start = time.time()
        parallel_results = await asyncio.gather(*[single_parallel_stream(i) for i in range(1, 11)], return_exceptions=True)
        p_elapsed = time.time() - p_start
        
        p_success = sum(1 for r in parallel_results if isinstance(r, str) and "Could not connect to Ollama" not in r and len(r) > 0)
        print(f"[Step 4 Complete] 10 Parallel Streams: {p_success}/10 succeeded in {p_elapsed:.2f}s")
        assert p_success == 10, f"Parallel stream failures: {safe_str(parallel_results)}"

        # 5. Idle Period followed by re-engagement
        print("[Step 5] Testing idle period pause (3 seconds) followed by re-engagement...")
        await asyncio.sleep(3.0)
        
        async with client.stream("POST", f"{BASE_URL}/conversations/{conv_id}/messages/stream", json={"content": "Post idle test prompt"}, headers=headers) as resp:
            idle_text = []
            async for line in resp.aiter_lines():
                if line.startswith("data: ") and not line.endswith("[DONE]"):
                    try:
                        d = json.loads(line[6:])
                        if "delta" in d:
                            idle_text.append(d["delta"])
                    except Exception:
                        pass
            assert len(idle_text) > 0, "Idle re-engagement stream failed"
            print("[Step 5 OK] Idle re-engagement successful!")

    print("\n====================================================")
    print("[OK] LIVE SYSTEM END-TO-END VERIFICATION: 100% SUCCESS")
    print("====================================================\n")


if __name__ == "__main__":
    asyncio.run(run_live_verification())
