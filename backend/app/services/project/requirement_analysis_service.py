"""
Requirement Analysis Service.
Parses user prompts into structured RequirementSpec, enforcing the Ambiguity Clarification Gate.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from app.services.project.llm_orchestrator import LLMOrchestrator
from app.services.llm.base import ChatMessage
from app.core.logging import get_logger

logger = get_logger(__name__)


class RequirementSpec(BaseModel):
    app_name: str = Field(..., description="Short name of the project")
    description: str = Field(..., description="High-level project description")
    domain: str = Field(..., description="Business domain, e.g. healthcare, ecommerce, fintech, etc.")
    features: List[str] = Field(default_factory=list, description="Explicit functional requirements")
    entities: List[str] = Field(default_factory=list, description="Key domain entities / data models")
    non_functional_requirements: List[str] = Field(default_factory=list, description="Performance, security, or compliance constraints")
    is_ambiguous: bool = Field(False, description="True if prompt is too vague or underspecified")
    clarification_questions: List[str] = Field(default_factory=list, description="Questions to ask user if ambiguous")
    raw_prompt: str = Field("", description="Original user prompt")


class RequirementAnalysisService:
    def __init__(self, orchestrator: Optional[LLMOrchestrator] = None) -> None:
        self.orchestrator = orchestrator or LLMOrchestrator()

    async def analyze_requirement(self, prompt: str) -> RequirementSpec:
        """
        Analyzes user requirements prompt via LLMOrchestrator structured output.
        Triggers ambiguity clarification gate when prompt lacks actionable detail.
        """
        prompt_clean = prompt.strip()
        words = prompt_clean.split()

        # Deterministic Ambiguity Gate for extremely brief / vague prompts
        if len(words) < 4 or prompt_clean.lower() in ("make app", "build site", "create website", "help me code", "build app"):
            return RequirementSpec(
                app_name="Unspecified Project",
                description="The prompt provided is too brief or ambiguous.",
                domain="general",
                features=[],
                entities=[],
                non_functional_requirements=[],
                is_ambiguous=True,
                clarification_questions=[
                    "What target domain or business problem does your application solve?",
                    "What key user features or workflows should be included?",
                    "Which tech stack or database preferences do you have (e.g. React, FastAPI, PostgreSQL)?"
                ],
                raw_prompt=prompt,
            )

        messages = [
            ChatMessage(
                role="system",
                content=(
                    "You are a Senior Principal Software Architect. Analyze the user's project requirement prompt "
                    "and produce a detailed RequirementSpec. Extract specific features, domain entities, and non-functional constraints. "
                    "If the prompt is missing critical context or is inherently ambiguous, set is_ambiguous=true and provide clarification_questions."
                ),
            ),
            ChatMessage(role="user", content=f"Requirement Prompt:\n{prompt}"),
        ]

        try:
            spec = await self.orchestrator.chat_structured(messages=messages, schema_model=RequirementSpec)
            spec.raw_prompt = prompt
            return spec
        except Exception as exc:
            logger.warning("[RequirementAnalysisService] LLM structured parsing warning: %s. Falling back to heuristic spec.", exc)
            # Fallback heuristic parser if LLM fails
            domain = "ecommerce" if "store" in prompt.lower() or "shop" in prompt.lower() else "general"
            return RequirementSpec(
                app_name="App " + prompt[:20].title().replace(" ", ""),
                description=prompt,
                domain=domain,
                features=[w.title() for w in words if len(w) > 4][:5],
                entities=["User", "Item"],
                non_functional_requirements=["High Availability", "JWT Authentication"],
                is_ambiguous=False,
                clarification_questions=[],
                raw_prompt=prompt,
            )
