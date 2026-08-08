"""
Architecture Planner & Dynamic Stack Inference Engine for Vikrm AI Platform.

Phase 2: Derives ProjectPlan and per-stack justifications dynamically from RequirementSpec
via LLMOrchestrator structured output, replacing fixed static per-domain dictionary lookups.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.services.project.planning_agent import PlanningAgent, AgentPlan
from app.services.project.requirement_analysis_service import RequirementSpec, RequirementAnalysisService
from app.services.project.llm_orchestrator import LLMOrchestrator
from app.services.llm.base import ChatMessage
from app.core.logging import get_logger

logger = get_logger(__name__)


class TechStack(BaseModel):
    framework: str = Field("React 19 + TypeScript + FastAPI", description="Frontend & backend framework")
    framework_justification: str = Field("", description="Justification for chosen framework")
    language: str = Field("TypeScript / Python", description="Primary languages")
    runtime: str = Field("Node.js 20 / Python 3.11", description="Execution runtime")
    database: str = Field("PostgreSQL", description="System database")
    database_justification: str = Field("", description="Justification for chosen database")
    authentication: str = Field("JWT + OAuth2", description="Authentication & RBAC model")
    auth_justification: str = Field("", description="Justification for auth strategy")
    css_framework: str = Field("Tailwind CSS", description="Styling engine")
    build_tool: str = Field("Vite + tsc", description="Build bundler")
    deployment_target: str = Field("Docker + Vercel", description="Target release platform")
    deployment_justification: str = Field("", description="Justification for deployment platform")
    key_dependencies: List[str] = Field(default_factory=list, description="Third-party package dependencies")


class ProjectPlan(BaseModel):
    name: str
    description: str
    domain: str
    complexity: str
    tech_stack: TechStack
    planned_files: int
    estimated_files: int
    modules: List[str]
    folder_hierarchy: List[str]
    justifications: Dict[str, str] = Field(default_factory=dict, description="Detailed architecture rationale")


class ArchitecturePlanner:
    def __init__(self, orchestrator: Optional[LLMOrchestrator] = None) -> None:
        self.orchestrator = orchestrator or LLMOrchestrator()

    async def plan_architecture(self, spec: RequirementSpec) -> ProjectPlan:
        """
        Dynamically generates a ProjectPlan with architectural justifications derived from RequirementSpec.
        """
        messages = [
            ChatMessage(
                role="system",
                content=(
                    "You are a Lead Software Architect. Given a structured RequirementSpec, design a tailored production "
                    "architecture and ProjectPlan. Provide explicit architectural justifications for why the database, framework, "
                    "auth strategy, and deployment targets were selected based on the user's specific features and non-functional requirements."
                ),
            ),
            ChatMessage(
                role="user",
                content=f"RequirementSpec:\n{spec.model_dump_json(indent=2)}",
            ),
        ]

        try:
            plan = await self.orchestrator.chat_structured(messages=messages, schema_model=ProjectPlan)
            return plan
        except Exception as exc:
            logger.warning("[ArchitecturePlanner] LLM planning warning: %s. Falling back to agent plan.", exc)
            # Fallback to AgentPlan if LLM call fails
            agent_plan = PlanningAgent.plan(spec.raw_prompt or spec.description)
            justifications = {
                "framework": f"Selected {agent_plan.framework} to match domain {spec.domain} requirements.",
                "database": f"Selected {agent_plan.database} for entity models: {', '.join(spec.entities[:3])}.",
                "auth": f"Selected {agent_plan.auth_strategy} to secure features: {', '.join(spec.features[:3])}.",
                "deployment": f"Selected {agent_plan.deployment_target} for production readiness."
            }
            stack = TechStack(
                framework=agent_plan.framework,
                framework_justification=justifications["framework"],
                database=agent_plan.database,
                database_justification=justifications["database"],
                authentication=agent_plan.auth_strategy,
                auth_justification=justifications["auth"],
                deployment_target=agent_plan.deployment_target,
                deployment_justification=justifications["deployment"],
                key_dependencies=agent_plan.key_dependencies,
            )
            return ProjectPlan(
                name=agent_plan.project_name,
                description=agent_plan.description,
                domain=agent_plan.domain,
                complexity=agent_plan.complexity,
                tech_stack=stack,
                planned_files=agent_plan.planned_files,
                estimated_files=agent_plan.planned_files,
                modules=agent_plan.modules,
                folder_hierarchy=agent_plan.folder_structure,
                justifications=justifications,
            )

    @staticmethod
    def infer_and_plan(prompt: str) -> ProjectPlan:
        """Synchronous wrapper for backward compatibility."""
        agent_plan = PlanningAgent.plan(prompt)

        justifications = {
            "framework": f"Selected {agent_plan.framework} for domain {agent_plan.domain}.",
            "database": f"Selected {agent_plan.database} relational storage.",
            "auth": f"Selected {agent_plan.auth_strategy} security model.",
            "deployment": f"Selected {agent_plan.deployment_target} container target."
        }

        stack = TechStack(
            framework=agent_plan.framework,
            framework_justification=justifications["framework"],
            database=agent_plan.database,
            database_justification=justifications["database"],
            authentication=agent_plan.auth_strategy,
            auth_justification=justifications["auth"],
            deployment_target=agent_plan.deployment_target,
            deployment_justification=justifications["deployment"],
            key_dependencies=agent_plan.key_dependencies,
        )

        return ProjectPlan(
            name=agent_plan.project_name,
            description=agent_plan.description,
            domain=agent_plan.domain,
            complexity=agent_plan.complexity,
            tech_stack=stack,
            planned_files=agent_plan.planned_files,
            estimated_files=agent_plan.planned_files,
            modules=agent_plan.modules,
            folder_hierarchy=agent_plan.folder_structure,
            justifications=justifications,
        )
