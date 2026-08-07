"""
Central API v1 router.
"""
from fastapi import APIRouter

from app.api.v1 import (
    admin,
    agent_teams,
    agents,
    ai_file_actions,
    analytics,
    attachments,
    auth,
    chat,
    datasets,
    deployments,
    documents,
    github,
    git,
    health,
    huggingface,
    memory,
    projects,
    providers,
    search,
    terminal,
    tools,
    users,
    workflows,
)

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(agents.router)
api_router.include_router(ai_file_actions.router)
api_router.include_router(chat.router)
api_router.include_router(agent_teams.router)
api_router.include_router(workflows.router)
api_router.include_router(tools.router)
api_router.include_router(memory.router)
api_router.include_router(documents.router)
api_router.include_router(attachments.router)
api_router.include_router(analytics.router)
api_router.include_router(providers.router)
api_router.include_router(projects.router)
api_router.include_router(huggingface.router)
api_router.include_router(datasets.router)
api_router.include_router(terminal.router)
api_router.include_router(github.router)
api_router.include_router(git.router)
api_router.include_router(deployments.router)
api_router.include_router(search.router)
api_router.include_router(admin.router)

