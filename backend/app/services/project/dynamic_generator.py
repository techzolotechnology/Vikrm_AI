"""
Dynamic Production Code Synthesizer for Vikrm AI Platform.
Synthesizes multi-file production applications based on ProjectPlan
from ArchitecturePlanner and orders them with DependencyGraphResolver.
Fully dynamic per-feature synthesis without artificial file limits.
"""

from typing import Any, Dict
from app.services.project.architecture_planner import ArchitecturePlanner, ProjectPlan
from app.services.project.planning_agent import PlanningAgent
from app.services.project.code_synthesizer import LLMCodeSynthesizer
from app.services.project.dependency_graph import DependencyGraphResolver

class DynamicProjectGenerator:
    @classmethod
    def generate_project(cls, prompt: str) -> Dict[str, Any]:
        """
        Dynamically plans and builds a complete multi-file production project.
        Returns dict containing 'plan' (ProjectPlan) and 'files' (Dict[str, str]).
        """
        plan = ArchitecturePlanner.infer_and_plan(prompt)
        agent_plan = PlanningAgent.plan(prompt)
        files = LLMCodeSynthesizer.synthesize(agent_plan)
        sorted_files = DependencyGraphResolver.sort_files(files)

        return {
            "plan": plan,
            "agent_plan": agent_plan,
            "files": sorted_files
        }
