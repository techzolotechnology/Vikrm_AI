"""
AI File Action Service — Phase 5: Per-file intelligent actions.
Supports: explain, refactor, optimize, document, test_generate, fix_bugs,
          code_review, security_scan, translate, rename_vars, extract_component, extract_function
Uses the LLM provider to perform targeted, surgical file-level operations.
"""
from typing import Any
from app.core.logging import get_logger
from app.services.intent_service import IntentService

logger = get_logger(__name__)

AI_FILE_ACTION_PROMPTS: dict[str, str] = {
    "explain": (
        "You are an expert software architect. Analyze this code file and provide a concise, professional explanation.\n"
        "Cover: purpose, key functions, dependencies, design patterns, and potential issues.\n"
        "Be direct and practical. No filler text.\n\nFILE: {path}\n```{language}\n{content}\n```"
    ),
    "refactor": (
        "You are a senior software engineer. Refactor this code to:\n"
        "1. Apply clean code principles (SOLID, DRY, KISS)\n"
        "2. Reduce cognitive complexity\n"
        "3. Improve naming conventions\n"
        "4. Extract reusable abstractions\n"
        "5. Remove dead code\n"
        "Return ONLY the refactored code without explanation.\n\nFILE: {path}\n```{language}\n{content}\n```"
    ),
    "optimize": (
        "You are a performance engineering expert. Optimize this code for:\n"
        "1. Time complexity (Big O)\n"
        "2. Memory efficiency\n"
        "3. Unnecessary re-renders (React) or redundant computations\n"
        "4. Bundle size (tree-shakeable exports)\n"
        "Return ONLY the optimized code.\n\nFILE: {path}\n```{language}\n{content}\n```"
    ),
    "document": (
        "You are a technical documentation specialist. Add comprehensive documentation to this file:\n"
        "- JSDoc / Python docstrings for every function, class, and interface\n"
        "- Parameter descriptions with @param\n"
        "- Return type with @returns\n"
        "- Usage examples with @example\n"
        "- Module-level docstring\n"
        "Return ONLY the fully documented code.\n\nFILE: {path}\n```{language}\n{content}\n```"
    ),
    "test_generate": (
        "You are a QA engineer specializing in automated testing. Generate comprehensive tests for this file.\n"
        "Include: unit tests, edge cases, error scenarios, and integration stubs.\n"
        "Use vitest + @testing-library/react for TypeScript, pytest for Python.\n"
        "Every test must be runnable with zero configuration changes.\n\nFILE: {path}\n```{language}\n{content}\n```"
    ),
    "fix_bugs": (
        "You are a debugging expert. Analyze this code and fix all bugs:\n"
        "1. Logic errors\n"
        "2. Off-by-one errors\n"
        "3. Null/undefined dereferences\n"
        "4. Race conditions\n"
        "5. Memory leaks\n"
        "6. Type mismatches\n"
        "Return ONLY the fixed code with brief inline comments for each fix.\n\nFILE: {path}\n```{language}\n{content}\n```"
    ),
    "code_review": (
        "You are a senior code reviewer conducting a professional code review.\n"
        "Evaluate: naming, structure, error handling, security, performance, testability, documentation.\n"
        "Format: provide a numbered list of issues with severity (Critical/Major/Minor) and suggested fix.\n"
        "End with an overall quality score from 0-100.\n\nFILE: {path}\n```{language}\n{content}\n```"
    ),
    "security_scan": (
        "You are a security engineer performing a comprehensive security audit.\n"
        "Check for: OWASP Top 10, SQL injection, XSS, CSRF, auth vulnerabilities, secret exposure,\n"
        "insecure dependencies, improper error handling revealing internals, and input validation gaps.\n"
        "Format: severity, location, description, remediation. End with Security Score /100.\n\nFILE: {path}\n```{language}\n{content}\n```"
    ),
    "translate": (
        "You are a full-stack engineer. Convert this code to modern TypeScript:\n"
        "1. Add strict type annotations\n"
        "2. Use TypeScript interfaces/types for all data structures\n"
        "3. Remove any `any` types\n"
        "4. Use generics where applicable\n"
        "5. Add readonly modifiers where appropriate\n"
        "Return ONLY the converted TypeScript code.\n\nFILE: {path}\n```{language}\n{content}\n```"
    ),
    "extract_component": (
        "You are a React architect. Extract reusable React components from this file.\n"
        "1. Identify UI blocks that can be componentized\n"
        "2. Create proper prop interfaces\n"
        "3. Apply React best practices (memo, useCallback where needed)\n"
        "4. Return both the refactored main file AND each new component file.\n"
        "Format: ### original/file.tsx\\n```tsx\\n...code...\\n```\\n### src/components/NewComp.tsx\\n```tsx\\n...```\n\nFILE: {path}\n```{language}\n{content}\n```"
    ),
    "extract_function": (
        "You are a software architect. Extract pure functions from this file:\n"
        "1. Identify complex logic blocks that should be functions\n"
        "2. Create well-named pure functions with single responsibilities\n"
        "3. Move utilities to appropriate utility modules\n"
        "Return the refactored code with extracted functions in a utils/ file.\n\nFILE: {path}\n```{language}\n{content}\n```"
    ),
}


class AIFileActionService:
    @classmethod
    async def execute_action(
        cls,
        action: str,
        path: str,
        content: str,
        language: str,
        provider_name: str = "ollama",
        model: str = "qwen3:8b",
    ) -> dict[str, Any]:
        """
        Execute an AI file action on the given file.
        Returns: { result: str, action: str, path: str, success: bool }
        """
        prompt_template = AI_FILE_ACTION_PROMPTS.get(action)
        if not prompt_template:
            return {"success": False, "error": f"Unknown action: {action}", "result": "", "action": action, "path": path}

        prompt = prompt_template.format(path=path, language=language, content=content[:8000])

        try:
            from app.services.llm.registry import get_provider
            from app.services.llm.base import ChatMessage
            provider = get_provider(provider_name)
            result_chunks: list[str] = []
            async for chunk in provider.stream_chat(
                messages=[ChatMessage(role="user", content=prompt)],
                model=model,
                temperature=0.2,
            ):
                from app.services.llm.base import normalize_content_chunk
                text = normalize_content_chunk(chunk)
                if text:
                    result_chunks.append(text)
            result = "".join(result_chunks)
            logger.info("[AIFileAction] action=%s path=%s length=%d", action, path, len(result))
            return {"success": True, "action": action, "path": path, "result": result}
        except Exception as e:
            logger.error("[AIFileAction] Error: %s", str(e))
            return {"success": False, "error": str(e), "result": "", "action": action, "path": path}
