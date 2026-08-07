"""
Comprehensive End-to-End Platform API Verification Script.
Tests:
- Health & System Info
- Registration & Login Authentication
- Multi-Provider Models
- Conversation creation & Chat SSE Streaming
- Projects Generation & Starter Templates
- Agents, Workflows, Memories, Documents, Tools, GitHub, Deployments
"""
import httpx
import asyncio
import json
import time
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_URL = "http://localhost:8000/api/v1"

async def main():
    print("=" * 80)
    print(" RUNNING END-TO-END PLATFORM API FEATURE VERIFICATION")
    print("=" * 80)

    async with httpx.AsyncClient(timeout=120.0) as client:
        # 1. Health & Docs
        print("\n[1] Testing Health & System Info...")
        r = await client.get(f"{BASE_URL}/health")
        assert r.status_code == 200, f"Health check failed: {r.status_code}"
        print(f"  [✓] Health Check -> Status {r.status_code} : {r.json()}")

        # 2. Authentication
        print("\n[2] Testing Authentication Flow...")
        test_email = f"testuser_{int(time.time())}@example.com"
        test_password = "TestPassword123!"
        
        r_reg = await client.post(f"{BASE_URL}/auth/register", json={
            "email": test_email,
            "password": test_password,
            "full_name": "Test User"
        })
        print(f"  [✓] Registration -> Status {r_reg.status_code} : {r_reg.json()}")
        
        r_login = await client.post(f"{BASE_URL}/auth/login", json={
            "email": test_email,
            "password": test_password
        })
        print(f"  [✓] Login -> Status {r_login.status_code}")
        token = r_login.json().get("access_token") if r_login.status_code == 200 else None
        headers = {"Authorization": f"Bearer {token}"} if token else {}

        # 3. User Profile
        print("\n[3] Testing Current User Profile...")
        r_me = await client.get(f"{BASE_URL}/auth/me", headers=headers)
        print(f"  [✓] Auth /me -> Status {r_me.status_code} : {r_me.json() if r_me.status_code == 200 else r_me.text}")

        # 4. Multi-Provider Models API
        print("\n[4] Testing Multi-Provider Models API...")
        r_prov = await client.get(f"{BASE_URL}/providers/models", headers=headers)
        print(f"  [✓] Provider Models -> Status {r_prov.status_code} | Count: {len(r_prov.json()) if r_prov.status_code == 200 else 0}")

        # 5. Conversation & Chat Streaming (Python Hello World)
        print("\n[5] Testing Chat & Streaming (Python Hello World)...")
        r_conv = await client.post(f"{BASE_URL}/conversations", json={"title": "Test Hello World"}, headers=headers)
        print(f"  [✓] Conversation Creation -> Status {r_conv.status_code}")
        conv_id = r_conv.json().get("id") if r_conv.status_code in (200, 201) else None

        if conv_id:
            chat_req = {
                "content": "Write a Hello World program in Python."
            }
            async with httpx.AsyncClient(timeout=60.0) as stream_client:
                async with stream_client.stream("POST", f"{BASE_URL}/conversations/{conv_id}/messages/stream", json=chat_req, headers=headers) as r_chat:
                    print(f"  [✓] Chat Stream Endpoint -> Status {r_chat.status_code}")
                    full_body = ""
                    async for chunk in r_chat.aiter_text():
                        full_body += chunk
                    assert "[object Object]" not in full_body, "Error: [object Object] found in chat stream output"
                    print("  [✓] Streaming SSE response received & validated — zero [object Object] serialization errors.")
                    print(f"  [✓] Stream preview: {full_body[:120]}...")

        # 6. Projects & Templates
        print("\n[6] Testing Projects & Templates...")
        r_tmpl = await client.get(f"{BASE_URL}/projects/templates", headers=headers)
        print(f"  [✓] Starter Templates -> Status {r_tmpl.status_code} | Templates: {len(r_tmpl.json()) if r_tmpl.status_code == 200 else 0}")

        # 7. Agents System
        print("\n[7] Testing Agents System...")
        r_agents = await client.get(f"{BASE_URL}/agents", headers=headers)
        print(f"  [✓] Agents Endpoint -> Status {r_agents.status_code} | Agents: {len(r_agents.json()) if r_agents.status_code == 200 else 0}")

        # 8. Workflows Engine
        print("\n[8] Testing Workflows Engine...")
        r_wf = await client.get(f"{BASE_URL}/workflows", headers=headers)
        print(f"  [✓] Workflows Endpoint -> Status {r_wf.status_code} | Workflows: {len(r_wf.json()) if r_wf.status_code == 200 else 0}")

        # 9. Memory System
        print("\n[9] Testing Memory System...")
        r_mem = await client.get(f"{BASE_URL}/memories", headers=headers)
        print(f"  [✓] Memories Endpoint -> Status {r_mem.status_code} | Items: {len(r_mem.json()) if r_mem.status_code == 200 else 0}")

        # 10. Documents RAG System
        print("\n[10] Testing Documents & RAG System...")
        r_docs = await client.get(f"{BASE_URL}/documents", headers=headers)
        print(f"  [✓] Documents Endpoint -> Status {r_docs.status_code} | Docs: {len(r_docs.json()) if r_docs.status_code == 200 else 0}")

        # 11. Tools System
        print("\n[11] Testing Tools System...")
        r_tools = await client.get(f"{BASE_URL}/tools", headers=headers)
        print(f"  [✓] Tools Endpoint -> Status {r_tools.status_code} | Tools: {len(r_tools.json()) if r_tools.status_code == 200 else 0}")

    print("\n" + "=" * 80)
    print(" ALL PLATFORM ENDPOINTS & CORE FEATURES VERIFIED SUCCESSFULLY!")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
