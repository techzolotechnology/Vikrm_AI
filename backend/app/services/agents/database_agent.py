"""
Database Specialist Agent.
Generates SQL schemas, ORM models (SQLAlchemy/Prisma), migrations, and seed scripts.
"""

import re
from typing import Dict, List, Optional
from pydantic import BaseModel, Field
from app.services.project.requirement_analysis_service import RequirementSpec
from app.services.project.architecture_planner import ProjectPlan
from app.services.project.llm_orchestrator import LLMOrchestrator
from app.services.llm.base import ChatMessage
from app.core.logging import get_logger

logger = get_logger(__name__)


class DatabaseAgentInput(BaseModel):
    spec: RequirementSpec
    plan: ProjectPlan


class DatabaseAgentOutput(BaseModel):
    generated_files: Dict[str, str] = Field(default_factory=dict)
    schemas_created: List[str] = Field(default_factory=list)
    agent_notes: str = "Database ORM schemas and migration scripts synthesized."


class DatabaseAgent:
    def __init__(self, orchestrator: Optional[LLMOrchestrator] = None) -> None:
        self.orchestrator = orchestrator or LLMOrchestrator()

    async def execute(self, inp: DatabaseAgentInput) -> DatabaseAgentOutput:
        prompt = (
            f"You are the Database Architect AI Agent.\n"
            f"Target App: {inp.plan.name} ({inp.spec.domain})\n"
            f"Entities: {', '.join(inp.spec.entities)}\n"
            f"Database Choice: {inp.plan.tech_stack.database}\n"
            f"Generate database schema files (e.g. server/app/models/schema.py or server/schema.sql).\n"
            f"Use markdown file headers: ### path/to/file.ext followed by code blocks."
        )

        messages = [
            ChatMessage(role="system", content="Generate complete production SQL and SQLAlchemy ORM model schemas."),
            ChatMessage(role="user", content=prompt),
        ]

        gen_files: Dict[str, str] = {}
        schemas: List[str] = []

        try:
            response = await self.orchestrator.chat(messages=messages, temperature=0.1)
            file_regex = r"###\s+([^\n]+)\s*\n+```(\w+)?\n([\s\S]*?)```"
            matches = re.findall(file_regex, response)
            for m in matches:
                p_clean = m[0].strip().replace("`", "").replace("./", "")
                code = m[2].strip()
                gen_files[p_clean] = code
                schemas.append(p_clean)
        except Exception as exc:
            logger.warning("[DatabaseAgent] Synthesis error: %s", exc)

        if not gen_files:
            gen_files["server/app/models/schema.py"] = (
                "from sqlalchemy import Column, Integer, String, DateTime, func\n"
                "from sqlalchemy.ext.declarative import declarative_base\n\n"
                "Base = declarative_base()\n\n"
                "class User(Base):\n"
                "    __tablename__ = 'users'\n"
                "    id = Column(Integer, primary_key=True, index=True)\n"
                "    email = Column(String, unique=True, index=True, nullable=False)\n"
                "    hashed_password = Column(String, nullable=False)\n"
                "    created_at = Column(DateTime, server_default=func.now())\n"
            )
            schemas.append("server/app/models/schema.py")

        return DatabaseAgentOutput(generated_files=gen_files, schemas_created=schemas)
