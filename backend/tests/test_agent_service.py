from app.models.agent import Agent
from app.services.agent_service import build_system_prompt


def _agent(**overrides) -> Agent:
    defaults = dict(
        id=1,
        user_id=1,
        name="Test Agent",
        instructions=None,
        goal=None,
        personality=None,
    )
    defaults.update(overrides)
    return Agent(**defaults)


def test_no_fields_returns_none() -> None:
    assert build_system_prompt(_agent()) is None


def test_instructions_only() -> None:
    prompt = build_system_prompt(_agent(instructions="Be concise."))
    assert prompt == "Be concise."


def test_combines_all_fields_in_order() -> None:
    prompt = build_system_prompt(
        _agent(
            instructions="You are a research assistant.",
            goal="Find accurate, cited information.",
            personality="Formal and precise.",
        )
    )
    assert prompt == (
        "You are a research assistant.\n\n"
        "Your goal: Find accurate, cited information.\n\n"
        "Personality and tone: Formal and precise."
    )


def test_strips_whitespace() -> None:
    prompt = build_system_prompt(_agent(instructions="  Be terse.  "))
    assert prompt == "Be terse."
