"""
Exercises OrchestrationService end-to-end: real DB persistence, real
plan parsing, real per-agent delegation and failure isolation, and
real synthesis — against a fake LLM provider whose responses are
keyed by prompt content, so each phase (planning vs a specific
member's subtask vs synthesis) gets a distinct, verifiable response.
"""
from typing import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent_team import TeamRunStatus
from app.repositories.agent_repository import AgentRepository
from app.repositories.user_repository import UserRepository
from app.services.llm import registry
from app.services.llm.base import ChatMessage, LLMProvider
from app.services.orchestration_service import OrchestrationError, OrchestrationService


class FakeLLMProvider(LLMProvider):
    """Returns a canned response based on which trigger substring
    appears in the prompt — lets a test control exactly what the
    'manager' and each 'member' agent say at each phase."""

    def __init__(self, triggers: dict[str, str]) -> None:
        self.triggers = triggers
        self.calls: list[str] = []

    async def stream_chat(
        self, *, messages: list[ChatMessage], model: str, temperature: float = 0.7
    ) -> AsyncIterator[str]:
        prompt = messages[-1].content
        self.calls.append(prompt)
        for trigger, response in self.triggers.items():
            if trigger in prompt:
                yield response
                return
        yield "(no matching trigger — fake provider default response)"


@pytest.mark.asyncio
async def test_full_orchestration_plan_delegate_synthesize(
    db_session: AsyncSession, monkeypatch
) -> None:
    fake = FakeLLMProvider(
        {
            # Order matters: the synthesis prompt embeds each step's
            # subtask text verbatim (so the manager can see what was
            # done), so a subtask trigger would also match inside the
            # synthesis prompt unless the more specific "Synthesize
            # these" trigger is checked first.
            "Synthesize these": "FINAL: Q3 revenue grew 12% to $4.2M; full summary attached.",
            "JSON array": (
                '[{"agent": "Researcher", "task": "Find Q3 revenue figures"}, '
                '{"agent": "Writer", "task": "Draft a summary"}]'
            ),
            "Find Q3 revenue figures": "Q3 revenue was $4.2M, up 12% YoY.",
            "Draft a summary": "Here is a one-paragraph summary of performance.",
        }
    )
    monkeypatch.setitem(registry._PROVIDERS, "fake", lambda: fake)

    users = UserRepository(db_session)
    user = await users.create(
        google_sub="orch-1", email="orch1@example.com", full_name=None, avatar_url=None
    )
    await db_session.commit()

    agents = AgentRepository(db_session)
    manager = await agents.create(user_id=user.id, name="Manager", provider="fake", model="fake-model")
    researcher = await agents.create(
        user_id=user.id, name="Researcher", description="Finds data", provider="fake", model="fake-model"
    )
    writer = await agents.create(
        user_id=user.id, name="Writer", description="Writes prose", provider="fake", model="fake-model"
    )
    await db_session.commit()

    service = OrchestrationService(db_session)
    team = await service.create_team(
        user_id=user.id,
        name="Reporting Team",
        description=None,
        manager_agent_id=manager.id,
        member_agent_ids=[researcher.id, writer.id],
    )

    run = await service.run_team(team=team, user_id=user.id, task="Produce a Q3 performance report")

    assert run.status == TeamRunStatus.COMPLETED
    assert "FINAL:" in run.final_output
    assert len(run.plan) == 2
    assert len(run.steps) == 2
    assert run.steps[0]["agent_name"] == "Researcher"
    assert run.steps[0]["status"] == "success"
    assert "$4.2M" in run.steps[0]["output"]
    assert run.steps[1]["agent_name"] == "Writer"
    assert run.steps[1]["status"] == "success"

    # Verify the actual call sequence: plan, then each member, then synthesis.
    assert len(fake.calls) == 4
    assert "JSON array" in fake.calls[0]  # planning call went to the manager
    assert "Find Q3 revenue figures" in fake.calls[1]  # delegated to researcher
    assert "Draft a summary" in fake.calls[2]  # delegated to writer
    assert "Synthesize these" in fake.calls[3]  # final call back to the manager


@pytest.mark.asyncio
async def test_unparseable_plan_falls_back_to_running_all_members(
    db_session: AsyncSession, monkeypatch
) -> None:
    fake = FakeLLMProvider(
        {
            # No "JSON array" trigger response configured for planning —
            # falls through to the fake's default non-JSON response.
            "Handle": "Handled the fallback task.",
        }
    )
    monkeypatch.setitem(registry._PROVIDERS, "fake", lambda: fake)

    users = UserRepository(db_session)
    user = await users.create(
        google_sub="orch-2", email="orch2@example.com", full_name=None, avatar_url=None
    )
    await db_session.commit()

    agents = AgentRepository(db_session)
    manager = await agents.create(user_id=user.id, name="Manager", provider="fake", model="fake-model")
    helper = await agents.create(user_id=user.id, name="Helper", provider="fake", model="fake-model")
    await db_session.commit()

    service = OrchestrationService(db_session)
    team = await service.create_team(
        user_id=user.id,
        name="Fallback Team",
        description=None,
        manager_agent_id=manager.id,
        member_agent_ids=[helper.id],
    )

    run = await service.run_team(team=team, user_id=user.id, task="Handle this task")

    # Fallback plan must be visibly marked, not a silent default.
    assert run.plan[0]["fallback"] is True
    assert run.plan[0]["agent"] == "Helper"
    assert run.steps[0]["agent_name"] == "Helper"
    assert run.steps[0]["status"] == "success"


@pytest.mark.asyncio
async def test_one_member_failing_does_not_abort_the_whole_run(
    db_session: AsyncSession, monkeypatch
) -> None:
    class PartiallyFailingProvider(LLMProvider):
        async def stream_chat(self, *, messages, model, temperature=0.7):
            prompt = messages[-1].content
            # Order matters here too: the synthesis prompt embeds the
            # successful step's subtask text ("succeed") verbatim, so
            # that check must come after the "Synthesize" check.
            if "JSON array" in prompt:
                yield (
                    '[{"agent": "Good Agent", "task": "succeed"}, '
                    '{"agent": "Bad Agent", "task": "fail"}]'
                )
            elif "Synthesize" in prompt:
                yield "Synthesized from the one successful step."
            elif "succeed" in prompt:
                yield "This part worked fine."
            elif "fail" in prompt:
                raise RuntimeError("simulated provider crash")

    monkeypatch.setitem(registry._PROVIDERS, "fake", lambda: PartiallyFailingProvider())

    users = UserRepository(db_session)
    user = await users.create(
        google_sub="orch-3", email="orch3@example.com", full_name=None, avatar_url=None
    )
    await db_session.commit()

    agents = AgentRepository(db_session)
    manager = await agents.create(user_id=user.id, name="Manager", provider="fake", model="fake-model")
    good_agent = await agents.create(user_id=user.id, name="Good Agent", provider="fake", model="fake-model")
    bad_agent = await agents.create(user_id=user.id, name="Bad Agent", provider="fake", model="fake-model")
    await db_session.commit()

    service = OrchestrationService(db_session)
    team = await service.create_team(
        user_id=user.id,
        name="Mixed Team",
        description=None,
        manager_agent_id=manager.id,
        member_agent_ids=[good_agent.id, bad_agent.id],
    )

    run = await service.run_team(team=team, user_id=user.id, task="Do a mixed-result task")

    assert run.status == TeamRunStatus.COMPLETED  # overall run still completes
    good_step = next(s for s in run.steps if s["agent_name"] == "Good Agent")
    bad_step = next(s for s in run.steps if s["agent_name"] == "Bad Agent")
    assert good_step["status"] == "success"
    assert bad_step["status"] == "failed"
    assert "simulated provider crash" in bad_step["error"]
    assert "Synthesized from the one successful step" in run.final_output


@pytest.mark.asyncio
async def test_create_team_rejects_nonexistent_manager(db_session: AsyncSession) -> None:
    users = UserRepository(db_session)
    user = await users.create(
        google_sub="orch-4", email="orch4@example.com", full_name=None, avatar_url=None
    )
    await db_session.commit()

    service = OrchestrationService(db_session)
    with pytest.raises(OrchestrationError, match="Manager agent not found"):
        await service.create_team(
            user_id=user.id,
            name="Bad Team",
            description=None,
            manager_agent_id=9999,
            member_agent_ids=[],
        )
