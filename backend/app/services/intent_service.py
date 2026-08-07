"""
Semantic Intent Classification Engine for Vikrm AI Platform.

Strictly classifies incoming user prompts into operational modes.
If prompt contains project creation, building, or tech keywords, Intent = ARTIFACT_PROJECT or EDIT_PROJECT.
"""

import enum
import re
from typing import Dict, Any, List, Optional


class ResponseMode(str, enum.Enum):
    CONVERSATIONAL = "conversational"
    SMALL_CODE = "small_code"
    ARTIFACT_PROJECT = "artifact_project"
    EDIT_PROJECT = "edit_project"
    DEBUG = "debug"
    CODE_REVIEW = "code_review"
    ARCHITECT = "architect"


class IntentService:
    PROJECT_KEYWORDS = [
        "build", "create", "generate", "develop", "make", "scaffold", "implement",
        "website", "web app", "application", "dashboard", "saas", "crm", "erp",
        "hospital", "portfolio", "clone", "next.js", "react", "spring", "fastapi",
        "node", "ai", "backend", "frontend", "full stack", "project", "store",
        "ecommerce", "e-commerce", "netflix", "lms", "cms", "kanban", "trello"
    ]

    EDIT_KEYWORDS = [
        "add", "modify", "update", "fix", "change", "refactor", "remove",
        "optimize", "improve", "convert", "convert to", "add stripe", "add oauth",
        "add google", "add redis", "improve ui", "add auth"
    ]

    BUILD_PREFIXES = ("build ", "create ", "generate ", "make ", "scaffold ", "develop ", "implement ")
    EXPLAIN_PREFIXES = ("explain ", "what is ", "define ", "how does ", "why ", "difference between ")

    @staticmethod
    def classify_intent(
        prompt: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        has_active_workspace: bool = False,
    ) -> Dict[str, Any]:
        """
        Analyzes the semantic intent of the user prompt and context.
        Enforces strict routing: Any project-building keyword forces ARTIFACT_PROJECT or EDIT_PROJECT mode.
        """
        text = prompt.strip()
        lower_text = text.lower()
        word_count = len(text.split())

        # 1. DEBUG MODE (Stack traces & errors)
        debug_keywords = [
            "exception", "traceback", "stack trace", "error:", "failed to",
            "syntaxerror", "typeerror", "nullpointerexception", "undefined is not",
            "uncaught error", "exit code 1", "500 internal server error"
        ]
        if any(kw in lower_text for kw in debug_keywords) or ("\n\tat " in text) or ("File \"" in text and "line " in text):
            return {
                "mode": ResponseMode.DEBUG,
                "confidence": 0.95,
                "reason": "Detected stack trace or error log format",
                "ui_theme": "Cursor / Diagnostic"
            }

        # 2. ARCHITECT MODE
        architect_keywords = [
            "system design", "architecture", "microservice", "er diagram",
            "database schema", "scaling strategy", "api contract", "sequence diagram",
            "design uber", "design system", "design app", "design architecture"
        ]
        if any(kw in lower_text for kw in architect_keywords) or lower_text.startswith("design "):
            return {
                "mode": ResponseMode.ARCHITECT,
                "confidence": 0.92,
                "reason": "System architecture or design diagram requested",
                "ui_theme": "Architect Diagrams"
            }

        # 3. CODE REVIEW MODE
        review_keywords = [
            "review my code", "audit this code", "code review", "security audit",
            "performance audit", "rate this code", "score out of 10", "refactor advice"
        ]
        if any(kw in lower_text for kw in review_keywords) or lower_text.startswith("review "):
            return {
                "mode": ResponseMode.CODE_REVIEW,
                "confidence": 0.92,
                "reason": "Code audit or review requested",
                "ui_theme": "Staff Engineer Review"
            }

        is_explicit_explanation = lower_text.startswith(IntentService.EXPLAIN_PREFIXES)

        # 4. ARTIFACT PROJECT MODE (Building new project)
        has_project_keyword = any(kw in lower_text for kw in IntentService.PROJECT_KEYWORDS)
        if has_project_keyword and not is_explicit_explanation:
            return {
                "mode": ResponseMode.ARTIFACT_PROJECT,
                "confidence": 0.99,
                "reason": f"Prompt contains project generation intent ('{prompt[:40]}...')",
                "ui_theme": "Claude Artifacts / Replit"
            }

        # 5. EDIT PROJECT MODE (Incremental workspace modifications)
        is_edit_intent = (
            any(lower_text.startswith(kw + " ") for kw in IntentService.EDIT_KEYWORDS) or
            any(kw in lower_text for kw in ["add stripe", "add oauth", "add redis", "improve ui", "convert to next.js"]) or
            (has_active_workspace and any(kw in lower_text for kw in ["add", "modify", "update", "fix", "change", "refactor"]))
        )
        if is_edit_intent and not is_explicit_explanation:
            return {
                "mode": ResponseMode.EDIT_PROJECT,
                "confidence": 0.95,
                "reason": "Incremental workspace edit requested",
                "ui_theme": "Cursor Diff"
            }

        # 6. SMALL CODE MODE (Quick isolated snippet)
        snippet_patterns = [
            r"\b(write|show|python|js|ts|java|c\+\+|sql)\b.*\b(function|script|query|sort|button|class|regex)\b",
            r"\b(bubble sort|fibonacci|binary search|hello world|reverse string)\b"
        ]
        if any(re.search(pat, lower_text) for pat in snippet_patterns) or (word_count <= 15 and lower_text.startswith("write ")):
            return {
                "mode": ResponseMode.SMALL_CODE,
                "confidence": 0.85,
                "reason": "Single function or code snippet requested",
                "ui_theme": "Copilot Inline"
            }

        # 7. CONVERSATIONAL MODE (Default for general questions)
        return {
            "mode": ResponseMode.CONVERSATIONAL,
            "confidence": 0.80,
            "reason": "General question, definition, or explanation requested",
            "ui_theme": "ChatGPT Conversational"
        }
