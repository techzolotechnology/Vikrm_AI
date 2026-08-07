"""
Manager agent planning.

The manager agent is prompted to respond with a JSON array describing
which member agent handles which subtask, in what order. Real models
don't always return clean JSON (preamble text, markdown code fences,
trailing commentary), so `extract_json_array` searches for the first
balanced `[...]` substring rather than assuming the entire response is
parseable JSON — and returns `None` (not an exception) on failure, so
the caller can apply a documented, visible fallback instead of the
orchestration silently crashing on a slightly-off model response.
"""
import json


def build_planning_prompt(*, task: str, member_agents: list[dict]) -> str:
    roster = "\n".join(f"- {a['name']}: {a['description'] or 'No description'}" for a in member_agents)
    return (
        "You are coordinating a team of specialist agents to complete a task. "
        "Break the task into subtasks and assign each to the most suitable agent.\n\n"
        f"Available agents:\n{roster}\n\n"
        f"Task: {task}\n\n"
        "Respond with ONLY a JSON array, no other text, in this exact format:\n"
        '[{"agent": "<agent name from the list above>", "task": "<specific subtask for that agent>"}]\n'
        "Use as many or as few steps as the task genuinely requires."
    )


def extract_json_array(text: str) -> list | None:
    start = text.find("[")
    if start == -1:
        return None

    depth = 0
    for i in range(start, len(text)):
        if text[i] == "[":
            depth += 1
        elif text[i] == "]":
            depth -= 1
            if depth == 0:
                candidate = text[start : i + 1]
                try:
                    parsed = json.loads(candidate)
                except json.JSONDecodeError:
                    return None
                return parsed if isinstance(parsed, list) else None
    return None


from app.services.llm.base import normalize_content_chunk


def build_synthesis_prompt(*, task: str, step_results: list[dict]) -> str:
    results_text = "\n\n".join(
        f"[{s['agent_name']}] (subtask: {s['subtask']})\n{normalize_content_chunk(s['output'])}"
        for s in step_results
        if s.get("status") == "success"
    )
    return (
        f"You coordinated a team to complete this task: {task}\n\n"
        f"Here is what each team member produced:\n\n{results_text}\n\n"
        "Synthesize these into a single, coherent final answer to the original task."
    )
