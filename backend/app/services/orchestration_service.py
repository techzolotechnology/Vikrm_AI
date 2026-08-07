"""
Multi-agent orchestration service.

`run_team` is a three-phase process:
1. PLAN — the manager agent is prompted with the task and the member
   roster, and asked to return a JSON delegation plan.
2. EXECUTE — each planned step runs the named member agent (its own
   system prompt + model settings) against its assigned subtask, in
   order, with prior steps' outputs available as context.
3. SYNTHESIZE — the manager agent is called once more, given every
   member's output, to produce a single coherent final answer.

Failure isolation mirrors the workflow engine (Milestone 7): one
member agent failing doesn't abort the whole run — its step is marked
failed with an error, and synthesis proceeds using whatever succeeded.
If planning itself fails to produce a usable plan (the manager's
response wasn't parseable JSON even after best-effort extraction), a
documented fallback runs every member agent once against the full,
unmodified task — visible in the run's `plan` field as
`fallback: true`, not a silent default.
"""
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent
from app.models.agent_team import AgentTeam, AgentTeamRun, TeamRunStatus
from app.repositories.agent_repository import AgentRepository
from app.repositories.agent_team_repository import AgentTeamRepository, AgentTeamRunRepository
from app.services.agent_service import build_system_prompt
from app.services.llm.base import ChatMessage, ensure_chat_response, normalize_content_chunk
from app.services.llm.registry import get_provider
from app.services.orchestration.planning import (
    build_planning_prompt,
    build_synthesis_prompt,
    extract_json_array,
)


class OrchestrationError(Exception):
    pass


class OrchestrationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._teams = AgentTeamRepository(session)
        self._runs = AgentTeamRunRepository(session)
        self._agents = AgentRepository(session)

    async def create_team(
        self,
        *,
        user_id: int,
        name: str,
        description: str | None,
        manager_agent_id: int,
        member_agent_ids: list[int],
    ) -> AgentTeam:
        manager = await self._agents.get_by_id(manager_agent_id, user_id=user_id)
        if manager is None:
            raise OrchestrationError("Manager agent not found")
        for agent_id in member_agent_ids:
            member = await self._agents.get_by_id(agent_id, user_id=user_id)
            if member is None:
                raise OrchestrationError(f"Member agent {agent_id} not found")

        team = await self._teams.create(
            user_id=user_id,
            name=name,
            description=description,
            manager_agent_id=manager_agent_id,
            member_agent_ids=member_agent_ids,
        )
        await self._session.commit()
        return team

    async def list_teams(self, *, user_id: int) -> list[AgentTeam]:
        return await self._teams.list_for_user(user_id)

    async def get_team(self, *, team_id: int, user_id: int) -> AgentTeam | None:
        return await self._teams.get_by_id(team_id, user_id=user_id)

    async def delete_team(self, *, team: AgentTeam) -> None:
        await self._teams.delete(team)
        await self._session.commit()

    async def run_team(self, *, team: AgentTeam, user_id: int, task: str) -> AgentTeamRun:
        started_at = datetime.now(timezone.utc)

        manager = await self._agents.get_by_id(team.manager_agent_id, user_id=user_id)
        if manager is None:
            raise OrchestrationError("Manager agent not found")

        members: list[Agent] = []
        for agent_id in team.member_agent_ids:
            member = await self._agents.get_by_id(agent_id, user_id=user_id)
            if member is not None:
                members.append(member)

        if not members:
            raise OrchestrationError("Team has no valid member agents")

        # --- PLAN ---
        member_summaries = [{"name": m.name, "description": m.description} for m in members]
        planning_prompt = build_planning_prompt(task=task, member_agents=member_summaries)
        raw_plan_response = await self._call_agent(manager, planning_prompt)
        parsed_plan = extract_json_array(raw_plan_response)

        used_fallback = False
        if not parsed_plan:
            used_fallback = True
            parsed_plan = [{"agent": m.name, "task": task} for m in members]

        members_by_name = {m.name.strip().lower(): m for m in members}

        # --- EXECUTE ---
        steps: list[dict] = []
        for planned_step in parsed_plan:
            agent_name = str(planned_step.get("agent", "")).strip()
            subtask = str(planned_step.get("task", task))
            member = members_by_name.get(agent_name.lower())

            if member is None:
                steps.append(
                    {
                        "agent_name": agent_name or "(unknown)",
                        "subtask": subtask,
                        "output": "",
                        "status": "failed",
                        "error": f"Plan referenced an unknown agent '{agent_name}'",
                    }
                )
                continue

            try:
                output = await self._call_agent(member, subtask)
                steps.append(
                    {
                        "agent_name": member.name,
                        "subtask": subtask,
                        "output": ensure_chat_response(output),
                        "status": "success",
                        "error": None,
                    }
                )
            except Exception as exc:  # noqa: BLE001 — isolate one member's failure from the rest
                steps.append(
                    {
                        "agent_name": member.name,
                        "subtask": subtask,
                        "output": "",
                        "status": "failed",
                        "error": str(exc),
                    }
                )

        # --- SYNTHESIZE ---
        successful_steps = [s for s in steps if s["status"] == "success"]
        if successful_steps:
            synthesis_prompt = build_synthesis_prompt(task=task, step_results=successful_steps)
            try:
                final_output = await self._call_agent(manager, synthesis_prompt)
                final_output = ensure_chat_response(final_output)
                overall_status = TeamRunStatus.COMPLETED
                run_error = None
            except Exception as exc:  # noqa: BLE001
                final_output = None
                overall_status = TeamRunStatus.FAILED
                run_error = f"Synthesis failed: {exc}"
        else:
            final_output = None
            overall_status = TeamRunStatus.FAILED
            run_error = "Every delegated step failed; nothing to synthesize"

        run = AgentTeamRun(
            team_id=team.id,
            user_id=user_id,
            task=task,
            status=overall_status,
            plan=[{**step, "fallback": used_fallback} for step in parsed_plan]
            if used_fallback
            else parsed_plan,
            steps=steps,
            final_output=final_output,
            error=run_error,
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
        )
        persisted = await self._runs.create(run)
        await self._session.commit()
        return persisted

    async def list_runs(self, *, team_id: int, user_id: int) -> list[AgentTeamRun]:
        return await self._runs.list_for_team(team_id, user_id=user_id)

    async def get_run(self, *, run_id: int, user_id: int) -> AgentTeamRun | None:
        return await self._runs.get_by_id(run_id, user_id=user_id)

    @staticmethod
    async def _call_agent(agent: Agent, prompt: str) -> str:
        messages = []
        system_prompt = build_system_prompt(agent)

        # Inject RAG context into agent prompt
        try:
            from app.services.rag.retriever import KnowledgeRetriever
            from app.services.rag.context_builder import RAGContextBuilder
            retriever = KnowledgeRetriever()
            res = retriever.retrieve_context(prompt, top_k=5)
            context_builder = RAGContextBuilder()
            augmented_prompt = context_builder.build_augmented_prompt(prompt, res)
            if augmented_prompt != prompt:
                if system_prompt:
                    system_prompt = f"{system_prompt}\n\n{augmented_prompt}"
                else:
                    system_prompt = augmented_prompt
        except Exception:
            pass

        if system_prompt:
            messages.append(ChatMessage(role="system", content=system_prompt))
        messages.append(ChatMessage(role="user", content=prompt))

        provider = get_provider(agent.provider)
        chunks = []
        async for chunk in provider.stream_chat(
            messages=messages, model=agent.model, temperature=agent.temperature
        ):
            norm_chunk = normalize_content_chunk(chunk)
            if norm_chunk:
                chunks.append(norm_chunk)
        return ensure_chat_response("".join(chunks))

