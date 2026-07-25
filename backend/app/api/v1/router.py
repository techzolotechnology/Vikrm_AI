"""
Aggregates all v1 routers into one. Future milestones append their
router here (e.g. `api_router.include_router(auth.router, prefix="/auth")`)
rather than main.py knowing about every individual module.
"""
from fastapi import APIRouter

from app.api.v1 import (
    admin,
    agent_teams,
    agents,
    analytics,
    auth,
    chat,
    documents,
    health,
    memory,
    providers,
    tools,
    users,
    workflows,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(users.router)
api_router.include_router(chat.router)
api_router.include_router(providers.router)
api_router.include_router(agents.router)
api_router.include_router(memory.router)
api_router.include_router(documents.router)
api_router.include_router(workflows.router)
api_router.include_router(tools.router)
api_router.include_router(agent_teams.router)
api_router.include_router(analytics.router)
api_router.include_router(admin.router)
