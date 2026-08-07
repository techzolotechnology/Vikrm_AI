"""
LIVE STREAMING PIPELINE TRACE — uses the backend's own auth service
to create a test user, then streams a real chat request and logs every delta.
"""
import asyncio, json, sys, os, httpx

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

API_BASE = "http://localhost:8000/api/v1"
TEST_EMAIL = "live_trace@vikrm.ai"
TEST_PASSWORD = "LiveTrace!2024"
TEST_NAME = "Live Trace Test"

SEP = "-" * 70


def trace_value(stage: str, value):
    t = type(value).__name__
    is_bad = isinstance(value, (dict, list)) or (
        isinstance(value, str) and "[object Object]" in value
    )
    print(f"\n{SEP}")
    print(f"STAGE:       {stage}")
    print(f"TYPE:        {t}")
    print(f"CONSTRUCTOR: {type(value).__name__}")
    print(f"IS_BAD:      {'YES <<<< ROOT CAUSE FOUND HERE' if is_bad else 'no'}")
    if isinstance(value, str):
        print(f"VALUE:       {repr(value[:500])}")
    elif isinstance(value, (dict, list)):
        try:
            print(f"VALUE:       {json.dumps(value, indent=2)[:500]}")
        except Exception:
            print(f"VALUE:       {repr(str(value)[:500])}")
    print(SEP)
    return is_bad


async def auth_or_register(client: httpx.AsyncClient) -> str:
    # Try login
    r = await client.post(f"{API_BASE}/auth/login",
                          json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
                          timeout=10.0)
    if r.status_code == 200:
        data = r.json()
        token = data.get("access_token") or data.get("token") or data.get("jwt")
        if token:
            print(f"[AUTH] Login OK for {TEST_EMAIL}")
            return token

    # Register new user
    r = await client.post(f"{API_BASE}/auth/register",
                          json={"email": TEST_EMAIL, "password": TEST_PASSWORD, "full_name": TEST_NAME},
                          timeout=10.0)
    print(f"[AUTH] Register response {r.status_code}: {r.text[:200]}")

    # Login after register
    r = await client.post(f"{API_BASE}/auth/login",
                          json={"email": TEST_EMAIL, "password": TEST_PASSWORD},
                          timeout=10.0)
    if r.status_code == 200:
        data = r.json()
        token = data.get("access_token") or data.get("token") or data.get("jwt")
        if token:
            print(f"[AUTH] Login after register OK")
            return token

    # Print full response to understand schema
    print(f"[AUTH] Full login response: {r.status_code} {r.text[:600]}")
    raise RuntimeError("Cannot authenticate")


async def run_trace():
    print("\n" + "=" * 70)
    print(" LIVE STREAMING PIPELINE TRACE — FULL RUNTIME EVIDENCE")
    print("=" * 70)

    async with httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0)) as client:

        # STEP 1: Authenticate
        token = await auth_or_register(client)
        headers = {"Authorization": f"Bearer {token}"}

        # STEP 2: Create conversation
        r = await client.post(
            f"{API_BASE}/conversations",
            json={"title": "Trace: FastAPI test", "provider": "ollama", "model": "llama3.2"},
            headers=headers,
        )
        if r.status_code not in (200, 201):
            print(f"[CONV] ERROR {r.status_code}: {r.text[:300]}")
            return
        conv = r.json()
        conv_id = conv["id"]
        print(f"\n[CONV] Created conv id={conv_id} provider=ollama model=llama3.2")

        # STEP 3: Stream
        prompt = "Create a simple FastAPI app with a GET endpoint at /hello that returns {message: 'Hello World'}"
        print(f"\n[PROMPT] {prompt!r}")
        print(f"\n[STREAM] Sending to /conversations/{conv_id}/messages/stream ...")

        url = f"{API_BASE}/conversations/{conv_id}/messages/stream"
        body_bytes = json.dumps({"content": prompt, "attachment_ids": []}).encode()

        total_deltas = 0
        bad_deltas = 0
        full_content = ""
        first_bad_stage = None

        async with client.stream(
            "POST", url,
            content=body_bytes,
            headers={**headers, "Content-Type": "application/json", "Accept": "text/event-stream"},
        ) as resp:
            print(f"[HTTP] Status: {resp.status_code}")
            if resp.status_code != 200:
                body_read = await resp.aread()
                print(f"[HTTP] Body: {body_read[:400]}")
                return

            trace_value("HTTP Response Status", str(resp.status_code))

            buffer = ""
            async for raw_chunk in resp.aiter_bytes(1024):
                buffer += raw_chunk.decode("utf-8", errors="replace")
                frames = buffer.split("\n\n")
                buffer = frames.pop()

                for frame in frames:
                    for line in frame.split("\n"):
                        line = line.strip()
                        if not line.startswith("data:"):
                            continue
                        json_str = line[5:].strip()
                        if not json_str or json_str == "[DONE]":
                            continue

                        try:
                            event = json.loads(json_str)
                        except Exception:
                            continue

                        # STAGE: Raw SSE event
                        if "delta" in event:
                            delta = event["delta"]
                            total_deltas += 1

                            is_bad = isinstance(delta, (dict, list)) or (
                                isinstance(delta, str) and "[object Object]" in delta
                            )

                            if is_bad:
                                bad_deltas += 1
                                stage = f"SSE delta #{total_deltas} (delta field)"
                                trace_value(f">>> BAD! {stage}", delta)
                                trace_value(f">>> BAD! Raw SSE event #{total_deltas}", event)
                                if first_bad_stage is None:
                                    first_bad_stage = stage

                            # Log first 3 deltas
                            if total_deltas <= 3:
                                trace_value(f"SSE delta #{total_deltas}", delta)

                            if isinstance(delta, str):
                                full_content += delta
                            else:
                                full_content += str(delta)

                        if event.get("done"):
                            print(f"\n[DONE] Stream completed. Total deltas: {total_deltas}")

        # STEP 4: Verify accumulated content
        print(f"\n{'='*70}")
        print(f" CONTENT VERIFICATION")
        print(f"{'='*70}")
        print(f"Total SSE deltas:        {total_deltas}")
        print(f"Bad (object) deltas:     {bad_deltas}")
        print(f"[object Object] in text: {'YES <<< BUG STILL EXISTS' if '[object Object]' in full_content else 'NO — CLEAN'}")
        if first_bad_stage:
            print(f"First bad stage:         {first_bad_stage}")
        print(f"\nGenerated content preview (first 800 chars):")
        print("-" * 60)
        print(full_content[:800])
        print("-" * 60)

        # STEP 5: Load from API and verify DB content
        r = await client.get(f"{API_BASE}/conversations/{conv_id}", headers=headers)
        if r.status_code == 200:
            conv_detail = r.json()
            msgs = conv_detail.get("messages", [])
            print(f"\n[API] Loaded {len(msgs)} messages from API (DB-backed)")
            for msg in msgs:
                content = msg.get("content", "")
                role = msg.get("role", "?")
                content_type = type(content).__name__
                is_bad = isinstance(content, (dict, list)) or (
                    isinstance(content, str) and "[object Object]" in content
                )
                print(f"  role={role:<12} type={content_type:<8} len={len(str(content)):<6} bad={'YES <<< DB BUG' if is_bad else 'no'}")
                if is_bad:
                    print(f"    CONTENT: {repr(str(content)[:400])}")

        print(f"\n{'='*70}")
        if bad_deltas == 0 and "[object Object]" not in full_content:
            print(" FINAL RESULT: PASS — Zero [object Object] detected in pipeline")
            print(" The Ollama provider fix is working correctly.")
        else:
            print(f" FINAL RESULT: FAIL")
            print(f"   Bad deltas:      {bad_deltas}")
            print(f"   [obj Object]:    {'in content' if '[object Object]' in full_content else 'not found'}")
            print(f"   First bad stage: {first_bad_stage}")
        print(f"{'='*70}")


if __name__ == "__main__":
    asyncio.run(run_trace())
