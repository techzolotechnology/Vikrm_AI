"""
Planner Specialist Agent.
Responsible for converting RequirementSpec into a ProjectPlan and TaskGraph DAG.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from app.services.project.requirement_analysis_service import RequirementSpec
from app.services.project.architecture_planner import ArchitecturePlanner, ProjectPlan
from app.services.project.task_graph_builder import TaskGraphBuilder, TaskGraph, TaskNode
from app.services.project.llm_orchestrator import LLMOrchestrator
from app.core.logging import get_logger

logger = get_logger(__name__)


class PlannerInput(BaseModel):
    spec: RequirementSpec


class PlannerOutput(BaseModel):
    plan: ProjectPlan
    tasks: List[TaskNode]
    agent_notes: str = "Architecture plan and DAG successfully generated."


class PlannerAgent:
    def __init__(self, orchestrator: Optional[LLMOrchestrator] = None) -> None:
        self.orchestrator = orchestrator or LLMOrchestrator()
        self.arch_planner = ArchitecturePlanner(orchestrator=self.orchestrator)

    async def execute(self, inp: PlannerInput) -> PlannerOutput:
        plan: ProjectPlan = await self.arch_planner.plan_architecture(inp.spec)
        graph: TaskGraph = TaskGraphBuilder.build_graph(inp.spec, plan)
        task_nodes = list(graph.nodes.values())
        return PlannerOutput(plan=plan, tasks=task_nodes)
