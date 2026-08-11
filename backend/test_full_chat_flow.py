import asyncio
import sys
import json
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.config import settings
from app.core.security import create_access_token
from app.repositories.user_repository import UserRepository
from app.models.user import User, AuthProvider, UserRole
from app.core.database import AsyncSessionLocal

sys.stdout.reconfigure(encoding="utf-8")

async def test_chat_flow():
    async with AsyncSessionLocal() as session:
        user_repo = UserRepository(session)
        user = await user_repo.get_by_email("test@example.com")
        if not user:
            user = User(
                email="test@example.com",
                full_name="Test User",
                auth_provider=AuthProvider.EMAIL,
                role=UserRole.USER,
                email_verified=True,
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
        user_id = user.id
        user_role = user.role
        token = create_access_token(user_id=user_id, role=user_role)

    headers = {"Authorization": f"Bearer {token}"}
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Test /api/v1/providers/models
        res_models = await client.get("/api/v1/providers/models", headers=headers)
        print("=== 1. Providers Models Response ===")
        print("Status:", res_models.status_code)
        print("Body:", res_models.json())
        assert res_models.json()["default_model"] == "qwen3:8b", f"Expected default_model qwen3:8b, got {res_models.json().get('default_model')}"

        # 2. Create conversation
        res_conv = await client.post(
            "/api/v1/conversations",
            json={"title": "Test Flow Conv", "provider": "ollama", "model": "qwen3:8b"},
            headers=headers,
        )
        print("\n=== 2. Create Conversation Response ===")
        print("Status:", res_conv.status_code)
        conv_data = res_conv.json()
        print("Conversation Data:", conv_data)
        conv_id = conv_data["id"]

        # 3. Stream message "hello"
        print("\n=== 3. Stream Message Payload ===")
        payload = {
            "content": "hello",
            "provider": "ollama",
            "model": "qwen3:8b",
        }
        print("Payload sent:", payload)

        print("\n=== 4. Stream Message SSE Output ===")
        async with client.stream(
            "POST",
            f"/api/v1/conversations/{conv_id}/messages/stream",
            json=payload,
            headers=headers,
        ) as response:
            print("Stream Status:", response.status_code)
            async for line in response.aiter_lines():
                if line:
                    print("SSE Line:", line)

if __name__ == "__main__":
    asyncio.run(test_chat_flow())
