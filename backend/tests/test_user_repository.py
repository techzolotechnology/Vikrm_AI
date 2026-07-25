"""
Integration tests against a real (in-memory SQLite) database session —
these exercise actual SQL, not mocks, catching the class of bug where
a comment claims behavior the code doesn't implement.
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserRole
from app.repositories.user_repository import UserRepository


@pytest.mark.asyncio
async def test_first_user_is_created_correctly(db_session: AsyncSession) -> None:
    repo = UserRepository(db_session)
    assert await repo.count() == 0

    user = await repo.create(
        google_sub="google-sub-1",
        email="first@example.com",
        full_name="First User",
        avatar_url=None,
        role=UserRole.ADMIN,
    )
    await db_session.commit()

    assert user.role == UserRole.ADMIN
    assert await repo.count() == 1


@pytest.mark.asyncio
async def test_second_user_defaults_to_user_role(db_session: AsyncSession) -> None:
    repo = UserRepository(db_session)
    await repo.create(
        google_sub="google-sub-1",
        email="first@example.com",
        full_name="First User",
        avatar_url=None,
        role=UserRole.ADMIN,
    )
    await db_session.commit()

    second = await repo.create(
        google_sub="google-sub-2",
        email="second@example.com",
        full_name="Second User",
        avatar_url=None,
        role=UserRole.USER,
    )
    await db_session.commit()

    assert second.role == UserRole.USER
    assert await repo.count() == 2


@pytest.mark.asyncio
async def test_get_by_google_sub_and_email(db_session: AsyncSession) -> None:
    repo = UserRepository(db_session)
    created = await repo.create(
        google_sub="google-sub-x",
        email="findme@example.com",
        full_name="Find Me",
        avatar_url=None,
    )
    await db_session.commit()

    by_sub = await repo.get_by_google_sub("google-sub-x")
    by_email = await repo.get_by_email("findme@example.com")
    missing = await repo.get_by_google_sub("does-not-exist")

    assert by_sub is not None and by_sub.id == created.id
    assert by_email is not None and by_email.id == created.id
    assert missing is None


@pytest.mark.asyncio
async def test_full_auth_service_flow_promotes_first_user_to_admin(
    db_session: AsyncSession,
) -> None:
    """End-to-end through AuthService, mocking only the Google network
    call — everything else (DB writes, role promotion, token issuance)
    runs for real."""
    from unittest.mock import patch

    from app.services.auth_service import AuthService, GoogleTokenInfo

    fake_info = GoogleTokenInfo(
        sub="google-sub-first", email="admin-to-be@example.com", name="Admin To Be", picture=None
    )

    with patch("app.services.auth_service.verify_google_id_token", return_value=fake_info):
        service = AuthService(db_session)
        user, access_token, refresh_token = await service.authenticate_with_google("fake-id-token")

    assert user.role == UserRole.ADMIN
    assert access_token
    assert refresh_token

    # A second, different user signing in afterward must NOT be admin.
    fake_info_2 = GoogleTokenInfo(
        sub="google-sub-second", email="regular@example.com", name="Regular", picture=None
    )
    with patch("app.services.auth_service.verify_google_id_token", return_value=fake_info_2):
        service2 = AuthService(db_session)
        user2, _, _ = await service2.authenticate_with_google("fake-id-token-2")

    assert user2.role == UserRole.USER
