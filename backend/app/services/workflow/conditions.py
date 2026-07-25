"""
Condition node evaluation.

Conditions are structured data (`{"left": "...", "operator": "...",
"right": "..."}`), never a free-form expression string — this closes
off the same arbitrary-code-execution risk `templating.py` and
`calculator.py` avoid. `left`/`right` are resolved via
`resolve_template` first, so they can reference upstream node output.
"""
from app.services.workflow.templating import resolve_template

VALID_OPERATORS = {
    "equals",
    "not_equals",
    "contains",
    "not_contains",
    "greater_than",
    "less_than",
    "is_empty",
    "is_not_empty",
}


class ConditionError(Exception):
    pass


def evaluate_condition(
    *, left: str, operator: str, right: str | None, initial_input: str, node_outputs: dict[str, str]
) -> bool:
    if operator not in VALID_OPERATORS:
        raise ConditionError(f"Unknown operator '{operator}'. Valid: {', '.join(VALID_OPERATORS)}")

    resolved_left = resolve_template(left, initial_input=initial_input, node_outputs=node_outputs)
    resolved_right = (
        resolve_template(right, initial_input=initial_input, node_outputs=node_outputs)
        if right is not None
        else None
    )

    if operator == "equals":
        return resolved_left == resolved_right
    if operator == "not_equals":
        return resolved_left != resolved_right
    if operator == "contains":
        return (resolved_right or "") in resolved_left
    if operator == "not_contains":
        return (resolved_right or "") not in resolved_left
    if operator == "is_empty":
        return resolved_left.strip() == ""
    if operator == "is_not_empty":
        return resolved_left.strip() != ""
    if operator in ("greater_than", "less_than"):
        try:
            left_num = float(resolved_left)
            right_num = float(resolved_right or "0")
        except ValueError as exc:
            raise ConditionError(
                f"'{operator}' requires numeric values, got '{resolved_left}' and '{resolved_right}'"
            ) from exc
        return left_num > right_num if operator == "greater_than" else left_num < right_num

    raise ConditionError(f"Unhandled operator '{operator}'")  # unreachable given the check above
