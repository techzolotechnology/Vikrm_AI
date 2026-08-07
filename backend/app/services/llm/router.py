"""
Intelligent Model Router.

Determines the optimal provider and model based on task intent or explicit manual override.
Rules:
- Website / UI Generation -> Anthropic Claude
- Backend APIs & Database -> OpenAI GPT-4o
- Fast reasoning / low latency -> Groq
- Long context / deep reasoning -> Gemini
- Offline / Free mode -> Ollama
- Refactoring / Code Review -> DeepSeek
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class RouteDecision:
    provider: str
    model: str
    reason: str


class ModelRouter:
    @staticmethod
    def route_task(
        task_description: str,
        *,
        intent: Optional[str] = None,
        offline: bool = False,
        free_mode: bool = False,
        manual_override_provider: Optional[str] = None,
        manual_override_model: Optional[str] = None,
    ) -> RouteDecision:
        # Manual override takes precedence
        if manual_override_provider:
            model = manual_override_model or ""
            return RouteDecision(
                provider=manual_override_provider.lower(),
                model=model,
                reason="Manual override by user"
            )

        if offline or free_mode:
            return RouteDecision(
                provider="ollama",
                model="llama3",
                reason="Offline or free execution mode selected"
            )

        lower_desc = (task_description or "").lower()
        lower_intent = (intent or "").lower()

        # Intent / Keyword matching rules
        if any(kw in lower_desc or kw in lower_intent for kw in ["website", "frontend", "react", "html", "css", "landing page", "ui"]):
            return RouteDecision(
                provider="anthropic",
                model="claude-3-5-sonnet-20241022",
                reason="Website & Frontend Generation routed to Anthropic Claude"
            )

        if any(kw in lower_desc or kw in lower_intent for kw in ["api", "backend", "database", "sql", "fastapi", "spring", "express"]):
            return RouteDecision(
                provider="openai",
                model="gpt-4o",
                reason="Backend API & System Engineering routed to OpenAI GPT-4o"
            )

        if any(kw in lower_desc or kw in lower_intent for kw in ["fast", "quick", "instant", "summarize", "latency"]):
            return RouteDecision(
                provider="groq",
                model="llama-3.3-70b-versatile",
                reason="High speed low-latency reasoning routed to Groq"
            )

        if any(kw in lower_desc or kw in lower_intent for kw in ["long", "document", "deep research", "analysis", "rag"]):
            return RouteDecision(
                provider="gemini",
                model="gemini-1.5-pro",
                reason="Large context window & deep reasoning routed to Google Gemini"
            )

        if any(kw in lower_desc or kw in lower_intent for kw in ["refactor", "review", "bug", "debug", "audit"]):
            return RouteDecision(
                provider="deepseek",
                model="deepseek-chat",
                reason="Code refactoring & bug audit routed to DeepSeek"
            )

        # Default fallback
        return RouteDecision(
            provider="openai",
            model="gpt-4o",
            reason="Default system routing to OpenAI GPT-4o"
        )
