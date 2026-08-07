"""
Project Memory & Incremental File Updater Engine for Vikrm AI Platform.
Stores project architecture and files in DB, and performs incremental edits
on existing workspaces without re-generating unchanged files.
"""

from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.project import Project, ProjectFile

class ProjectMemoryEngine:
    @classmethod
    async def get_workspace_files(cls, session: AsyncSession, project_id: int) -> Dict[str, str]:
        """
        Retrieves all active files in a given project workspace from DB.
        """
        res = await session.execute(select(ProjectFile).where(ProjectFile.project_id == project_id))
        files = res.scalars().all()
        return {f.path: f.content for f in files}

    @classmethod
    async def process_incremental_edit(
        cls,
        session: AsyncSession,
        project_id: int,
        prompt: str,
        existing_files: Dict[str, str]
    ) -> Dict[str, str]:
        """
        Processes an incremental edit request ('Add Stripe Payments', 'Fix auth', 'Update theme') on an active workspace.
        Generates and updates ONLY changed or new files instead of re-generating the entire project.
        """
        from app.services.project.incremental_edit_engine import IncrementalEditEngine, WorkspaceContext
        ctx = WorkspaceContext()
        ctx.load_from_files(existing_files)
        
        delta_files, changed_paths = IncrementalEditEngine.apply_edit(ctx, prompt)
        
        # Persist modified files into database
        for path in changed_paths:
            content = delta_files.get(path, "")
            res = await session.execute(
                select(ProjectFile).where(ProjectFile.project_id == project_id, ProjectFile.path == path)
            )
            pf = res.scalar_one_or_none()
            if pf:
                pf.content = content
            else:
                ext = path.split(".")[-1].lower() if "." in path else ""
                lang_map = {
                    "ts": "typescript", "tsx": "typescript",
                    "js": "javascript", "jsx": "javascript",
                    "py": "python", "json": "json", "html": "html",
                    "css": "css", "md": "markdown"
                }
                pf = ProjectFile(
                    project_id=project_id,
                    path=path,
                    content=content,
                    language=lang_map.get(ext, "text"),
                )
                session.add(pf)

        await session.commit()
        return delta_files
