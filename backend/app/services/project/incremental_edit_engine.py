"""
Incremental Edit Engine — Phase 6 & 7 of the AI Software Engineering Agent.

Phase 6: Surgical file-level patching.
  When user says 'Add Stripe', 'Fix the auth bug', 'Add dark mode', etc.:
  - Do NOT regenerate the entire project
  - Identify only the files that need to change
  - Apply targeted patches (imports, routes, env vars, deps, docs)

Phase 7: Context Preservation.
  Remembers framework, theme, folder layout, dependencies, coding style,
  API conventions for the active workspace session.
"""

from __future__ import annotations

import json
import re
from typing import Any
from dataclasses import dataclass, field, asdict
from app.core.logging import get_logger

logger = get_logger(__name__)


# ─────────────────────────────────────────────
# Phase 7: Workspace Context Store
# ─────────────────────────────────────────────

@dataclass
class WorkspaceContext:
    """
    Persists workspace intelligence across conversation turns.
    Knows every file, every component, every API, every hook.
    """
    project_name: str = ""
    project_slug: str = ""
    domain: str = ""
    framework: str = ""
    css_framework: str = "Tailwind CSS"
    database: str = ""
    auth_strategy: str = ""
    state_management: str = ""
    api_base_url: str = "http://localhost:8000"
    coding_style: str = "TypeScript strict mode, functional components, custom hooks"
    # File manifest
    files: dict[str, str] = field(default_factory=dict)
    # Extracted knowledge
    components: list[str] = field(default_factory=list)
    hooks: list[str] = field(default_factory=list)
    pages: list[str] = field(default_factory=list)
    api_endpoints: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    env_vars: list[str] = field(default_factory=list)
    db_tables: list[str] = field(default_factory=list)
    # Edit history
    edit_history: list[dict] = field(default_factory=list)

    def load_from_files(self, files: dict[str, str]) -> None:
        """Extract workspace intelligence from generated project files."""
        self.files = files

        for path, content in files.items():
            # Extract component names (export function X)
            if path.endswith((".tsx", ".jsx")) and "/components/" in path:
                matches = re.findall(r"export (?:function|const) (\w+)", content)
                self.components.extend(matches)

            # Extract hook names
            if path.endswith((".ts", ".tsx")) and ("/hooks/" in path or "use" in path.lower()):
                matches = re.findall(r"export (?:function|const) (use\w+)", content)
                self.hooks.extend(matches)

            # Extract page names
            if "Page.tsx" in path or "/pages/" in path:
                matches = re.findall(r"export (?:function|const) (\w+Page)", content)
                self.pages.extend(matches)

            # Extract FastAPI endpoints
            if path.endswith(".py") and "server/" in path:
                matches = re.findall(r'@app\.(get|post|put|delete|patch)\("([^"]+)"', content)
                self.api_endpoints.extend(f"{m[0].upper()} {m[1]}" for m in matches)

            # Extract env vars
            if path == ".env.example":
                self.env_vars = [
                    line.split("=")[0].strip()
                    for line in content.splitlines()
                    if "=" in line and not line.startswith("#") and line.strip()
                ]

            # Extract dependencies from package.json
            if path == "package.json":
                try:
                    pkg = json.loads(content)
                    self.dependencies = list(pkg.get("dependencies", {}).keys())
                except Exception:
                    pass

            # Extract SQL tables from server schema
            if path.endswith(".sql"):
                matches = re.findall(r"CREATE TABLE(?:\s+IF NOT EXISTS)?\s+(\w+)", content, re.IGNORECASE)
                self.db_tables.extend(matches)

        # Deduplicate
        self.components = sorted(set(self.components))
        self.hooks = sorted(set(self.hooks))
        self.pages = sorted(set(self.pages))
        self.api_endpoints = sorted(set(self.api_endpoints))

    def to_context_summary(self) -> str:
        """Returns a compact context string for injection into LLM system prompt."""
        return (
            f"## Active Workspace Context\n"
            f"- Project: {self.project_name} ({self.domain})\n"
            f"- Framework: {self.framework}\n"
            f"- Database: {self.database}\n"
            f"- Auth: {self.auth_strategy}\n"
            f"- Files: {len(self.files)} files\n"
            f"- Components: {', '.join(self.components[:10])}\n"
            f"- Pages: {', '.join(self.pages[:8])}\n"
            f"- Hooks: {', '.join(self.hooks[:8])}\n"
            f"- API Endpoints: {', '.join(self.api_endpoints[:10])}\n"
            f"- Dependencies: {', '.join(self.dependencies[:10])}\n"
            f"- Env Vars: {', '.join(self.env_vars[:8])}\n"
            f"- DB Tables: {', '.join(self.db_tables)}\n"
            f"- Coding Style: {self.coding_style}\n"
        )


# In-memory workspace store (production: use Redis/DB)
_workspace_store: dict[str, WorkspaceContext] = {}


def get_workspace_context(conversation_id: str) -> WorkspaceContext | None:
    return _workspace_store.get(conversation_id)


def save_workspace_context(conversation_id: str, ctx: WorkspaceContext) -> None:
    _workspace_store[conversation_id] = ctx
    logger.info("[WorkspaceContext] Saved context for conversation=%s files=%d", conversation_id, len(ctx.files))


# ─────────────────────────────────────────────
# Phase 6: Incremental Edit Engine
# ─────────────────────────────────────────────

class EditClassifier:
    """Classifies an edit request into the set of files that need updating."""

    EDIT_PATTERNS: list[tuple[list[str], list[str], str]] = [
        # (keywords, target_file_patterns, description)
        (["stripe", "payment", "checkout"], ["package.json", ".env.example", "src/api/", "server/main.py", "README.md"], "payment_integration"),
        (["auth", "login", "password", "jwt", "oauth"], ["src/context/AuthContext.tsx", "src/pages/LoginPage.tsx", "server/main.py", ".env.example"], "auth_update"),
        (["dark mode", "theme", "color scheme", "design", "style"], ["src/index.css", "tailwind.config.js"], "theme_update"),
        (["docker", "deployment", "ci/cd", "github actions", "kubernetes"], ["Dockerfile", "docker-compose.yml", ".github/workflows/ci.yml", "README.md"], "deployment_update"),
        (["database", "db", "model", "schema", "migration", "table"], ["server/main.py", "server/schema.sql"], "database_update"),
        (["test", "testing", "vitest", "pytest", "coverage"], ["src/__tests__/", "server/tests/", "package.json"], "test_update"),
        (["api", "endpoint", "route", "rest"], ["server/main.py", "src/api/"], "api_update"),
        (["redux", "zustand", "context", "state"], ["src/context/", "src/hooks/", "package.json"], "state_update"),
        (["readme", "documentation", "docs"], ["README.md"], "docs_update"),
        (["environment", "env", "config", "settings"], [".env.example", "vite.config.ts", "server/main.py"], "config_update"),
    ]

    @classmethod
    def classify(cls, edit_prompt: str) -> tuple[str, list[str]]:
        """Returns (edit_type, list of file_patterns_to_update)."""
        lower = edit_prompt.lower()
        for keywords, patterns, edit_type in cls.EDIT_PATTERNS:
            if any(kw in lower for kw in keywords):
                return edit_type, patterns
        return "general_edit", []


class IncrementalEditEngine:
    """
    Phase 6 — Applies surgical patches to the active workspace.
    Only modifies files that are actually affected by the edit request.
    """

    @classmethod
    def apply_edit(cls, ctx: WorkspaceContext, edit_prompt: str) -> tuple[dict[str, str], list[str]]:
        """
        Apply a targeted edit to the workspace context.
        Returns (updated_files_dict, list_of_changed_paths).
        """
        edit_type, file_patterns = EditClassifier.classify(edit_prompt)
        lower = edit_prompt.lower()

        changed_files: dict[str, str] = {}
        changed_paths: list[str] = []

        # Determine which actual files match the patterns
        target_files = cls._resolve_target_files(ctx.files, file_patterns)

        if edit_type == "payment_integration" and "stripe" in lower:
            changed_files, changed_paths = cls._add_stripe(ctx, target_files)
        elif edit_type == "theme_update":
            changed_files, changed_paths = cls._update_theme(ctx, target_files, lower)
        elif edit_type == "auth_update":
            changed_files, changed_paths = cls._update_auth(ctx, target_files, lower)
        elif edit_type == "deployment_update":
            changed_files, changed_paths = cls._update_deployment(ctx, target_files, lower)
        elif edit_type == "test_update":
            changed_files, changed_paths = cls._update_tests(ctx, target_files, lower)
        elif edit_type == "docs_update":
            changed_files, changed_paths = cls._update_readme(ctx, lower)
        else:
            # Generic: add a comment header noting the applied edit
            for path, content in target_files.items():
                updated = f"// [Edit Applied: {edit_prompt[:60]}]\n{content}"
                changed_files[path] = updated
                changed_paths.append(path)

        # Record edit history
        ctx.edit_history.append({
            "prompt": edit_prompt,
            "type": edit_type,
            "changed_files": changed_paths,
        })

        # Update context files
        ctx.files.update(changed_files)

        logger.info("[IncrementalEdit] type=%s changed=%d files", edit_type, len(changed_paths))
        return changed_files, changed_paths

    @classmethod
    def _resolve_target_files(cls, all_files: dict[str, str], patterns: list[str]) -> dict[str, str]:
        """Filter files that match any of the given patterns."""
        result: dict[str, str] = {}
        for pattern in patterns:
            for path, content in all_files.items():
                if path == pattern or path.startswith(pattern.rstrip("/")):
                    result[path] = content
        return result

    @classmethod
    def _add_stripe(cls, ctx: WorkspaceContext, target_files: dict[str, str]) -> tuple[dict[str, str], list[str]]:
        changed: dict[str, str] = {}
        paths: list[str] = []

        # 1. Add stripe to package.json
        if "package.json" in ctx.files:
            try:
                pkg = json.loads(ctx.files["package.json"])
                if "stripe" not in pkg.get("dependencies", {}):
                    pkg["dependencies"]["@stripe/stripe-js"] = "^4.0.0"
                    pkg["dependencies"]["@stripe/react-stripe-js"] = "^2.7.0"
                changed["package.json"] = json.dumps(pkg, indent=2)
                paths.append("package.json")
            except Exception:
                pass

        # 2. Add Stripe env vars
        if ".env.example" in ctx.files:
            env = ctx.files[".env.example"]
            if "STRIPE" not in env:
                env += "\n# Stripe Payments\nSTRIPE_PUBLISHABLE_KEY=pk_test_...\nSTRIPE_SECRET_KEY=sk_test_...\nSTRIPE_WEBHOOK_SECRET=whsec_...\n"
                changed[".env.example"] = env
                paths.append(".env.example")

        # 3. Add Stripe API module
        stripe_api = (
            "/**\n"
            " * Stripe Payment API Client\n"
            " * Handles payment intents, subscriptions, and webhook verification.\n"
            " */\n"
            "import { loadStripe } from '@stripe/stripe-js';\n\n"
            "export const stripePromise = loadStripe(\n"
            "  import.meta.env.VITE_STRIPE_PUBLISHABLE_KEY ?? ''\n"
            ");\n\n"
            "export interface PaymentIntentResponse {\n"
            "  client_secret: string;\n"
            "  payment_intent_id: string;\n"
            "  amount: number;\n"
            "  currency: string;\n"
            "}\n\n"
            "export async function createPaymentIntent(\n"
            "  amount: number,\n"
            "  currency = 'usd',\n"
            "): Promise<PaymentIntentResponse> {\n"
            "  const res = await fetch('/api/v1/payments/create-intent', {\n"
            "    method: 'POST',\n"
            "    headers: { 'Content-Type': 'application/json' },\n"
            "    body: JSON.stringify({ amount, currency }),\n"
            "  });\n"
            "  if (!res.ok) throw new Error('Payment intent creation failed');\n"
            "  return res.json();\n"
            "}\n"
        )
        changed["src/api/stripeApi.ts"] = stripe_api
        paths.append("src/api/stripeApi.ts")

        # 4. Add backend Stripe endpoint to server/main.py
        if "server/main.py" in ctx.files:
            backend = ctx.files["server/main.py"]
            if "stripe" not in backend.lower():
                stripe_endpoint = (
                    "\n# ── Stripe Payment Integration ─────────────────\n"
                    "class PaymentIntentRequest(BaseModel):\n"
                    "    amount: int\n"
                    "    currency: str = 'usd'\n\n"
                    "@app.post('/api/v1/payments/create-intent')\n"
                    "async def create_payment_intent(body: PaymentIntentRequest):\n"
                    "    import os\n"
                    "    stripe_key = os.getenv('STRIPE_SECRET_KEY', '')\n"
                    "    if not stripe_key:\n"
                    "        raise HTTPException(400, 'Stripe not configured')\n"
                    "    import stripe as stripe_lib\n"
                    "    stripe_lib.api_key = stripe_key\n"
                    "    intent = stripe_lib.PaymentIntent.create(\n"
                    "        amount=body.amount,\n"
                    "        currency=body.currency,\n"
                    "        automatic_payment_methods={'enabled': True},\n"
                    "    )\n"
                    "    return {'client_secret': intent.client_secret, 'payment_intent_id': intent.id, 'amount': body.amount, 'currency': body.currency}\n"
                )
                changed["server/main.py"] = backend + stripe_endpoint
                paths.append("server/main.py")

        return changed, paths

    @classmethod
    def _update_theme(cls, ctx: WorkspaceContext, target_files: dict[str, str], lower: str) -> tuple[dict[str, str], list[str]]:
        changed: dict[str, str] = {}
        paths: list[str] = []
        if "src/index.css" in ctx.files:
            # Apply a theme update — switch accent color
            if "purple" in lower or "violet" in lower:
                new_primary = "139 92 246"  # violet-500
                accent = "purple"
            elif "rose" in lower or "red" in lower or "pink" in lower:
                new_primary = "244 63 94"  # rose-500
                accent = "rose"
            elif "emerald" in lower or "green" in lower:
                new_primary = "16 185 129"  # emerald-500
                accent = "emerald"
            elif "amber" in lower or "yellow" in lower or "orange" in lower:
                new_primary = "245 158 11"  # amber-500
                accent = "amber"
            else:
                new_primary = "99 102 241"  # indigo-500 (default)
                accent = "indigo"
            css = ctx.files["src/index.css"]
            css = re.sub(r"--primary:\s*[\d\s]+;", f"--primary: {new_primary};", css)
            css += f"\n/* Theme updated to {accent} accent */\n"
            changed["src/index.css"] = css
            paths.append("src/index.css")
        return changed, paths

    @classmethod
    def _update_auth(cls, ctx: WorkspaceContext, target_files: dict[str, str], lower: str) -> tuple[dict[str, str], list[str]]:
        changed: dict[str, str] = {}
        paths: list[str] = []
        if "google" in lower and "src/context/AuthContext.tsx" in ctx.files:
            # Add Google OAuth link to auth context
            auth = ctx.files["src/context/AuthContext.tsx"]
            if "googleLogin" not in auth:
                auth += (
                    "\nexport function googleLogin() {\n"
                    "  window.location.href = `${import.meta.env.VITE_API_BASE_URL}/api/v1/auth/google`;\n"
                    "}\n"
                )
                changed["src/context/AuthContext.tsx"] = auth
                paths.append("src/context/AuthContext.tsx")
        if "2fa" in lower or "two factor" in lower or "mfa" in lower:
            if ".env.example" in ctx.files:
                env = ctx.files[".env.example"]
                if "TOTP" not in env:
                    env += "\n# Two-Factor Authentication\nTOTP_SECRET_KEY=change-me-totp-key\n"
                    changed[".env.example"] = env
                    paths.append(".env.example")
        return changed, paths

    @classmethod
    def _update_deployment(cls, ctx: WorkspaceContext, target_files: dict[str, str], lower: str) -> tuple[dict[str, str], list[str]]:
        changed: dict[str, str] = {}
        paths: list[str] = []
        if "kubernetes" in lower or "k8s" in lower:
            k8s = (
                "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: app\nspec:\n"
                "  replicas: 3\n  selector:\n    matchLabels:\n      app: web\n"
                "  template:\n    metadata:\n      labels:\n        app: web\n"
                "    spec:\n      containers:\n      - name: web\n        image: vikrm/app:latest\n"
                "        ports:\n        - containerPort: 80\n"
                "        env:\n        - name: NODE_ENV\n          value: production\n"
            )
            changed["k8s/deployment.yaml"] = k8s
            paths.append("k8s/deployment.yaml")
        if "vercel" in lower:
            vercel = '{\n  "buildCommand": "npm run build",\n  "outputDirectory": "dist",\n  "installCommand": "npm ci",\n  "framework": "vite"\n}\n'
            changed["vercel.json"] = vercel
            paths.append("vercel.json")
        return changed, paths

    @classmethod
    def _update_tests(cls, ctx: WorkspaceContext, target_files: dict[str, str], lower: str) -> tuple[dict[str, str], list[str]]:
        changed: dict[str, str] = {}
        paths: list[str] = []
        if "playwright" in lower or "e2e" in lower:
            test = (
                "import { test, expect } from '@playwright/test';\n\n"
                "test('full auth flow', async ({ page }) => {\n"
                "  await page.goto('/login');\n"
                "  await page.getByPlaceholder('you@example.com').fill('test@example.com');\n"
                "  await page.getByPlaceholder('••••••••').fill('password123');\n"
                "  await page.getByRole('button', { name: /sign in/i }).click();\n"
                "  await page.waitForURL('/');\n"
                "  await expect(page.getByText('Welcome back')).toBeVisible();\n"
                "});\n"
            )
            changed["tests/e2e/auth.spec.ts"] = test
            paths.append("tests/e2e/auth.spec.ts")
        return changed, paths

    @classmethod
    def _update_readme(cls, ctx: WorkspaceContext, lower: str) -> tuple[dict[str, str], list[str]]:
        changed: dict[str, str] = {}
        paths: list[str] = []
        if "README.md" in ctx.files:
            readme = ctx.files["README.md"]
            if "## API Reference" not in readme:
                api_section = (
                    "\n## API Reference\n\n"
                    + "\n".join(f"- `{ep}`" for ep in ctx.api_endpoints[:15])
                    + "\n\nSee `/api/docs` for full OpenAPI documentation.\n"
                )
                readme += api_section
                changed["README.md"] = readme
                paths.append("README.md")
        return changed, paths
