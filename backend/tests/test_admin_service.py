"""
Tests AdminService directly (RBAC enforcement itself — require_admin —
was already covered by test_auth_endpoints.py in Milestone 2; these
tests cover the admin business logic: self-protection rules and
system-wide stat accuracy).
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import UserRole
from app.repositories.agent_repository import AgentRepository
from app.repositories.user_repository import UserRepository
from app.services.admin_service import AdminService, AdminServiceError


@pytest.mark.asyncio
async def test_list_users_returns_all_users(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    await users.create(google_sub="u1", email="u1@example.com", full_name=None, avatar_url=None, role=UserRole.ADMIN)
    await users.create(google_sub="u2", email="u2@example.com", full_name=None, avatar_url=None)
    await db_session.commit()

    admin_service = AdminService(db_session)
    all_users = await admin_service.list_users()
    assert len(all_users) == 2


@pytest.mark.asyncio
async def test_admin_can_promote_another_user(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    admin_user = await users.create(
        google_sub="admin", email="admin@example.com", full_name=None, avatar_url=None, role=UserRole.ADMIN
    )
    regular_user = await users.create(
        google_sub="regular", email="regular@example.com", full_name=None, avatar_url=None
    )
    await db_session.commit()

    admin_service = AdminService(db_session)
    updated = await admin_service.update_user(
        target_user_id=regular_user.id, acting_user_id=admin_user.id, role="admin", is_active=None
    )
    assert updated.role == UserRole.ADMIN


@pytest.mark.asyncio
async def test_admin_can_deactivate_another_user(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    admin_user = await users.create(
        google_sub="admin2", email="admin2@example.com", full_name=None, avatar_url=None, role=UserRole.ADMIN
    )
    regular_user = await users.create(
        google_sub="regular2", email="regular2@example.com", full_name=None, avatar_url=None
    )
    await db_session.commit()

    admin_service = AdminService(db_session)
    updated = await admin_service.update_user(
        target_user_id=regular_user.id, acting_user_id=admin_user.id, role=None, is_active=False
    )
    assert updated.is_active is False


@pytest.mark.asyncio
async def test_admin_cannot_deactivate_own_account(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    admin_user = await users.create(
        google_sub="admin3", email="admin3@example.com", full_name=None, avatar_url=None, role=UserRole.ADMIN
    )
    await db_session.commit()

    admin_service = AdminService(db_session)
    with pytest.raises(AdminServiceError, match="cannot deactivate your own"):
        await admin_service.update_user(
            target_user_id=admin_user.id, acting_user_id=admin_user.id, role=None, is_active=False
        )


@pytest.mark.asyncio
async def test_admin_cannot_remove_own_admin_role(db_session: AsyncSession) -> None:
    """Prevents a self-inflicted lockout with no other admin to fix it."""
    users = UserRepository(db_session)
    admin_user = await users.create(
        google_sub="admin4", email="admin4@example.com", full_name=None, avatar_url=None, role=UserRole.ADMIN
    )
    await db_session.commit()

    admin_service = AdminService(db_session)
    with pytest.raises(AdminServiceError, match="cannot remove your own admin role"):
        await admin_service.update_user(
            target_user_id=admin_user.id, acting_user_id=admin_user.id, role="user", is_active=None
        )


@pytest.mark.asyncio
async def test_update_nonexistent_user_raises(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    admin_user = await users.create(
        google_sub="admin5", email="admin5@example.com", full_name=None, avatar_url=None, role=UserRole.ADMIN
    )
    await db_session.commit()

    admin_service = AdminService(db_session)
    with pytest.raises(AdminServiceError, match="User not found"):
        await admin_service.update_user(
            target_user_id=9999, acting_user_id=admin_user.id, role="admin", is_active=None
        )


@pytest.mark.asyncio
async def test_system_stats_reflect_real_data_across_all_users(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    user_a = await users.create(
        google_sub="stat-a", email="stat-a@example.com", full_name=None, avatar_url=None, role=UserRole.ADMIN
    )
    user_b = await users.create(google_sub="stat-b", email="stat-b@example.com", full_name=None, avatar_url=None)
    await db_session.commit()

    agents = AgentRepository(db_session)
    await agents.create(user_id=user_a.id, name="Agent 1")
    await agents.create(user_id=user_b.id, name="Agent 2")
    await agents.create(user_id=user_b.id, name="Agent 3")
    await db_session.commit()

    admin_service = AdminService(db_session)
    stats = await admin_service.get_system_stats()

    # Stats must span BOTH users, not just one — this is the key
    # difference from Milestone 11's user-scoped AnalyticsService.
    assert stats["total_users"] == 2
    assert stats["active_users"] == 2
    assert stats["admin_users"] == 1
    assert stats["total_agents"] == 3
