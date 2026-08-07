"""
Documentation Specialist Agent.
Generates README.md, Swagger/OpenAPI docs, architecture specs, and API guides.
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


class DocumentationAgentInput(BaseModel):
    spec: RequirementSpec
    plan: ProjectPlan
    existing_files: Dict[str, str] = Field(default_factory=dict)


class DocumentationAgentOutput(BaseModel):
    generated_files: Dict[str, str] = Field(default_factory=dict)
    docs_created: List[str] = Field(default_factory=list)
    agent_notes: str = "Documentation (README.md, API specs) synthesized."


class DocumentationAgent:
    def __init__(self, orchestrator: Optional[LLMOrchestrator] = None) -> None:
        self.orchestrator = orchestrator or LLMOrchestrator()

    async def execute(self, inp: DocumentationAgentInput) -> DocumentationAgentOutput:
        prompt = (
            f"You are the Documentation AI Agent.\n"
            f"Target App: {inp.plan.name} ({inp.spec.domain})\n"
            f"Description: {inp.spec.description}\n"
            f"Features: {', '.join(inp.spec.features)}\n"
            f"Generate README.md and documentation files.\n"
            f"Use markdown file headers: ### path/to/file.ext followed by code blocks."
        )

        messages = [
            ChatMessage(role="system", content="Generate complete production README.md and technical documentation."),
            ChatMessage(role="user", content=prompt),
        ]

        gen_files: Dict[str, str] = {}
        docs: List[str] = []

        try:
            response = await self.orchestrator.chat(messages=messages, temperature=0.2)
            file_regex = r"###\s+([^\n]+)\s*\n+```(\w+)?\n([\s\S]*?)```"
            matches = re.findall(file_regex, response)
            for m in matches:
                p_clean = m[0].strip().replace("`", "").replace("./", "")
                code = m[2].strip()
                gen_files[p_clean] = code
                docs.append(p_clean)
        except Exception as exc:
            logger.warning("[DocumentationAgent] Synthesis error: %s", exc)

        if not gen_files:
            gen_files["README.md"] = (
                f"# {inp.plan.name}\n\n"
                f"{inp.spec.description}\n\n"
                "## Architecture\n\n"
                f"- **Framework**: {inp.plan.tech_stack.framework}\n"
                f"- **Database**: {inp.plan.tech_stack.database}\n"
                f"- **Auth**: {inp.plan.tech_stack.authentication}\n\n"
                "## Getting Started\n\n"
                "```bash\n"
                "npm install\n"
                "npm run dev\n"
                "```\n"
            )
            docs.append("README.md")

        return DocumentationAgentOutput(generated_files=gen_files, docs_created=docs)
