import pytest

from app.services.workflow.conditions import ConditionError, evaluate_condition
from app.services.workflow.templating import resolve_template


def test_resolves_input_reference() -> None:
    result = resolve_template("Hello {{input}}!", initial_input="world", node_outputs={})
    assert result == "Hello world!"


def test_resolves_node_output_reference() -> None:
    result = resolve_template(
        "Summary: {{n1.output}}", initial_input="ignored", node_outputs={"n1": "the summary text"}
    )
    assert result == "Summary: the summary text"


def test_resolves_node_reference_without_dot_output_suffix() -> None:
    result = resolve_template("{{n1}}", initial_input="x", node_outputs={"n1": "value"})
    assert result == "value"


def test_missing_reference_is_marked_not_silently_dropped() -> None:
    result = resolve_template("{{missing_node.output}}", initial_input="x", node_outputs={})
    assert "missing:missing_node" in result


def test_multiple_references_in_one_template() -> None:
    result = resolve_template(
        "{{input}} and {{n1.output}}", initial_input="A", node_outputs={"n1": "B"}
    )
    assert result == "A and B"


def test_condition_equals() -> None:
    assert evaluate_condition(
        left="{{input}}", operator="equals", right="hello", initial_input="hello", node_outputs={}
    )
    assert not evaluate_condition(
        left="{{input}}", operator="equals", right="hello", initial_input="world", node_outputs={}
    )


def test_condition_contains() -> None:
    assert evaluate_condition(
        left="{{input}}", operator="contains", right="ell", initial_input="hello", node_outputs={}
    )


def test_condition_numeric_comparison() -> None:
    assert evaluate_condition(
        left="10", operator="greater_than", right="5", initial_input="", node_outputs={}
    )
    assert not evaluate_condition(
        left="10", operator="less_than", right="5", initial_input="", node_outputs={}
    )


def test_condition_is_empty() -> None:
    assert evaluate_condition(
        left="{{input}}", operator="is_empty", right=None, initial_input="   ", node_outputs={}
    )
    assert not evaluate_condition(
        left="{{input}}", operator="is_empty", right=None, initial_input="not empty", node_outputs={}
    )


def test_condition_invalid_operator_raises() -> None:
    with pytest.raises(ConditionError):
        evaluate_condition(
            left="a", operator="does_not_exist", right="b", initial_input="", node_outputs={}
        )


def test_condition_numeric_comparison_with_non_numeric_raises() -> None:
    with pytest.raises(ConditionError):
        evaluate_condition(
            left="not a number", operator="greater_than", right="5", initial_input="", node_outputs={}
        )
