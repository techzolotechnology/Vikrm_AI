"""
Document search tool — the workflow-node equivalent of the RAG search
Milestone 6 wired into chat, reusing RagService directly.
"""
from app.services.tools.base import Tool, ToolContext, ToolError


class DocumentSearchTool(Tool):
    name = "document_search"
    description = "Searches the current user's uploaded documents for relevant excerpts, with citations."

    async def run(self, input_text: str, *, context: ToolContext | None = None) -> str:
        if context is None or context.session is None:
            raise ToolError("document_search requires an authenticated workflow context")

        from app.services.rag_service import RagService

        service = RagService(context.session)
        matches = await service.search_chunks(user_id=context.user_id, query=input_text, top_k=5)

        if not matches:
            return "No relevant document excerpts found."
        return "\n".join(f"[{m['metadata']['filename']}]: {m['document']}" for m in matches)
