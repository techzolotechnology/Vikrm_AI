"""
Frontend Specialist Agent.
Generates React 19 + TypeScript components, pages, hooks, state contexts, and routes.
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


class FrontendAgentInput(BaseModel):
    spec: RequirementSpec
    plan: ProjectPlan
    existing_files: Dict[str, str] = Field(default_factory=dict)


class FrontendAgentOutput(BaseModel):
    generated_files: Dict[str, str] = Field(default_factory=dict)
    components_created: List[str] = Field(default_factory=list)
    agent_notes: str = "Frontend UI components and pages synthesized."


class FrontendAgent:
    def __init__(self, orchestrator: Optional[LLMOrchestrator] = None) -> None:
        self.orchestrator = orchestrator or LLMOrchestrator()

    async def execute(self, inp: FrontendAgentInput) -> FrontendAgentOutput:
        prompt = (
            f"You are the Frontend Lead AI Agent.\n"
            f"Target App: {inp.plan.name} ({inp.spec.domain})\n"
            f"Features: {', '.join(inp.spec.features)}\n"
            f"Generate React 19 + TypeScript frontend files (e.g. src/App.tsx, src/pages/DashboardPage.tsx, src/components/Header.tsx).\n"
            f"Use markdown file headers: ### path/to/file.ext followed by code blocks."
        )

        messages = [
            ChatMessage(role="system", content="Generate complete production React 19 + Tailwind CSS frontend code files."),
            ChatMessage(role="user", content=prompt),
        ]

        gen_files: Dict[str, str] = {}
        components: List[str] = []

        try:
            response = await self.orchestrator.chat(messages=messages, temperature=0.2)
            file_regex = r"###\s+([^\n]+)\s*\n+```(\w+)?\n([\s\S]*?)```"
            matches = re.findall(file_regex, response)
            for m in matches:
                p_clean = m[0].strip().replace("`", "").replace("./", "")
                code = m[2].strip()
                gen_files[p_clean] = code
                if "/components/" in p_clean or "/pages/" in p_clean:
                    components.append(p_clean)
        except Exception as exc:
            logger.warning("[FrontendAgent] Synthesis error: %s", exc)

        if not gen_files:
            gen_files["src/App.tsx"] = (
                "import React from 'react';\n\n"
                f"export default function App() {{\n"
                f"  return (\n"
                f"    <div className='min-h-screen bg-slate-900 text-white p-8'>\n"
                f"      <h1 className='text-3xl font-bold'>{inp.plan.name}</h1>\n"
                f"      <p className='mt-2 text-slate-400'>{inp.spec.description}</p>\n"
                f"    </div>\n"
                f"  );\n"
                f"}}\n"
            )
            components.append("src/App.tsx")

        return FrontendAgentOutput(generated_files=gen_files, components_created=components)
