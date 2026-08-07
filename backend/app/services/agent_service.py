"""
Agent service.

`build_system_prompt` is the one piece of real "business logic" here:
it combines an agent's instructions/goal/personality into a single
system message. Kept as a pure function (not stored pre-concatenated
on the model) so editing any one field takes effect immediately on the
next message, without a migration or backfill.
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.agent import Agent, AgentStatus
from app.repositories.agent_repository import AgentRepository


class AgentServiceError(Exception):
    pass


def build_system_prompt(agent: Agent) -> str | None:
    parts: list[str] = []
    if agent.instructions:
        parts.append(agent.instructions.strip())
    if agent.goal:
        parts.append(f"Your goal: {agent.goal.strip()}")
    if agent.personality:
        parts.append(f"Personality and tone: {agent.personality.strip()}")

    if not parts:
        return None
    return "\n\n".join(parts)


class AgentService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._agents = AgentRepository(session)

    async def create_agent(self, *, user_id: int, data: dict) -> Agent:
        agent = await self._agents.create(user_id=user_id, **data)
        await self._session.commit()
        return agent

    async def list_agents(self, *, user_id: int, include_archived: bool = False) -> list[Agent]:
        return await self._agents.list_for_user(user_id, include_archived=include_archived)

    async def get_agent(self, *, agent_id: int, user_id: int) -> Agent | None:
        return await self._agents.get_by_id(agent_id, user_id=user_id)

    async def update_agent(self, *, agent: Agent, data: dict) -> Agent:
        if "status" in data and data["status"] is not None:
            data["status"] = AgentStatus(data["status"])
        updated = await self._agents.update(agent, **data)
        await self._session.commit()
        return updated

    async def delete_agent(self, *, agent: Agent) -> None:
        await self._agents.delete(agent)
        await self._session.commit()

    async def duplicate_agent(self, *, agent: Agent, user_id: int) -> Agent:
        new_data = {
            "name": f"{agent.name} (Copy)",
            "description": agent.description,
            "instructions": agent.instructions,
            "goal": agent.goal,
            "personality": agent.personality,
            "provider": agent.provider,
            "model": agent.model,
            "temperature": agent.temperature,
            "max_tokens": agent.max_tokens,
            "avatar_color": getattr(agent, "avatar_color", "#7C3AED"),
            "status": AgentStatus.ACTIVE,
        }
        new_agent = await self._agents.create(user_id=user_id, **new_data)
        await self._session.commit()
        return new_agent

    async def seed_specialized_agents(self, *, user_id: int) -> list[Agent]:
        existing = await self._agents.list_for_user(user_id)
        existing_names = {a.name for a in existing}

        SPECIALIZED_ROSTER = [
            {"name": "Planner Agent", "description": "Deconstructs requirements into system specs and execution DAG", "instructions": "You are Lead Engineering Planner. Breakdown requirements into clear execution phases.", "color": "#7C3AED"},
            {"name": "Architect Agent", "description": "Designs system architecture, API schemas, and component structure", "instructions": "You are Principal Architect. Define modular class hierarchy and system design.", "color": "#06B6D4"},
            {"name": "Frontend Developer Agent", "description": "Generates modern React, Vue, HTML/CSS component interfaces", "instructions": "You are Senior Frontend Engineer. Build sleek glassmorphic UI code.", "color": "#EC4899"},
            {"name": "Backend Developer Agent", "description": "Writes FastAPI, Node, Express, Spring Boot REST/GraphQL microservices", "instructions": "You are Lead Backend Engineer. Implement robust async endpoints.", "color": "#22C55E"},
            {"name": "Database Engineer Agent", "description": "Constructs SQL schemas, ORM models, and database migration scripts", "instructions": "You are Senior Database Architect. Write optimized SQL and migration code.", "color": "#F59E0B"},
            {"name": "API Engineer Agent", "description": "Builds OpenAPI specifications, client SDKs, and payload validation", "instructions": "You are API Design Lead. Construct strict JSON schemas and REST contracts.", "color": "#3B82F6"},
            {"name": "DevOps Engineer Agent", "description": "Generates Dockerfiles, docker-compose configurations, and CI/CD pipelines", "instructions": "You are DevOps & Cloud Engineer. Construct containerized deployment files.", "color": "#6366F1"},
            {"name": "Security Engineer Agent", "description": "Performs security audits, dependency vulnerability scans, and auth hardening", "instructions": "You are Chief Security Officer. Scan code for vulnerabilities and secret leaks.", "color": "#EF4444"},
            {"name": "QA Engineer Agent", "description": "Writes comprehensive unit, integration, and E2E automated test suites", "instructions": "You are QA Automation Lead. Generate complete PyTest and Jest tests.", "color": "#14B8A6"},
            {"name": "Documentation Writer Agent", "description": "Generates README documentation, API guides, and architecture inline specs", "instructions": "You are Technical Documentation Lead. Write clean GitHub Markdown docs.", "color": "#8B5CF6"},
            {"name": "Deployment Agent", "description": "Orchestrates Vercel, Netlify, Docker, and Kubernetes production releases", "instructions": "You are Site Reliability Lead. Package build artifacts for release.", "color": "#10B981"},
        ]

        created = []
        for spec in SPECIALIZED_ROSTER:
            if spec["name"] not in existing_names:
                ag = await self._agents.create(
                    user_id=user_id,
                    name=spec["name"],
                    description=spec["description"],
                    instructions=spec["instructions"],
                    goal=f"Fulfill {spec['name']} responsibilities in multi-agent software engineering team.",
                    personality="Professional, thorough, production-grade engineer.",
                    provider="openai",
                    model="gpt-4o",
                    temperature=0.3,
                    avatar_color=spec["color"],
                )
                created.append(ag)
        await self._session.commit()
        return created

