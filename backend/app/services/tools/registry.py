"""
Tool registry — mirrors the LLM/embedding provider registry pattern.
"""
from app.services.tools.base import Tool, ToolError
from app.services.tools.calculator import CalculatorTool
from app.services.tools.document_search import DocumentSearchTool
from app.services.tools.http_request import HttpRequestTool
from app.services.tools.memory_search import MemorySearchTool
from app.services.tools.python_executor import PythonExecutorTool

_TOOLS: dict[str, Tool] = {
    "calculator": CalculatorTool(),
    "http_request": HttpRequestTool(),
    "python_executor": PythonExecutorTool(),
    "memory_search": MemorySearchTool(),
    "document_search": DocumentSearchTool(),
}


def get_tool(name: str) -> Tool:
    tool = _TOOLS.get(name)
    if tool is None:
        raise ToolError(f"Unknown tool '{name}'. Available: {', '.join(_TOOLS)}")
    return tool


def list_tools() -> list[dict]:
    return [{"name": t.name, "description": t.description} for t in _TOOLS.values()]
