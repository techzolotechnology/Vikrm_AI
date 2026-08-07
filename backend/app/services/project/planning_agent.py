"""
Phase 1 & Phase 2 — True Planning Agent & Dynamic Task Decomposition Engine.

Generates unlimited, feature-driven multi-file project plans without artificial truncation or fixed limits.
Supports complexity estimation scaling from Small (20-40 files) to Enterprise (500+ files).
"""

from typing import Any, Dict, List, Tuple
from pydantic import BaseModel, Field


DOMAIN_PATTERNS: List[Tuple[List[str], str]] = [
    (["hospital", "medical", "patient", "doctor", "health", "ehr", "clinic"], "healthcare"),
    (["ecommerce", "e-commerce", "store", "shop", "cart", "checkout", "stripe"], "ecommerce"),
    (["saas", "dashboard", "analytics", "admin", "telemetry", "metrics"], "enterprise_saas"),
    (["portfolio", "developer", "resume", "showcase"], "portfolio"),
    (["media", "stream", "video", "netflix", "movie"], "media_streaming"),
    (["chat", "messaging", "websocket", "slack", "discord"], "realtime_chat"),
    (["fintech", "wallet", "banking", "transaction", "payment", "ledger"], "fintech"),
    (["social", "feed", "post", "comment", "twitter", "instagram"], "social_platform"),
    (["ai", "llm", "embedding", "rag", "chatgpt"], "ai_platform"),
    (["cms", "blog", "article", "post", "content"], "cms"),
    (["kanban", "trello", "jira", "task", "todo", "productivity"], "productivity"),
    (["restaurant", "food", "order", "menu", "dining"], "restaurant"),
    (["lms", "education", "course", "student", "learning"], "education"),
    (["real estate", "property", "listing", "agent", "mortgage"], "real_estate"),
    (["erp", "enterprise resource planning", "supply chain", "logistics", "manufacturing"], "erp"),
]

STACK_PROFILES: Dict[str, Dict[str, Any]] = {
    "healthcare": {
        "framework": "React 19 + TypeScript + FastAPI",
        "css": "Tailwind CSS",
        "database": "PostgreSQL (SQLAlchemy ORM)",
        "auth": "JWT + RBAC (Doctor / Nurse / Admin roles)",
        "state": "React Context + useReducer",
        "api": "REST (FastAPI) + OpenAPI docs",
        "deployment": "Docker + docker-compose",
        "test_framework": "vitest + pytest",
        "dependencies": ["react", "react-dom", "react-router-dom", "lucide-react", "fastapi", "sqlalchemy", "passlib", "python-jose"],
        "base_modules": ["Auth", "Patients", "Appointments", "Doctors", "Billing", "EHR", "Pharmacy", "Laboratory", "Inpatient", "Radiology", "Emergency", "Reports", "Inventory", "Telemedicine", "Insurance", "Audit", "Users", "Settings", "Analytics", "Payments", "Notifications"],
    },
    "erp": {
        "framework": "React 19 + TypeScript + FastAPI",
        "css": "Tailwind CSS",
        "database": "PostgreSQL + Redis",
        "auth": "OAuth2 + JWT + MFA",
        "state": "Zustand + React Query",
        "api": "REST + OpenAPI",
        "deployment": "Docker + Kubernetes",
        "test_framework": "vitest + pytest",
        "dependencies": ["react", "react-dom", "react-router-dom", "recharts", "lucide-react", "fastapi", "sqlalchemy", "redis"],
        "base_modules": ["Auth", "Inventory", "Procurement", "Sales", "HR", "Payroll", "Accounting", "AssetManagement", "Manufacturing", "Logistics", "CRM", "Projects", "QualityControl", "Compliance", "Customers", "Vendors", "Warehouse", "Audit", "Users", "Settings", "Analytics", "Payments", "Notifications"],
    },
    "ecommerce": {
        "framework": "React 19 + TypeScript + FastAPI",
        "css": "Tailwind CSS",
        "database": "PostgreSQL + Redis (sessions)",
        "auth": "JWT + OAuth2 (Google)",
        "state": "Zustand (cart) + React Context (auth)",
        "api": "REST (FastAPI) + Stripe Webhooks",
        "deployment": "Docker + Vercel (frontend)",
        "test_framework": "vitest + pytest",
        "dependencies": ["react", "react-dom", "react-router-dom", "lucide-react", "zustand", "fastapi", "stripe", "passlib"],
        "base_modules": ["Auth", "Catalog", "ProductDetail", "Cart", "Checkout", "Orders", "Admin", "Payments", "Inventory", "Reviews", "Recommendations", "Discounts", "Shipping", "Customers", "Vendors", "Analytics"],
    },
    "enterprise_saas": {
        "framework": "React 19 + TypeScript + FastAPI",
        "css": "Tailwind CSS",
        "database": "PostgreSQL + Redis",
        "auth": "OAuth2 + JWT + MFA",
        "state": "Zustand + React Query",
        "api": "REST + GraphQL",
        "deployment": "Docker + Kubernetes",
        "test_framework": "vitest + playwright",
        "dependencies": ["react", "react-dom", "react-router-dom", "recharts", "lucide-react", "zustand", "fastapi", "redis"],
        "base_modules": ["Auth", "Dashboard", "Analytics", "Users", "Teams", "Settings", "Reports", "Billing", "Audit", "Workspaces", "Integrations", "APIKeys", "Webhooks", "Security", "Notifications"],
    },
    "portfolio": {
        "framework": "React 19 + TypeScript",
        "css": "Tailwind CSS + framer-motion",
        "database": "None (static data)",
        "auth": "None",
        "state": "Local state only",
        "api": "EmailJS (contact form)",
        "deployment": "Netlify / Vercel",
        "test_framework": "vitest",
        "dependencies": ["react", "react-dom", "lucide-react", "framer-motion"],
        "base_modules": ["Hero", "About", "Projects", "Skills", "Experience", "Contact", "Testimonials", "Blog"],
    },
    "media_streaming": {
        "framework": "React 19 + TypeScript",
        "css": "Tailwind CSS",
        "database": "External API (TMDB)",
        "auth": "JWT Auth",
        "state": "React Context + localStorage",
        "api": "REST proxy + TMDB API",
        "deployment": "Vercel",
        "test_framework": "vitest",
        "dependencies": ["react", "react-dom", "react-router-dom", "lucide-react"],
        "base_modules": ["Auth", "Hero", "Browse", "MovieCard", "Player", "Search", "Favorites", "Watchlist", "Subtitles", "Recommendations"],
    },
    "realtime_chat": {
        "framework": "React 19 + TypeScript + FastAPI + WebSocket",
        "css": "Tailwind CSS",
        "database": "PostgreSQL + Redis (pub/sub)",
        "auth": "JWT",
        "state": "Zustand + WebSocket context",
        "api": "REST + WebSocket",
        "deployment": "Docker",
        "test_framework": "vitest + pytest",
        "dependencies": ["react", "react-dom", "react-router-dom", "lucide-react", "zustand", "fastapi", "websockets", "redis"],
        "base_modules": ["Auth", "Channels", "Messages", "Users", "Notifications", "FileUploads", "DirectMessages", "Search"],
    },
    "fintech": {
        "framework": "React 19 + TypeScript + FastAPI",
        "css": "Tailwind CSS",
        "database": "PostgreSQL (double-entry ledger)",
        "auth": "JWT + 2FA",
        "state": "Zustand",
        "api": "REST + Stripe API",
        "deployment": "Docker + AWS",
        "test_framework": "vitest + pytest",
        "dependencies": ["react", "react-dom", "react-router-dom", "recharts", "lucide-react", "fastapi", "stripe", "passlib"],
        "base_modules": ["Auth", "Wallet", "Transactions", "Payments", "Statements", "Analytics", "Accounts", "Cards", "Transfers", "FraudCheck"],
    },
    "social_platform": {
        "framework": "React 19 + TypeScript + FastAPI",
        "css": "Tailwind CSS",
        "database": "PostgreSQL",
        "auth": "JWT + OAuth2",
        "state": "Zustand + React Query",
        "api": "REST + SSE (feed updates)",
        "deployment": "Docker",
        "test_framework": "vitest",
        "dependencies": ["react", "react-dom", "react-router-dom", "lucide-react", "zustand", "fastapi"],
        "base_modules": ["Auth", "Feed", "Profile", "Posts", "Comments", "Follow", "Explore", "Notifications", "DirectMessages", "Bookmarks"],
    },
    "ai_platform": {
        "framework": "React 19 + TypeScript + FastAPI",
        "css": "Tailwind CSS",
        "database": "PostgreSQL + pgvector",
        "auth": "JWT + API Keys",
        "state": "Zustand",
        "api": "REST + SSE (streaming LLM)",
        "deployment": "Docker + GPU server",
        "test_framework": "vitest + pytest",
        "dependencies": ["react", "react-dom", "react-router-dom", "lucide-react", "zustand", "fastapi", "openai", "langchain"],
        "base_modules": ["Auth", "Chat", "Models", "Embeddings", "Playground", "Usage", "APIKeys", "FineTuning", "VectorSearch", "Prompts"],
    },
    "cms": {
        "framework": "React 19 + TypeScript + FastAPI",
        "css": "Tailwind CSS",
        "database": "PostgreSQL",
        "auth": "JWT (Editor / Admin roles)",
        "state": "React Context",
        "api": "REST (CRUD + slug routing)",
        "deployment": "Docker + Netlify",
        "test_framework": "vitest",
        "dependencies": ["react", "react-dom", "react-router-dom", "lucide-react", "fastapi"],
        "base_modules": ["Auth", "Articles", "Editor", "Categories", "Comments", "Tags", "Authors", "Subscriptions", "SEO", "MediaLibrary", "Analytics", "Admin"],
    },
    "productivity": {
        "framework": "React 19 + TypeScript",
        "css": "Tailwind CSS",
        "database": "localStorage + optional backend",
        "auth": "JWT (optional)",
        "state": "Zustand (drag-drop board state)",
        "api": "REST (optional backend)",
        "deployment": "Vercel",
        "test_framework": "vitest",
        "dependencies": ["react", "react-dom", "lucide-react", "zustand", "@hello-pangea/dnd"],
        "base_modules": ["Board", "Columns", "Cards", "Labels", "Members", "Filters", "Activity", "Attachments", "Checklists", "Milestones"],
    },
}

STACK_PROFILES["general"] = {
    "framework": "React 19 + TypeScript + FastAPI",
    "css": "Tailwind CSS",
    "database": "SQLite / PostgreSQL",
    "auth": "JWT",
    "state": "React Context",
    "api": "REST",
    "deployment": "Docker",
    "test_framework": "vitest",
    "dependencies": ["react", "react-dom", "react-router-dom", "lucide-react", "fastapi"],
    "base_modules": ["Auth", "Core", "UI", "API", "Database", "Dashboard", "Settings", "Notifications"],
}


class ProjectTask(BaseModel):
    id: str
    name: str
    description: str
    phase: str
    depends_on: List[str] = Field(default_factory=list)
    files: List[str] = Field(default_factory=list)


class AgentPlan(BaseModel):
    project_name: str
    project_slug: str
    description: str
    domain: str
    complexity: str  # Small, Medium, Large, Enterprise
    framework: str
    css_framework: str
    database: str
    auth_strategy: str
    state_management: str
    api_strategy: str
    deployment_target: str
    test_framework: str
    key_dependencies: List[str]
    modules: List[str]
    planned_files: int
    estimated_files: int
    tasks: List[ProjectTask]
    folder_structure: List[str]
    rag_context: List[str] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)


class PlanningAgent:
    @classmethod
    def detect_domain(cls, prompt: str) -> str:
        lower = prompt.lower()
        for keywords, domain in DOMAIN_PATTERNS:
            if any(kw in lower for kw in keywords):
                return domain
        return "general"

    @classmethod
    def estimate_complexity(cls, prompt: str, domain: str) -> str:
        """Determines complexity tier: Small, Medium, Large, or Enterprise."""
        lower = prompt.lower()

        if any(kw in lower for kw in ["enterprise", "erp", "hospital", "ehr", "clinical", "saas platform", "500", "multi-tenant"]):
            return "Enterprise"
        elif any(kw in lower for kw in ["ecommerce", "e-commerce", "fintech", "social", "banking", "full platform"]):
            return "Large"
        elif any(kw in lower for kw in ["cms", "blog", "chat", "kanban", "trello", "crm", "lms"]):
            return "Medium"
        elif any(kw in lower for kw in ["portfolio", "landing", "resume", "calculator", "widget"]):
            return "Small"

        domain_defaults = {
            "healthcare": "Enterprise",
            "erp": "Enterprise",
            "ecommerce": "Large",
            "enterprise_saas": "Large",
            "fintech": "Large",
            "cms": "Medium",
            "realtime_chat": "Medium",
            "portfolio": "Small",
        }
        return domain_defaults.get(domain, "Medium")

    @classmethod
    def infer_project_name(cls, prompt: str, domain: str) -> Tuple[str, str]:
        slug_map = {
            "healthcare": ("MediCore Hospital System", "medicore-hospital"),
            "erp": ("Apex Enterprise ERP", "apex-erp"),
            "ecommerce": ("Apex Commerce Platform", "apex-ecommerce"),
            "enterprise_saas": ("Enterprise Control Center", "enterprise-saas"),
            "portfolio": ("Developer Portfolio", "dev-portfolio"),
            "media_streaming": ("StreamHub Platform", "stream-hub"),
            "realtime_chat": ("ChatFlow Messenger", "chatflow"),
            "fintech": ("FinVault Platform", "finvault"),
            "social_platform": ("Nexus Social", "nexus-social"),
            "ai_platform": ("Synapse AI Platform", "synapse-ai"),
            "cms": ("ContentFlow CMS", "contentflow-cms"),
            "productivity": ("TaskBoard Pro", "taskboard-pro"),
            "restaurant": ("ForkTable Restaurant", "forktable"),
            "education": ("EduPath LMS", "edupath-lms"),
            "real_estate": ("PropertyHub", "property-hub"),
        }
        name, slug = slug_map.get(domain, ("Vikrm Custom App", "vikrm-app"))
        return name, slug

    @classmethod
    def decompose_tasks(cls, modules: List[str], domain: str, complexity: str) -> List[ProjectTask]:
        """
        Decomposes project into feature tasks without artificial limits.
        Generates dedicated frontend components, hooks, API clients, FastAPI models, schemas, and tests per module.
        """
        tasks: List[ProjectTask] = []

        # Foundation tasks
        tasks.append(ProjectTask(
            id="T01", name="Project Scaffold",
            description="Initialize package.json, tsconfig.json, vite.config.ts, tailwind.config.js, .gitignore, .env.example",
            phase="scaffold", depends_on=[],
            files=["package.json", "tsconfig.json", "tsconfig.app.json", "vite.config.ts", "tailwind.config.js", "postcss.config.js", "index.html", ".gitignore", ".env.example"]
        ))
        tasks.append(ProjectTask(
            id="T02", name="Design System & Global Styles",
            description="Configure Tailwind CSS tokens, theme colors, typography, glassmorphism, and global CSS",
            phase="scaffold", depends_on=["T01"],
            files=["src/index.css"]
        ))
        tasks.append(ProjectTask(
            id="T03", name="API & State Layer",
            description="HTTP client, auth interceptor, global error handler, and app state store",
            phase="frontend", depends_on=["T01"],
            files=["src/api/apiClient.ts", "src/api/types.ts"]
        ))

        if any(m.lower() in ["auth", "authentication"] for m in modules):
            tasks.append(ProjectTask(
                id="T04", name="Authentication System",
                description="JWT Auth Context, Login, Register, Forgot Password, Reset Password views, and RBAC guards",
                phase="auth", depends_on=["T03"],
                files=[
                    "src/context/AuthContext.tsx",
                    "src/hooks/useAuth.ts",
                    "src/pages/LoginPage.tsx",
                    "src/pages/RegisterPage.tsx",
                    "src/pages/ForgotPasswordPage.tsx",
                ]
            ))

        tasks.append(ProjectTask(
            id="T05", name="Layout Components",
            description="Header, Sidebar, Footer, Breadcrumbs, Notification Bell, and Layout Wrapper",
            phase="frontend", depends_on=["T04" if len(tasks) >= 4 else "T02"],
            files=[
                "src/components/layout/Header.tsx",
                "src/components/layout/Sidebar.tsx",
                "src/components/layout/Footer.tsx",
                "src/components/layout/Layout.tsx",
            ]
        ))

        # Generate feature files per module
        tid = 6
        prev_tid = "T05"
        for mod in modules:
            if mod.lower() in ["auth", "authentication"]:
                continue
            m_slug = mod.lower().replace(" ", "_")
            m_name = mod.replace(" ", "")
            task_id = f"T{tid:02d}"

            module_files = [
                f"src/components/{m_slug}/{m_name}List.tsx",
                f"src/components/{m_slug}/{m_name}Detail.tsx",
                f"src/components/{m_slug}/{m_name}Form.tsx",
                f"src/components/{m_slug}/{m_name}Card.tsx",
                f"src/hooks/use{m_name}.ts",
                f"src/api/{m_slug}Api.ts",
                f"src/pages/{m_name}Page.tsx",
                f"server/app/models/{m_slug}.py",
                f"server/app/schemas/{m_slug}.py",
                f"server/app/api/{m_slug}_routes.py",
                f"src/__tests__/{m_name}.test.tsx",
                f"server/tests/test_{m_slug}.py",
            ]

            tasks.append(ProjectTask(
                id=task_id,
                name=f"{mod} Feature Architecture",
                description=f"Full-stack {mod} module: UI views, state hooks, REST API client, SQLAlchemy model, Pydantic schemas, FastAPI router, and tests.",
                phase="feature",
                depends_on=[prev_tid],
                files=module_files,
            ))
            prev_tid = task_id
            tid += 1

        # Backend Core
        tasks.append(ProjectTask(
            id=f"T{tid:02d}", name="FastAPI Server Core",
            description="FastAPI app initialization, CORS middleware, JWT auth, database session factory, requirements, and Alembic migrations",
            phase="backend", depends_on=["T01"],
            files=[
                "server/main.py",
                "server/config.py",
                "server/database.py",
                "server/auth.py",
                "server/requirements.txt",
                "server/Dockerfile",
                "server/schema.sql",
            ]
        ))
        tid += 1

        # Routing & App Root
        tasks.append(ProjectTask(
            id=f"T{tid:02d}", name="Router & App Root",
            description="React Router v6 setup, ProtectedRoute guards, and App entry point",
            phase="integration", depends_on=[prev_tid],
            files=["src/routes/ProtectedRoute.tsx", "src/App.tsx", "src/main.tsx"]
        ))
        tid += 1

        # Global Testing
        tasks.append(ProjectTask(
            id=f"T{tid:02d}", name="Global Testing Suite",
            description="Vitest unit tests, pytest API tests, Playwright E2E configuration",
            phase="testing", depends_on=[f"T{tid-1:02d}"],
            files=["src/__tests__/App.test.tsx", "server/tests/test_api.py", "playwright.config.ts", "tests/e2e/app.spec.ts"]
        ))
        tid += 1

        # Infrastructure & DevOps
        tasks.append(ProjectTask(
            id=f"T{tid:02d}", name="DevOps & Deployment",
            description="Production Dockerfile, docker-compose.yml, GitHub Actions CI workflow, and README",
            phase="deployment", depends_on=[f"T{tid-1:02d}"],
            files=["Dockerfile", "docker-compose.yml", ".github/workflows/ci.yml", "README.md"]
        ))

        return tasks

    @classmethod
    def plan(cls, prompt: str) -> AgentPlan:
        domain = cls.detect_domain(prompt)
        complexity = cls.estimate_complexity(prompt, domain)
        profile = STACK_PROFILES.get(domain, STACK_PROFILES["general"])
        project_name, project_slug = cls.infer_project_name(prompt, domain)

        modules = list(profile["base_modules"])
        tasks = cls.decompose_tasks(modules, domain, complexity)

        all_files = [f for task in tasks for f in task.files]
        planned_file_count = len(all_files)

        folder_structure = sorted(set(
            "/".join(f.split("/")[:-1])
            for f in all_files
            if "/" in f
        ))

        return AgentPlan(
            project_name=project_name,
            project_slug=project_slug,
            description=f"Production-grade {complexity} {domain.replace('_', ' ').title()} application — generated dynamically by Vikrm AI Software Engineering Agent",
            domain=domain,
            complexity=complexity,
            framework=profile["framework"],
            css_framework=profile["css"],
            database=profile["database"],
            auth_strategy=profile["auth"],
            state_management=profile["state"],
            api_strategy=profile["api"],
            deployment_target=profile["deployment"],
            test_framework=profile["test_framework"],
            key_dependencies=profile["dependencies"],
            modules=modules,
            planned_files=planned_file_count,
            estimated_files=planned_file_count,
            tasks=tasks,
            folder_structure=folder_structure,
            metrics={
                "total_tasks": len(tasks),
                "phases": list({t.phase for t in tasks}),
                "planned_files": planned_file_count,
                "complexity": complexity,
                "domain": domain,
            }
        )
