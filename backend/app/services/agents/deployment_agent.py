"""
Deployment Specialist Agent.
Generates Dockerfile, docker-compose.yml, GitHub Actions workflows, and Kubernetes manifests.
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


class DeploymentAgentInput(BaseModel):
    spec: RequirementSpec
    plan: ProjectPlan


class DeploymentAgentOutput(BaseModel):
    generated_files: Dict[str, str] = Field(default_factory=dict)
    configs_created: List[str] = Field(default_factory=list)
    agent_notes: str = "Deployment manifests (Dockerfile, docker-compose.yml, CI workflows) synthesized."


class DeploymentAgent:
    def __init__(self, orchestrator: Optional[LLMOrchestrator] = None) -> None:
        self.orchestrator = orchestrator or LLMOrchestrator()

    async def execute(self, inp: DeploymentAgentInput) -> DeploymentAgentOutput:
        prompt = (
            f"You are the DevOps & Deployment AI Agent.\n"
            f"Target App: {inp.plan.name} ({inp.spec.domain})\n"
            f"Deployment Target: {inp.plan.tech_stack.deployment_target}\n"
            f"Generate Dockerfile, docker-compose.yml, and .github/workflows/ci.yml.\n"
            f"Use markdown file headers: ### path/to/file.ext followed by code blocks."
        )

        messages = [
            ChatMessage(role="system", content="Generate complete production Docker container and CI/CD workflow manifests."),
            ChatMessage(role="user", content=prompt),
        ]

        gen_files: Dict[str, str] = {}
        configs: List[str] = []

        try:
            response = await self.orchestrator.chat(messages=messages, temperature=0.1)
            file_regex = r"###\s+([^\n]+)\s*\n+```(\w+)?\n([\s\S]*?)```"
            matches = re.findall(file_regex, response)
            for m in matches:
                p_clean = m[0].strip().replace("`", "").replace("./", "")
                code = m[2].strip()
                gen_files[p_clean] = code
                configs.append(p_clean)
        except Exception as exc:
            logger.warning("[DeploymentAgent] Synthesis error: %s", exc)

        if not gen_files:
            gen_files["Dockerfile"] = (
                "FROM node:20-alpine AS builder\n"
                "WORKDIR /app\n"
                "COPY package.json package-lock.json* ./\n"
                "RUN npm ci || npm install\n"
                "COPY . .\n"
                "RUN npm run build\n"
                "EXPOSE 3000\n"
                "CMD [\"npm\", \"run\", \"dev\"]\n"
            )
            gen_files["docker-compose.yml"] = (
                "version: '3.8'\n\n"
                "services:\n"
                "  web:\n"
                "    build: .\n"
                "    ports:\n"
                "      - \"3000:3000\"\n"
                "    environment:\n"
                "      - NODE_ENV=production\n"
            )
            configs.extend(["Dockerfile", "docker-compose.yml"])

        return DeploymentAgentOutput(generated_files=gen_files, configs_created=configs)
