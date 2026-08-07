"""
Tool registry with expanded system tools.
"""
from app.services.tools.base import Tool, ToolError
from app.services.tools.calculator import CalculatorTool
from app.services.tools.database_query import DatabaseQueryTool
from app.services.tools.document_search import DocumentSearchTool
from app.services.tools.http_request import HttpRequestTool
from app.services.tools.memory_search import MemorySearchTool
from app.services.tools.python_executor import PythonExecutorTool
from app.services.tools.shell_executor import ShellExecutorTool
from app.services.tools.web_search import WebSearchTool

_TOOLS: dict[str, Tool] = {
    "calculator": CalculatorTool(),
    "web_search": WebSearchTool(),
    "python_executor": PythonExecutorTool(),
    "shell_executor": ShellExecutorTool(),
    "http_request": HttpRequestTool(),
    "database_query": DatabaseQueryTool(),
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
