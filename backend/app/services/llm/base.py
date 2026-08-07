"""
LLM provider abstraction.

Every provider (Ollama now; OpenAI/Anthropic/Gemini/Groq/etc in later
milestones) implements this single interface: an async generator that
yields text chunks. This is the seam that lets `ChatService` stay
provider-agnostic — it never imports a provider-specific SDK directly.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
import json
from typing import AsyncIterator, List, Dict, Any, Optional


@dataclass
class ChatMessage:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class GeneratedFile:
    path: str
    language: str
    content: str

    def to_markdown(self) -> str:
        return f"### {self.path}\n\n```{self.language}\n{self.content}\n```"


@dataclass
class NormalizedStreamDelta:
    text: str = ""
    files: Optional[List[GeneratedFile]] = None
    finish_reason: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {"text": self.text}
        if self.files:
            data["files"] = [
                {"path": f.path, "language": f.language, "content": f.content}
                for f in self.files
            ]
        if self.finish_reason:
            data["finish_reason"] = self.finish_reason
        if self.provider:
            data["provider"] = self.provider
        if self.model:
            data["model"] = self.model
        return data


class ProviderError(Exception):
    """Raised when a provider fails to stream a response (unreachable,
    model not found, malformed response, etc)."""


def normalize_content_chunk(chunk: Any) -> str:
    """
    Safely normalizes any stream chunk, LLM output, dictionary object,
    Pydantic model, dataclass, or list payload into a clean string delta.
    Converts structured file payloads into GitHub-Flavored Markdown code blocks
    to permanently eliminate '[object Object]' serialization across all providers,
    tools, workflows, and agents.
    """
    if chunk is None:
        return ""

    if isinstance(chunk, bytes):
        try:
            chunk = chunk.decode("utf-8")
        except Exception:
            return ""

    if hasattr(chunk, "model_dump"):
        try:
            chunk = chunk.model_dump()
        except Exception:
            pass

    if hasattr(chunk, "__dataclass_fields__"):
        try:
            from dataclasses import asdict
            chunk = asdict(chunk)
        except Exception:
            pass

    if isinstance(chunk, str):
        trimmed = chunk.strip()
        if trimmed == "[object Object]":
            return ""
        if (trimmed.startswith("{") and trimmed.endswith("}")) or (trimmed.startswith("[") and trimmed.endswith("]")):
            try:
                parsed = json.loads(trimmed)
                res = normalize_content_chunk(parsed)
                if res != trimmed:
                    return res
            except Exception:
                pass
        return chunk

    if isinstance(chunk, dict):
        if "files" in chunk and isinstance(chunk["files"], list) and chunk["files"]:
            blocks = []
            for f in chunk["files"]:
                if isinstance(f, dict):
                    file_path = f.get("path") or f.get("filename") or f.get("name") or "file"
                    file_content = f.get("content") or f.get("code") or ""
                    if not isinstance(file_content, str):
                        file_content = json.dumps(file_content, indent=2)
                    ext = file_path.split(".")[-1].lower() if "." in file_path else ""
                    lang_map = {
                        "tsx": "tsx", "ts": "typescript", "js": "javascript", "jsx": "jsx",
                        "py": "python", "sh": "bash", "bash": "bash", "json": "json",
                        "yaml": "yaml", "yml": "yaml", "md": "markdown", "html": "html",
                        "css": "css", "sql": "sql", "dockerfile": "dockerfile"
                    }
                    lang = lang_map.get(ext, ext or "code")
                    blocks.append(f"### {file_path}\n\n```{lang}\n{file_content}\n```")
            if blocks:
                return "\n\n".join(blocks)

        for key in ("content", "text", "delta", "message", "response", "output"):
            val = chunk.get(key)
            if isinstance(val, str) and val:
                return normalize_content_chunk(val)

        try:
            return f"\n\n```json\n{json.dumps(chunk, indent=2)}\n```\n\n"
        except Exception:
            return str(chunk)

    if isinstance(chunk, list):
        if not chunk:
            return ""
        items = [normalize_content_chunk(item) for item in chunk]
        return "\n".join(filter(None, items))

    res_str = str(chunk)
    return "" if res_str == "[object Object]" else res_str


def ensure_chat_response(output: Any) -> str:
    """
    Guarantees that an agent, tool, provider, or workflow output is
    strictly returned as a clean, normalized string.
    """
    normalized = normalize_content_chunk(output)
    if not normalized or normalized.strip() == "[object Object]":
        return "No content generated."
    return normalized


class LLMProvider(ABC):
    @abstractmethod
    def stream_chat(
        self, *, messages: list[ChatMessage], model: str, temperature: float = 0.7
    ) -> AsyncIterator[str]:
        """Yields response text chunks as they become available."""
        raise NotImplementedError


