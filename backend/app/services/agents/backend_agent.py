"""
Backend Specialist Agent.
Generates FastAPI/Express backend API endpoints, schemas, controllers, and business logic files.
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


class BackendAgentInput(BaseModel):
    spec: RequirementSpec
    plan: ProjectPlan
    existing_files: Dict[str, str] = Field(default_factory=dict)


class BackendAgentOutput(BaseModel):
    generated_files: Dict[str, str] = Field(default_factory=dict)
    api_endpoints: List[str] = Field(default_factory=list)
    agent_notes: str = "Backend REST API routes and services synthesized."


class BackendAgent:
    def __init__(self, orchestrator: Optional[LLMOrchestrator] = None) -> None:
        self.orchestrator = orchestrator or LLMOrchestrator()

    async def execute(self, inp: BackendAgentInput) -> BackendAgentOutput:
        prompt = (
            f"You are the Backend Lead AI Agent.\n"
            f"Target App: {inp.plan.name} ({inp.spec.domain})\n"
            f"Required Features: {', '.join(inp.spec.features)}\n"
            f"Domain Entities: {', '.join(inp.spec.entities)}\n"
            f"Generate backend server files (e.g. server/main.py, server/requirements.txt, server/app/api/routes.py).\n"
            f"Use markdown file headers: ### path/to/file.ext followed by code blocks."
        )

        messages = [
            ChatMessage(role="system", content="Generate complete, production-grade FastAPI / Python backend code files."),
            ChatMessage(role="user", content=prompt),
        ]

        gen_files: Dict[str, str] = {}
        endpoints: List[str] = []

        try:
            response = await self.orchestrator.chat(messages=messages, temperature=0.2)
            file_regex = r"###\s+([^\n]+)\s*\n+```(\w+)?\n([\s\S]*?)```"
            matches = re.findall(file_regex, response)
            for m in matches:
                p_clean = m[0].strip().replace("`", "").replace("./", "")
                code = m[2].strip()
                gen_files[p_clean] = code
                if "@app." in code or "router." in code:
                    ep_matches = re.findall(r'@(?:app|router)\.(get|post|put|delete)\("([^"]+)"\)', code)
                    endpoints.extend([f"{m_type.upper()} {url}" for m_type, url in ep_matches])
        except Exception as exc:
            logger.warning("[BackendAgent] Synthesis error: %s", exc)

        # Fallback guaranteed backend scaffold if LLM response parsing had no files
        if not gen_files:
            gen_files["server/main.py"] = (
                "from fastapi import FastAPI\n\n"
                f"app = FastAPI(title='{inp.plan.name} API')\n\n"
                "@app.get('/health')\ndef health():\n    return {'status': 'healthy'}\n"
            )
            gen_files["server/requirements.txt"] = "fastapi>=0.100.0\nuvicorn>=0.22.0\npydantic>=2.0\n"
            endpoints.append("GET /health")

        return BackendAgentOutput(generated_files=gen_files, api_endpoints=endpoints)
