"""
Tests for Milestone 9's new tools. The Python executor tests verify
real process isolation and timeout enforcement, not simulated behavior.
"""
import time

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.tools.base import ToolContext, ToolError
from app.services.tools.document_search import DocumentSearchTool
from app.services.tools.memory_search import MemorySearchTool
from app.services.tools.python_executor import PythonExecutorTool


@pytest.mark.asyncio
async def test_python_executor_runs_real_code() -> None:
    tool = PythonExecutorTool()
    result = await tool.run("print(6 * 7)")
    assert result == "42"


@pytest.mark.asyncio
async def test_python_executor_multiline_program() -> None:
    tool = PythonExecutorTool()
    result = await tool.run("total = 0\nfor i in range(5):\n    total += i\nprint(total)")
    assert result == "10"


@pytest.mark.asyncio
async def test_python_executor_runs_in_separate_process() -> None:
    """The defining security property: this must NOT be in-process exec()."""
    import os

    tool = PythonExecutorTool()
    result = await tool.run("import os; print(os.getpid())")
    assert result.isdigit()
    assert int(result) != os.getpid()


@pytest.mark.asyncio
async def test_python_executor_syntax_error_raises_tool_error() -> None:
    tool = PythonExecutorTool()
    with pytest.raises(ToolError, match="exited with code"):
        await tool.run("this is not ( valid python")


@pytest.mark.asyncio
async def test_python_executor_empty_input_raises() -> None:
    tool = PythonExecutorTool()
    with pytest.raises(ToolError, match="No code"):
        await tool.run("   ")


@pytest.mark.asyncio
async def test_python_executor_enforces_timeout() -> None:
    tool = PythonExecutorTool()
    start = time.monotonic()
    with pytest.raises(ToolError, match="timed out"):
        await tool.run("import time; time.sleep(30)")
    elapsed = time.monotonic() - start
    assert elapsed < 10  # must be killed well before the script's own 30s sleep completes


@pytest.mark.asyncio
async def test_python_executor_output_is_truncated() -> None:
    tool = PythonExecutorTool()
    result = await tool.run("print('x' * 10000)")
    assert len(result) <= 4020  # MAX_OUTPUT_CHARS + truncation marker
    assert "truncated" in result


@pytest.mark.asyncio
async def test_memory_search_tool_requires_context() -> None:
    tool = MemorySearchTool()
    with pytest.raises(ToolError, match="requires an authenticated"):
        await tool.run("anything")


@pytest.mark.asyncio
async def test_memory_search_tool_finds_relevant_memory(db_session: AsyncSession) -> None:
    from app.repositories.user_repository import UserRepository
    from app.services.memory_service import MemoryService

    users = UserRepository(db_session)
    user = await users.create(
        google_sub="tool-mem", email="toolmem@example.com", full_name=None, avatar_url=None
    )
    await db_session.commit()

    memory_service = MemoryService(db_session)
    await memory_service.create_memory(user_id=user.id, content="The user's favorite color is teal.")

    tool = MemorySearchTool()
    context = ToolContext(user_id=user.id, session=db_session)
    result = await tool.run("What is the user's favorite color?", context=context)
    assert "teal" in result


@pytest.mark.asyncio
async def test_document_search_tool_requires_context() -> None:
    tool = DocumentSearchTool()
    with pytest.raises(ToolError, match="requires an authenticated"):
        await tool.run("anything")


@pytest.mark.asyncio
async def test_document_search_tool_finds_relevant_chunk_with_citation(
    db_session: AsyncSession,
) -> None:
    from app.repositories.user_repository import UserRepository
    from app.services.rag_service import RagService

    users = UserRepository(db_session)
    user = await users.create(
        google_sub="tool-doc", email="tooldoc@example.com", full_name=None, avatar_url=None
    )
    await db_session.commit()

    rag_service = RagService(db_session)
    await rag_service.process_upload(
        user_id=user.id,
        filename="handbook.txt",
        content_type="text/plain",
        content=b"The office is closed on public holidays.",
    )

    tool = DocumentSearchTool()
    context = ToolContext(user_id=user.id, session=db_session)
    result = await tool.run("When is the office closed?", context=context)
    assert "handbook.txt" in result
    assert "public holidays" in result
