"""
Chat service - optimized for streaming performance.

Key optimization: buffer tokens during streaming, commit only at end.
This eliminates the DB write-per-token bottleneck that caused slow responses.
"""
import asyncio
import json
import re
from typing import AsyncIterator, Sequence

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import get_logger
from app.models.attachment import Attachment
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.repositories.agent_repository import AgentRepository
from app.repositories.attachment_repository import AttachmentRepository
from app.repositories.conversation_repository import ConversationRepository
from app.repositories.message_repository import MessageRepository
from app.services.agent_service import build_system_prompt
from app.services.intent_service import IntentService, ResponseMode
from app.services.project.templates import TEMPLATES
from app.services.project.dynamic_generator import DynamicProjectGenerator
from app.services.project.autonomous_execution_engine import AutonomousExecutionEngine
from app.services.project.agent_loop import AgentLoop
from app.services.llm.base import ChatMessage, ProviderError, normalize_content_chunk
from app.services.llm.registry import get_provider
from app.services.memory_service import MemoryService
from app.services.rag_service import RagService
from app.services.rag.retriever import KnowledgeRetriever
from app.services.rag.context_builder import RAGContextBuilder

logger = get_logger(__name__)
_global_retriever = None

def get_knowledge_retriever() -> KnowledgeRetriever:
    global _global_retriever
    if _global_retriever is None:
        _global_retriever = KnowledgeRetriever()
    return _global_retriever


DEFAULT_SYSTEM_PROMPT = (
    "You are Vikrm AI, an elite autonomous software engineering assistant and full-stack architect.\n\n"
    "RESPONSE ENGINE GUIDELINES:\n"
    "1. CONVERSATIONAL: For theory, definitions, concepts, and general questions, output ChatGPT-style markdown with headings, bullets, tables, and short inline code blocks. Do NOT create project structures or unnecessary files.\n"
    "2. SMALL CODE: For algorithm or single-component requests (e.g. bubble sort, React button), output a single clean code block + explanation + complexity + edge cases.\n"
    "3. ARTIFACT PROJECT: When asked to build, generate, or create an application, website, or project, output a complete multi-file project with production-grade code. Format each file with explicit Markdown headings and code blocks:\n"
    "   ### path/to/file.ext\n"
    "   ```lang\n"
    "   // full implementation\n"
    "   ```\n"
    "4. EDIT PROJECT: When modifying existing files, output only changed, added, or deleted files with clear line diffs or complete replacements. Do not regenerate unchanged files.\n"
    "5. DEBUG: For error logs and stack traces, provide Root Cause, Evidence, Confidence, Affected Files, Minimal Patch, and Verification Steps.\n"
    "6. CODE REVIEW: Provide Strengths, Security Issues, Performance, Architecture, Complexity, Refactored Code, and Score /10.\n"
    "7. ARCHITECT: Provide Mermaid diagrams (ER, sequence, architecture), folder structure, and API contracts.\n\n"
    "STRICT QUALITY RULES:\n"
    "- Production-ready code only. Zero placeholders, zero TODOs, zero missing imports, zero syntax errors.\n"
    "- Never output raw JSON objects, raw dictionaries, or '[object Object]' strings."
)



class ChatServiceError(Exception):
    pass


def generate_concise_title(user_prompt: str) -> str:
    """Generate a clean title (max 5 words) from the user's prompt."""
    cleaned = re.sub(r"[^\w\s]", "", user_prompt).strip()
    words = cleaned.split()
    if not words:
        return "AI Conversation"
    title_words = words[:5]
    title = " ".join(title_words).capitalize()
    return title if len(title) <= 50 else title[:47] + "..."


class ChatService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._conversations = ConversationRepository(session)
        self._messages = MessageRepository(session)
        self._agents = AgentRepository(session)
        self._attachments = AttachmentRepository(session)
        self._memories = MemoryService(session)
        self._rag = RagService(session)

    async def create_conversation(
        self,
        *,
        user_id: int,
        title: str | None = None,
        provider: str | None = None,
        model: str | None = None,
        agent_id: int | None = None,
    ) -> Conversation:
        resolved_provider = provider or settings.DEFAULT_LLM_PROVIDER
        resolved_model = model or settings.DEFAULT_LLM_MODEL
        resolved_title = title or "New Conversation"

        if agent_id is not None:
            agent = await self._agents.get_by_id(agent_id, user_id=user_id)
            if agent is None:
                raise ChatServiceError("Agent not found")
            resolved_provider = provider or agent.provider
            resolved_model = model or agent.model
            resolved_title = title or agent.name

        conversation = await self._conversations.create(
            user_id=user_id,
            title=resolved_title,
            provider=resolved_provider,
            model=resolved_model,
            agent_id=agent_id,
        )
        await self._session.commit()
        return conversation

    async def list_conversations(
        self,
        *,
        user_id: int,
        is_archived: bool | None = False,
        is_pinned: bool | None = None,
        search_query: str | None = None,
    ) -> Sequence[Conversation]:
        return await self._conversations.list_for_user(
            user_id,
            is_archived=is_archived,
            is_pinned=is_pinned,
            search_query=search_query,
        )

    async def get_conversation(self, *, conversation_id: int, user_id: int) -> Conversation | None:
        conv = await self._conversations.get_by_id(conversation_id, user_id=user_id)
        if conv and conv.messages:
            for msg in conv.messages:
                if msg.content:
                    norm = normalize_content_chunk(msg.content)
                    if norm != msg.content:
                        msg.content = norm
        return conv

    async def update_conversation(
        self,
        *,
        conversation: Conversation,
        title: str | None = None,
        is_pinned: bool | None = None,
        is_archived: bool | None = None,
        summary: str | None = None,
    ) -> Conversation:
        updated = await self._conversations.update(
            conversation,
            title=title,
            is_pinned=is_pinned,
            is_archived=is_archived,
            summary=summary,
        )
        await self._session.commit()
        return updated

    async def duplicate_conversation(self, conversation: Conversation) -> Conversation:
        new_conv = await self._conversations.create(
            user_id=conversation.user_id,
            title=f"{conversation.title} (Copy)",
            provider=conversation.provider,
            model=conversation.model,
            agent_id=conversation.agent_id,
        )
        prior_messages = await self._messages.list_for_conversation(conversation.id)
        for msg in prior_messages:
            await self._messages.create(
                conversation_id=new_conv.id,
                role=msg.role,
                content=normalize_content_chunk(msg.content),
                error=msg.error,
                is_bookmarked=msg.is_bookmarked,
            )
        await self._session.commit()
        return new_conv

    async def delete_conversation(self, conversation: Conversation) -> None:
        await self._conversations.delete(conversation)
        await self._session.commit()

    async def toggle_bookmark_message(
        self, *, conversation_id: int, message_id: int, user_id: int
    ) -> Message:
        conv = await self._conversations.get_by_id(conversation_id, user_id=user_id)
        if not conv:
            raise ChatServiceError("Conversation not found")
        msg = await self._messages.get_by_id(message_id, conversation_id)
        if not msg:
            raise ChatServiceError("Message not found")
        updated = await self._messages.toggle_bookmark(msg)
        await self._session.commit()
        return updated

    async def delete_message(self, *, conversation_id: int, message_id: int, user_id: int) -> None:
        conv = await self._conversations.get_by_id(conversation_id, user_id=user_id)
        if not conv:
            raise ChatServiceError("Conversation not found")
        msg = await self._messages.get_by_id(message_id, conversation_id)
        if not msg:
            raise ChatServiceError("Message not found")
        await self._messages.delete(msg)
        await self._session.commit()

    async def stream_reply(
        self,
        *,
        conversation: Conversation,
        user_content: str,
        attachment_ids: list[int] | None = None,
    ) -> AsyncIterator[str]:
        """
        Stream AI reply tokens.

        PERFORMANCE: We do NOT commit on every token. Instead we:
        1. Flush user + assistant messages once before streaming.
        2. Accumulate all tokens in-memory.
        3. Write the full response + commit ONCE after streaming completes.
        This eliminates the per-token DB serialization bottleneck.
        """
        import time
        start_time = time.perf_counter()

        logger.info("[Incoming Request] conversation_id=%s user_id=%s prompt=%r", conversation.id, conversation.user_id, user_content[:80])

        # 1. Semantic Intent Classification
        intent_res = IntentService.classify_intent(user_content)
        detected_mode = intent_res["mode"]
        confidence = intent_res.get("confidence", 0.95)
        reason = intent_res.get("reason", "Semantic intent rule matched")

        intent_log = (
            f"\nDetected Intent: {detected_mode}\n"
            f"Selected Mode: {detected_mode}\n"
            f"Confidence: {confidence:.2f}\n"
            f"Reason: {reason}\n"
        )
        logger.info(intent_log)
        print(intent_log)

        # Load conversation history
        prior_messages = await self._messages.list_for_conversation(conversation.id)
        history: list[ChatMessage] = [
            ChatMessage(role=m.role.value, content=m.content) for m in prior_messages
        ]

        temperature = 0.7

        # Project Generator System Prompt for ARTIFACT_PROJECT mode
        PROJECT_GENERATOR_SYSTEM_PROMPT = (
            "You are Vikrm AI Autonomous Project Generator.\n"
            "The user wants a complete, production-grade multi-file project application.\n\n"
            "MANDATORY OUTPUT FORMAT:\n"
            "You MUST output the complete project as multiple source files. Each file MUST be formatted with an explicit Markdown heading followed by a code block:\n\n"
            "### path/to/file.ext\n"
            "```language\n"
            "// Complete functional source code\n"
            "```\n\n"
            "STRICT RULES:\n"
            "1. NEVER output a text tutorial, step-by-step guide, setup commands, or markdown explanations.\n"
            "2. NEVER output generic tutorials like 'Here is a basic example...'.\n"
            "3. Output complete functional code for all files (index.html, package.json, README.md, App components, CSS/styles, API routes).\n"
            "4. Zero placeholders, zero TODO comments, zero missing imports."
        )

        # Inject agent system prompt, Project Generator prompt, or default prompt
        if detected_mode == ResponseMode.ARTIFACT_PROJECT:
            logger.info("[Project Generator] Forcing ARTIFACT_PROJECT mode execution for prompt: %r", user_content[:60])
            history = [m for m in history if m.role != "system"]
            history.insert(0, ChatMessage(role="system", content=PROJECT_GENERATOR_SYSTEM_PROMPT))
        elif conversation.agent_id is not None:
            logger.info("[Agent Execution] Loading agent_id=%s configuration", conversation.agent_id)
            agent = await self._agents.get_by_id(conversation.agent_id, user_id=conversation.user_id)
            if agent is not None:
                system_prompt = build_system_prompt(agent)
                if system_prompt and not any(m.role == "system" for m in history):
                    history.insert(0, ChatMessage(role="system", content=system_prompt))
                temperature = agent.temperature
        else:
            if not any(m.role == "system" for m in history):
                history.insert(0, ChatMessage(role="system", content=DEFAULT_SYSTEM_PROMPT))

        # Inject relevant memory context
        logger.info("[Memory Search] Querying memory store for user_id=%s", conversation.user_id)
        relevant_memories = []
        try:
            relevant_memories = await self._memories.search_memories(
                user_id=conversation.user_id, query=user_content, top_k=settings.MEMORY_SEARCH_TOP_K
            )
            if relevant_memories:
                memory_lines = "\n".join(
                    f"- {memory.content}" for memory, _distance in relevant_memories
                )
                history.append(
                    ChatMessage(
                        role="system",
                        content=f"Relevant information you remember about this user:\n{memory_lines}",
                    )
                )
        except Exception as exc:
            logger.warning("[Memory Search] Memory search failed (non-fatal): %s", exc)

        logger.info("[Memory Search] Retrieved %d memory entries", len(relevant_memories) if relevant_memories else 0)

        # Inject RAG uploaded user document chunks
        try:
            doc_chunks = await self._rag.search_chunks(user_id=conversation.user_id, query=user_content, top_k=4)
            if doc_chunks:
                doc_text = "\n\n".join(
                    f"--- Source: {c.get('metadata', {}).get('filename', 'document')} ---\n{c.get('document', '')}"
                    for c in doc_chunks
                )
                history.append(
                    ChatMessage(
                        role="system",
                        content=f"RELEVANT UPLOADED DOCUMENTS:\n{doc_text}",
                    )
                )
        except Exception as exc:
            logger.warning("[RAG Search] User document search failed: %s", exc)

        # Inject RAG document chunks and HF Datasets / Templates / Docs context for complex queries
        if detected_mode == ResponseMode.ARTIFACT_PROJECT or len(user_content.split()) > 3:
            logger.info("[RAG Retrieval] Searching Hugging Face datasets, docs, and templates for prompt=%r", user_content[:80])
            try:
                retriever = get_knowledge_retriever()
                retrieval_res = retriever.retrieve_context(query=user_content, top_k=10)
                context_builder = RAGContextBuilder()
                augmented_context_prompt = context_builder.build_augmented_prompt(
                    user_query=user_content, retrieval_results=retrieval_res
                )
                if augmented_context_prompt != user_content:
                    history.append(
                        ChatMessage(
                            role="system",
                            content=augmented_context_prompt,
                        )
                    )
            except Exception as exc:
                logger.warning("[RAG Retrieval] Knowledge retrieval failed (non-fatal): %s", exc)


        # Inject direct attachment text into the user message
        attached_texts: list[str] = []
        if attachment_ids:
            for att_id in attachment_ids:
                try:
                    att = await self._attachments.get_by_id(att_id, user_id=conversation.user_id)
                    if att and att.extracted_text:
                        attached_texts.append(f"--- File: {att.filename} ---\n{att.extracted_text}")
                except Exception as exc:
                    logger.warning("[ChatService] Failed to load attachment %s: %s", att_id, exc)

        full_user_text = user_content
        if attached_texts:
            full_user_text = (
                user_content
                + "\n\nAttached Document Contents:\n"
                + "\n\n".join(attached_texts)
            )

        history.append(ChatMessage(role="user", content=full_user_text))

        logger.info("[Prompt Built] history_length=%d temperature=%.2f model=%s", len(history), temperature, conversation.model)

        # Persist user message (flush only, no commit yet)
        user_message = await self._messages.create(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content=user_content,
        )
        if attachment_ids:
            for att_id in attachment_ids:
                try:
                    att = await self._attachments.get_by_id(att_id, user_id=conversation.user_id)
                    if att:
                        await self._attachments.link_to_message(att, user_message.id)
                except Exception:
                    pass

        # Create empty assistant message placeholder (flush only)
        assistant_message: Message = await self._messages.create(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content="",
        )
        # Single commit before streaming starts
        await self._session.commit()

        # ── True AI Agent Loop (Phases 1–15) ──
        if detected_mode in (ResponseMode.ARTIFACT_PROJECT, ResponseMode.EDIT_PROJECT):
            logger.info("[AgentLoop] Starting Autonomous Software Engineering Agent (mode=%s) for prompt=%r", detected_mode, user_content[:60])
            full_generated_text = ""

            from app.services.project.incremental_edit_engine import get_workspace_context, save_workspace_context, IncrementalEditEngine, WorkspaceContext

            ctx = get_workspace_context(conversation.id)

            if detected_mode == ResponseMode.EDIT_PROJECT and ctx and ctx.files:
                # Incremental Edit Mode on Active Workspace
                yield "> [Planning...]\n"
                await asyncio.sleep(0.01)
                yield "> [Analyzing Workspace...]\n"
                await asyncio.sleep(0.01)
                yield "> [Retrieving Knowledge...]\n"
                await asyncio.sleep(0.01)
                yield "> [Updating Existing Files...]\n"
                await asyncio.sleep(0.01)

                changed_files, changed_paths = IncrementalEditEngine.apply_edit(ctx, user_content)
                save_workspace_context(conversation.id, ctx)

                yield "> [Validating...]\n"
                await asyncio.sleep(0.01)
                yield "> [Running Build...]\n"
                await asyncio.sleep(0.01)
                yield "> [Workspace Ready]\n\n"
                await asyncio.sleep(0.01)

                for path, content in changed_files.items():
                    ext = path.split(".")[-1] if "." in path else ""
                    lang = {
                        "ts": "typescript", "tsx": "typescript",
                        "js": "javascript", "jsx": "javascript",
                        "py": "python", "css": "css", "html": "html",
                        "md": "markdown", "json": "json", "yml": "yaml",
                        "yaml": "yaml", "sql": "sql", "sh": "bash",
                    }.get(ext, "text")
                    block = f"### {path}\n```{lang}\n{content}\n```\n\n"
                    full_generated_text += block
                    yield block
                    await asyncio.sleep(0.005)

                assistant_message.content = full_generated_text
                await self._session.commit()
                return

            # Full Artifact Generation Mode
            async for event_type, content in AgentLoop.run(user_content):
                if event_type == "status":
                    status_line = f"> {content}\n"
                    full_generated_text += status_line
                    yield status_line
                    await asyncio.sleep(0.01)
                elif event_type == "file":
                    full_generated_text += content
                    yield content
                    await asyncio.sleep(0.003)

            # Save generated workspace context for subsequent incremental edits
            try:
                from app.services.project.planning_agent import PlanningAgent
                from app.services.project.code_synthesizer import LLMCodeSynthesizer
                plan = PlanningAgent.plan(user_content)
                gen_files = LLMCodeSynthesizer.synthesize(plan)
                new_ctx = WorkspaceContext(
                    project_name=plan.project_name,
                    project_slug=plan.project_slug,
                    domain=plan.domain,
                    framework=plan.framework,
                    database=plan.database,
                    auth_strategy=plan.auth_strategy,
                )
                new_ctx.load_from_files(gen_files)
                save_workspace_context(conversation.id, new_ctx)
            except Exception as ctx_err:
                logger.warning("[WorkspaceContext] Failed saving workspace context: %s", ctx_err)

            assistant_message.content = full_generated_text
            await self._session.commit()
            return

        provider = get_provider(conversation.provider)
        full_response_tokens: list[str] = []

        logger.info("[Ollama Request] Invoking provider=%s model=%s conversation_id=%s", conversation.provider, conversation.model, conversation.id)

        has_streamed_first_token = False

        try:
            async for chunk in provider.stream_chat(
                messages=history,
                model=conversation.model,
                temperature=temperature,
            ):
                if not has_streamed_first_token:
                    logger.info("[Streaming Started] First token yielded for conversation_id=%s", conversation.id)
                    has_streamed_first_token = True
                chunk_str = normalize_content_chunk(chunk)
                if chunk_str:
                    full_response_tokens.append(chunk_str)
                    yield chunk_str

            logger.info("[Streaming Finished] All tokens streamed successfully for conversation_id=%s", conversation.id)

        except ProviderError as exc:
            error_msg = str(exc)
            logger.error("[Exception] ProviderError: %s", error_msg)
            assistant_message.error = error_msg
            assistant_message.content = normalize_content_chunk("".join(full_response_tokens))
            try:
                await self._session.commit()
            except Exception:
                pass
            yield f"\n\n⚠️ **AI Provider Error**: {error_msg}"
            return

        except asyncio.CancelledError:
            logger.warning("[Streaming Cancelled] Stream cancelled for conversation_id=%s", conversation.id)
            full_response = normalize_content_chunk("".join(full_response_tokens))
            if full_response:
                assistant_message.content = full_response
            try:
                await self._session.commit()
            except Exception:
                pass
            raise

        except Exception as exc:
            error_msg = f"Unexpected error during streaming: {exc}"
            logger.exception("[Exception] Streaming failure: %s", exc)
            assistant_message.error = error_msg
            assistant_message.content = normalize_content_chunk("".join(full_response_tokens))
            try:
                await self._session.commit()
            except Exception:
                pass
            yield f"\n\n⚠️ **Error**: {error_msg}"
            return

        finally:
            elapsed = time.perf_counter() - start_time
            full_response = normalize_content_chunk("".join(full_response_tokens))
            if full_response and not assistant_message.content:
                assistant_message.content = full_response

            # Auto-generate concise title on first reply
            if conversation.title in ["New Conversation", "AI Conversation", "Untitled", ""]:
                conversation.title = generate_concise_title(user_content)

            try:
                await self._conversations.touch(conversation)
                await self._session.commit()
            except Exception as commit_exc:
                logger.warning("[ChatService] Failed final commit in stream_reply: %s", commit_exc)

            logger.info(
                "[Cleanup Completed] conversation_id=%s response_len=%d tokens=%d latency=%.2fs title=%r",
                conversation.id,
                len(full_response),
                len(full_response_tokens),
                elapsed,
                conversation.title,
            )

    async def export_conversation(self, conversation: Conversation) -> dict:
        messages = await self._messages.list_for_conversation(conversation.id)
        attachments = await self._attachments.list_for_conversation(conversation.id)
        return {
            "title": conversation.title,
            "provider": conversation.provider,
            "model": conversation.model,
            "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
            "messages": [
                {
                    "role": m.role.value,
                    "content": normalize_content_chunk(m.content),
                    "created_at": m.created_at.isoformat() if m.created_at else None,
                    "is_bookmarked": m.is_bookmarked,
                }
                for m in messages
            ],
            "attachments": [a.filename for a in attachments],
        }

    async def import_conversation(self, *, user_id: int, data: dict) -> Conversation:
        title = data.get("title") or "Imported Conversation"
        provider = data.get("provider") or settings.DEFAULT_LLM_PROVIDER
        model = data.get("model") or settings.DEFAULT_LLM_MODEL

        conv = await self._conversations.create(
            user_id=user_id,
            title=title,
            provider=provider,
            model=model,
        )
        messages_data = data.get("messages", [])
        for mdata in messages_data:
            role_str = mdata.get("role", "user")
            role = MessageRole.USER if role_str == "user" else MessageRole.ASSISTANT
            await self._messages.create(
                conversation_id=conv.id,
                role=role,
                content=normalize_content_chunk(mdata.get("content", "")),
                is_bookmarked=mdata.get("is_bookmarked", False),
            )
        await self._session.commit()
        return conv
