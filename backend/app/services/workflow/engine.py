"""
Workflow execution engine.

Executes a workflow definition (nodes + edges) starting from the
`start` node via graph traversal. Validates cycles, topological order,
resolves node outputs and template variables, and records detailed step telemetry.
"""
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone

from app.core.config import settings
from app.repositories.agent_repository import AgentRepository
from app.services.agent_service import build_system_prompt
from app.services.llm.base import ChatMessage, ProviderError
from app.services.llm.registry import get_provider
from app.services.tools.base import ToolContext, ToolError
from app.services.tools.registry import get_tool
from app.services.workflow.conditions import ConditionError, evaluate_condition
from app.services.workflow.templating import resolve_template


class WorkflowValidationError(Exception):
    pass


@dataclass
class StepResult:
    node_id: str
    node_type: str
    status: str  # "success" | "failed"
    input_summary: str
    output: str
    error: str | None
    started_at: datetime
    completed_at: datetime


@dataclass
class WorkflowRunResult:
    status: str  # "completed" | "failed"
    final_output: str
    steps: list[StepResult] = field(default_factory=list)


class WorkflowEngine:
    def __init__(self, session, *, user_id: int) -> None:
        self._session = session
        self._user_id = user_id
        self._agents = AgentRepository(session)

    async def execute(self, definition: dict, *, initial_input: str) -> WorkflowRunResult:
        nodes = {n["id"]: n for n in definition.get("nodes", [])}
        edges = definition.get("edges", [])

        start_nodes = [n for n in nodes.values() if n["type"] == "start"]
        if len(start_nodes) != 1:
            raise WorkflowValidationError("Workflow must have exactly one 'start' node")

        adjacency: dict[str, list[dict]] = {}
        for edge in edges:
            adjacency.setdefault(edge["source"], []).append(edge)

        # Graph cycle detection
        visited_states: dict[str, int] = {}  # 0: unvisited, 1: visiting, 2: visited

        def has_cycle(nid: str) -> bool:
            visited_states[nid] = 1
            for edge in adjacency.get(nid, []):
                target = edge.get("target")
                if target and visited_states.get(target, 0) == 1:
                    return True
                if target and visited_states.get(target, 0) == 0:
                    if has_cycle(target):
                        return True
            visited_states[nid] = 2
            return False

        for nid in nodes:
            if visited_states.get(nid, 0) == 0:
                if has_cycle(nid):
                    raise WorkflowValidationError("Cycle detected in workflow graph")

        node_outputs: dict[str, str] = {}
        steps: list[StepResult] = []
        visited: set[str] = set()
        failed = False
        last_output = initial_input
        final_output: str | None = None

        queue: deque[str] = deque([start_nodes[0]["id"]])

        while queue:
            node_id = queue.popleft()
            if node_id in visited:
                continue
            visited.add(node_id)

            node = nodes.get(node_id)
            if node is None:
                continue

            started_at = datetime.now(timezone.utc)
            try:
                output = await self._execute_node(
                    node, initial_input=initial_input, node_outputs=node_outputs
                )
                status = "success"
                error = None
            except Exception as exc:
                output = ""
                status = "failed"
                error = str(exc)
                failed = True

            completed_at = datetime.now(timezone.utc)
            node_outputs[node_id] = output
            if status == "success":
                last_output = output
            if node["type"] in ("output", "end"):
                final_output = output

            steps.append(
                StepResult(
                    node_id=node_id,
                    node_type=node["type"],
                    status=status,
                    input_summary=self._summarize_input(node, initial_input, node_outputs),
                    output=output,
                    error=error,
                    started_at=started_at,
                    completed_at=completed_at,
                )
            )

            if status == "failed":
                continue  # Stop branch execution on failure

            for edge in adjacency.get(node_id, []):
                if node["type"] == "condition":
                    branch_taken = "true" if output == "true" else "false"
                    if edge.get("branch") and edge.get("branch") != branch_taken:
                        continue
                if edge["target"] not in visited:
                    queue.append(edge["target"])

        return WorkflowRunResult(
            status="failed" if failed else "completed",
            final_output=final_output if final_output is not None else last_output,
            steps=steps,
        )

    async def _execute_node(
        self, node: dict, *, initial_input: str, node_outputs: dict[str, str]
    ) -> str:
        node_type = node["type"]
        data = node.get("data", {})

        if node_type == "start":
            return initial_input

        if node_type == "llm":
            prompt = resolve_template(
                data.get("prompt", "{{input}}"), initial_input=initial_input, node_outputs=node_outputs
            )
            provider_name = data.get("provider", settings.DEFAULT_LLM_PROVIDER)
            provider = get_provider(provider_name)
            model = data.get("model", settings.DEFAULT_LLM_MODEL)
            temperature = float(data.get("temperature", 0.7))
            return await self._consume_stream(
                provider.stream_chat(
                    messages=[ChatMessage(role="user", content=prompt)],
                    model=model,
                    temperature=temperature,
                )
            )

        if node_type == "agent":
            agent_id = data.get("agent_id")
            if agent_id is None:
                raise WorkflowValidationError("Agent node is missing 'agent_id'")
            agent = await self._agents.get_by_id(int(agent_id), user_id=self._user_id)
            if agent is None:
                raise WorkflowValidationError(f"Agent {agent_id} not found")

            prompt = resolve_template(
                data.get("prompt", "{{input}}"), initial_input=initial_input, node_outputs=node_outputs
            )
            messages = []
            system_prompt = build_system_prompt(agent)
            if system_prompt:
                messages.append(ChatMessage(role="system", content=system_prompt))
            messages.append(ChatMessage(role="user", content=prompt))

            provider = get_provider(agent.provider)
            return await self._consume_stream(
                provider.stream_chat(messages=messages, model=agent.model, temperature=agent.temperature)
            )

        if node_type == "condition":
            result = evaluate_condition(
                left=data.get("left", "{{input}}"),
                operator=data.get("operator", "is_not_empty"),
                right=data.get("right"),
                initial_input=initial_input,
                node_outputs=node_outputs,
            )
            return "true" if result else "false"

        if node_type == "tool":
            tool_name = data.get("tool_name")
            if not tool_name:
                raise WorkflowValidationError("Tool node is missing 'tool_name'")
            tool_input = resolve_template(
                data.get("input", "{{input}}"), initial_input=initial_input, node_outputs=node_outputs
            )
            tool = get_tool(tool_name)
            context = ToolContext(user_id=self._user_id, session=self._session)
            return await tool.run(tool_input, context=context)

        if node_type in ("output", "end"):
            template = data.get("template", "{{input}}")
            return resolve_template(template, initial_input=initial_input, node_outputs=node_outputs)

        raise WorkflowValidationError(f"Unknown node type '{node_type}'")

    @staticmethod
    async def _consume_stream(stream) -> str:
        chunks = []
        async for chunk in stream:
            chunks.append(chunk)
        return "".join(chunks)

    @staticmethod
    def _summarize_input(node: dict, initial_input: str, node_outputs: dict[str, str]) -> str:
        data = node.get("data", {})
        template = data.get("prompt") or data.get("input") or data.get("left") or "{{input}}"
        resolved = resolve_template(template, initial_input=initial_input, node_outputs=node_outputs)
        return resolved[:300]
