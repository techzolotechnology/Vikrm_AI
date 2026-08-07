"""
Architecture Planner & Stack Inference Engine for Vikrm AI Platform.
Dynamically infers stack, database, authentication model, folder hierarchy,
build tools, and deployment targets based on prompt domain intent.
Fully integrated with PlanningAgent for unlimited dynamic file scaling.
"""

from typing import Any, Dict, List
from pydantic import BaseModel, Field
from app.services.project.planning_agent import PlanningAgent

class TechStack(BaseModel):
    framework: str
    language: str = "TypeScript"
    runtime: str = "Node.js / Python"
    database: str = "SQLite / PostgreSQL"
    authentication: str = "JWT / OAuth2"
    css_framework: str = "Tailwind CSS"
    build_tool: str = "Vite"
    deployment_target: str = "Docker / Vercel"
    key_dependencies: List[str] = Field(default_factory=list)

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

class ArchitecturePlanner:
    @staticmethod
    def infer_and_plan(prompt: str) -> ProjectPlan:
        agent_plan = PlanningAgent.plan(prompt)
        
        stack = TechStack(
            framework=agent_plan.framework,
            database=agent_plan.database,
            authentication=agent_plan.auth_strategy,
            key_dependencies=agent_plan.key_dependencies
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
            folder_hierarchy=agent_plan.folder_structure
        )
