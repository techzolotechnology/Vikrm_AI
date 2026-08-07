"""
One-Click Deployment Service.

Phase 1 Status: Marked explicitly as not_yet_implemented / simulated pending Phase 8 deployment integration.
"""
from typing import Dict, Optional
from app.models.project import DeploymentTarget, DeploymentStatus


class DeploymentService:
    @classmethod
    async def trigger_deployment(cls, target: str, project_title: str) -> Dict:
        """
        Phase 1: Returns explicit 'not_yet_implemented' status with url=None.
        Real provider API deployment integration will land in Phase 8.
        """
        target_str = target.lower()
        logs = (
            f"[Phase 1 Status] Deployment to target '{target_str}' for project '{project_title}' is not_yet_implemented.\n"
            f"[Phase 8 Pending] Real deployment provider API requests will be activated in Phase 8."
        )

        return {
            "target": target_str,
            "status": DeploymentStatus.PENDING,
            "url": None,
            "logs": logs,
            "is_simulated": True,
            "execution_status": "not_yet_implemented",
        }
