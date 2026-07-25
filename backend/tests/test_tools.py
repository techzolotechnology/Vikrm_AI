import pytest

from app.services.tools.base import ToolError
from app.services.tools.calculator import CalculatorTool, safe_eval_arithmetic
from app.services.tools.http_request import HttpRequestTool
from app.services.tools.registry import get_tool, list_tools


def test_calculator_basic_arithmetic() -> None:
    assert safe_eval_arithmetic("2 + 3") == 5
    assert safe_eval_arithmetic("10 / 4") == 2.5
    assert safe_eval_arithmetic("2 ** 8") == 256
    assert safe_eval_arithmetic("-5 + 3") == -2


@pytest.mark.parametrize(
    "malicious_input",
    [
        "__import__('os').system('echo pwned')",
        "open('/etc/passwd').read()",
        "[x for x in range(10)]",
        "(lambda: 1)()",
        "1 if True else 2",
    ],
)
def test_calculator_rejects_non_arithmetic(malicious_input: str) -> None:
    with pytest.raises(ToolError):
        safe_eval_arithmetic(malicious_input)


def test_calculator_rejects_division_by_zero() -> None:
    with pytest.raises(ToolError):
        safe_eval_arithmetic("1 / 0")


@pytest.mark.asyncio
async def test_calculator_tool_run_formats_integers_cleanly() -> None:
    tool = CalculatorTool()
    assert await tool.run("2 + 2") == "4"
    assert await tool.run("10 / 4") == "2.5"


@pytest.mark.asyncio
async def test_http_tool_blocks_loopback() -> None:
    tool = HttpRequestTool()
    with pytest.raises(ToolError, match="private, loopback"):
        await tool.run("http://127.0.0.1:8000/")


@pytest.mark.asyncio
async def test_http_tool_blocks_localhost_hostname() -> None:
    tool = HttpRequestTool()
    with pytest.raises(ToolError, match="private, loopback"):
        await tool.run("http://localhost/")


@pytest.mark.asyncio
async def test_http_tool_rejects_non_http_scheme() -> None:
    tool = HttpRequestTool()
    with pytest.raises(ToolError, match="http:// and https://"):
        await tool.run("ftp://example.com/file")


def test_registry_lists_registered_tools() -> None:
    tools = list_tools()
    names = {t["name"] for t in tools}
    assert "calculator" in names
    assert "http_request" in names


def test_registry_raises_for_unknown_tool() -> None:
    with pytest.raises(ToolError):
        get_tool("does_not_exist")
