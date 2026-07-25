from app.services.orchestration.planning import (
    build_planning_prompt,
    build_synthesis_prompt,
    extract_json_array,
)


def test_extract_clean_json_array() -> None:
    result = extract_json_array('[{"agent": "A", "task": "do X"}]')
    assert result == [{"agent": "A", "task": "do X"}]


def test_extract_json_with_preamble_and_markdown_fences() -> None:
    messy = (
        "Sure, here's the plan:\n```json\n"
        '[{"agent": "Research Agent", "task": "find data"}, '
        '{"agent": "Writer Agent", "task": "write summary"}]\n'
        "```\nLet me know if that works!"
    )
    result = extract_json_array(messy)
    assert result == [
        {"agent": "Research Agent", "task": "find data"},
        {"agent": "Writer Agent", "task": "write summary"},
    ]


def test_extract_json_returns_none_for_no_json() -> None:
    assert extract_json_array("I cannot help with that request.") is None


def test_extract_json_returns_none_for_malformed_json() -> None:
    assert extract_json_array('[{"agent": "X", "task": }]') is None


def test_extract_json_returns_none_for_non_array_json() -> None:
    assert extract_json_array('{"agent": "X"}') is None


def test_extract_json_handles_nested_brackets_in_strings() -> None:
    text = '[{"agent": "A", "task": "process [1, 2, 3]"}]'
    result = extract_json_array(text)
    assert result == [{"agent": "A", "task": "process [1, 2, 3]"}]


def test_planning_prompt_includes_task_and_roster() -> None:
    prompt = build_planning_prompt(
        task="Write a report",
        member_agents=[
            {"name": "Researcher", "description": "Finds facts"},
            {"name": "Writer", "description": "Writes prose"},
        ],
    )
    assert "Write a report" in prompt
    assert "Researcher: Finds facts" in prompt
    assert "Writer: Writes prose" in prompt
    assert "JSON array" in prompt


def test_synthesis_prompt_includes_only_successful_steps() -> None:
    prompt = build_synthesis_prompt(
        task="Summarize the market",
        step_results=[
            {"agent_name": "A", "subtask": "research", "output": "Market grew 5%", "status": "success"},
            {"agent_name": "B", "subtask": "analyze", "output": "", "status": "failed"},
        ],
    )
    assert "Market grew 5%" in prompt
    assert "[A]" in prompt
    assert "[B]" not in prompt
