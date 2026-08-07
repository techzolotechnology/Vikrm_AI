"""
Code Synthesis Engine.
Generates complete production feature files by invoking LLMOrchestrator in topological batches.
"""

import time
import re
from typing import Dict, List, Optional
from app.services.project.planning_agent import AgentPlan
from app.services.project.task_graph_builder import TaskNode
from app.services.project.llm_orchestrator import LLMOrchestrator
from app.services.llm.base import ChatMessage
from app.core.logging import get_logger

logger = get_logger(__name__)


class CodeSynthesisEngine:
    def __init__(self, orchestrator: Optional[LLMOrchestrator] = None) -> None:
        self.orchestrator = orchestrator or LLMOrchestrator()

    async def generate_batch(
        self,
        batch: List[TaskNode],
        plan: AgentPlan,
        existing_files: Dict[str, str],
        provider_name: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Dict[str, str]:
        """
        Generates production code for a batch of TaskNodes using LLMOrchestrator.
        Incorporate plan.rag_context into the LLM prompt.
        """
        batch_files: List[str] = []
        for node in batch:
            batch_files.extend(node.files)

        batch_name = ", ".join(node.name for node in batch[:3])
        existing_manifest = "\n".join(f"- {path}" for path in list(existing_files.keys())[:30])

        rag_section = ""
        if hasattr(plan, "rag_context") and plan.rag_context:
            rag_docs_str = "\n".join(f"- {doc[:300]}" for doc in plan.rag_context[:3])
            rag_section = f"\nRetrieved RAG Context:\n{rag_docs_str}\n"

        prompt = (
            f"You are Vikrm AI Code Synthesis Engine.\n"
            f"Batch Target: {batch_name}\n"
            f"Project: {plan.project_name} ({plan.domain})\n"
            f"Framework: {plan.framework} + {plan.database}\n"
            f"Files to generate:\n" + "\n".join(f"- {f}" for f in batch_files) + "\n"
            f"Existing Workspace Files:\n{existing_manifest}\n"
            f"{rag_section}\n"
            f"Output complete, production-grade source code for each target file. "
            f"Use markdown file headers: ### path/to/file.ext followed by code fences ```lang ... ```."
        )

        messages = [
            ChatMessage(
                role="system",
                content="Generate complete production-grade source files with markdown headers (### path/to/file.ext). Zero placeholders, zero TODOs.",
            ),
            ChatMessage(role="user", content=prompt),
        ]

        synthesized_files: Dict[str, str] = {}
        try:
            response = await self.orchestrator.chat(
                messages=messages,
                provider_name=provider_name,
                model=model,
                temperature=0.2,
            )
            file_regex = r"###\s+([^\n]+)\s*\n+```(\w+)?\n([\s\S]*?)```"
            matches = re.findall(file_regex, response)
            for m in matches:
                p_clean = m[0].strip().replace("`", "").replace("./", "")
                synthesized_files[p_clean] = m[2].strip()
        except Exception as exc:
            logger.warning("[CodeSynthesisEngine] Batch synthesis warning (%s): %s", batch_name, exc)

        return synthesized_files
