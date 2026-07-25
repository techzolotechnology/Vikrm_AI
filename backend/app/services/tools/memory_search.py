"""
Memory search tool — lets a workflow's `tool` node query the same
long-term memory store that Milestone 5 wired into chat, without
duplicating any search/embedding logic. Requires a `ToolContext` with
`user_id` and a DB `session`; used outside that context (e.g. directly
from chat rather than a workflow) raises rather than silently
searching the wrong (or no) user's memories.
"""
from app.services.tools.base import Tool, ToolContext, ToolError


class MemorySearchTool(Tool):
    name = "memory_search"
    description = "Searches the current user's saved long-term memory for relevant facts."

    async def run(self, input_text: str, *, context: ToolContext | None = None) -> str:
        if context is None or context.session is None:
            raise ToolError("memory_search requires an authenticated workflow context")

        from app.services.memory_service import MemoryService

        service = MemoryService(context.session)
        results = await service.search_memories(user_id=context.user_id, query=input_text, top_k=5)

        if not results:
            return "No relevant memories found."
        return "\n".join(f"- {memory.content}" for memory, _distance in results)
