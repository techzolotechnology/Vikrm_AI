"""
Calculator tool.

Deliberately does NOT use eval()/exec() on the input — that would let
a workflow (or an agent driven by untrusted model output) run
arbitrary Python. Instead, the expression is parsed into an AST and
walked manually, allowing only numeric literals and a fixed set of
arithmetic operators. Anything else (names, calls, attribute access,
imports, comprehensions) raises ToolError rather than executing.
"""
import ast
import operator

from app.services.tools.base import Tool, ToolContext, ToolError

_ALLOWED_BINOPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}

_ALLOWED_UNARYOPS = {
    ast.UAdd: operator.pos,
    ast.USub: operator.neg,
}


def _eval_node(node: ast.AST) -> float:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ToolError(f"Unsupported constant: {node.value!r}")

    if isinstance(node, ast.BinOp):
        op_fn = _ALLOWED_BINOPS.get(type(node.op))
        if op_fn is None:
            raise ToolError(f"Unsupported operator: {type(node.op).__name__}")
        return op_fn(_eval_node(node.left), _eval_node(node.right))

    if isinstance(node, ast.UnaryOp):
        op_fn = _ALLOWED_UNARYOPS.get(type(node.op))
        if op_fn is None:
            raise ToolError(f"Unsupported unary operator: {type(node.op).__name__}")
        return op_fn(_eval_node(node.operand))

    raise ToolError(f"Unsupported expression: {type(node).__name__}")


def safe_eval_arithmetic(expression: str) -> float:
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise ToolError(f"Invalid arithmetic expression: {exc}") from exc

    try:
        return _eval_node(tree.body)
    except ZeroDivisionError as exc:
        raise ToolError("Division by zero") from exc


class CalculatorTool(Tool):
    name = "calculator"
    description = "Evaluates a basic arithmetic expression (+, -, *, /, //, %, **). No variables or functions."

    async def run(self, input_text: str, *, context: ToolContext | None = None) -> str:
        result = safe_eval_arithmetic(input_text.strip())
        # Render integers without a trailing ".0" for cleaner tool output.
        if isinstance(result, float) and result.is_integer():
            return str(int(result))
        return str(result)
