"""
Projects API Router.
Handles project creation, file management, template listing, ZIP downloads, and AI edits.
"""
import re
from typing import Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.project import Project, ProjectFile, ProjectStatus
from app.models.user import User
from app.services.project.generator import ProjectGenerator
from app.services.project.templates import TEMPLATES, ProjectTemplate

router = APIRouter(prefix="/projects", tags=["Projects"])


class CreateProjectRequest(BaseModel):
    title: str = Field(..., max_length=255)
    description: Optional[str] = None
    template: str = Field("react", description="Template ID")
    custom_prompt: Optional[str] = None


class SaveFileRequest(BaseModel):
    path: str
    content: str
    language: Optional[str] = "text"


class AIEditFileRequest(BaseModel):
    path: str
    instruction: str
    content: str


@router.get("/templates")
async def list_templates(_user: User = Depends(get_current_user)):
    """List all available project templates."""
    return [
        {
            "id": t.id,
            "name": t.name,
            "category": t.category,
            "framework": t.framework,
            "description": t.description,
            "icon": t.icon,
            "file_count": len(t.files),
        }
        for t in TEMPLATES.values()
    ]


@router.get("")
async def list_projects(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Project).where(Project.user_id == user.id).order_by(Project.updated_at.desc())
    res = await db.execute(stmt)
    projects = res.scalars().all()
    return [
        {
            "id": p.id,
            "title": p.title,
            "description": p.description,
            "template": p.template,
            "framework": p.framework,
            "status": p.status,
            "file_count": len(p.files),
            "updated_at": p.updated_at.isoformat(),
        }
        for p in projects
    ]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_project(
    req: CreateProjectRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    project = await ProjectGenerator.create_project(
        db,
        user_id=user.id,
        title=req.title,
        description=req.description,
        template_id=req.template,
        custom_prompt=req.custom_prompt,
    )
    return {
        "id": project.id,
        "title": project.title,
        "description": project.description,
        "template": project.template,
        "framework": project.framework,
        "status": project.status,
        "files": [{"id": f.id, "path": f.path, "language": f.language} for f in project.files],
    }


@router.get("/{project_id}")
async def get_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Project).where(Project.id == project_id, Project.user_id == user.id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return {
        "id": project.id,
        "title": project.title,
        "description": project.description,
        "template": project.template,
        "framework": project.framework,
        "status": project.status,
        "files": [
            {
                "id": f.id,
                "path": f.path,
                "content": f.content,
                "language": f.language,
                "updated_at": f.updated_at.isoformat(),
            }
            for f in project.files
        ],
    }


@router.post("/{project_id}/files")
async def save_project_file(
    project_id: int,
    req: SaveFileRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Project).where(Project.id == project_id, Project.user_id == user.id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Find existing file by path or create new
    file_stmt = select(ProjectFile).where(
        ProjectFile.project_id == project_id, ProjectFile.path == req.path
    )
    file_res = await db.execute(file_stmt)
    pf = file_res.scalar_one_or_none()

    if pf:
        pf.content = req.content
        if req.language:
            pf.language = req.language
    else:
        pf = ProjectFile(
            project_id=project_id,
            path=req.path,
            content=req.content,
            language=req.language or "text",
        )
        db.add(pf)

    await db.commit()
    await db.refresh(pf)
    return {
        "id": pf.id,
        "path": pf.path,
        "content": pf.content,
        "language": pf.language,
    }


@router.delete("/{project_id}/files/{file_id}")
async def delete_project_file(
    project_id: int,
    file_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(ProjectFile).join(Project).where(
        ProjectFile.id == file_id,
        ProjectFile.project_id == project_id,
        Project.user_id == user.id,
    )
    res = await db.execute(stmt)
    pf = res.scalar_one_or_none()
    if not pf:
        raise HTTPException(status_code=404, detail="File not found")

    await db.delete(pf)
    await db.commit()
    return {"message": "File deleted successfully"}


@router.get("/{project_id}/download")
async def download_project_zip(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Project).where(Project.id == project_id, Project.user_id == user.id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    zip_bytes = ProjectGenerator.generate_zip_archive(project.files)
    filename = f"{project.title.lower().replace(' ', '_')}_export.zip"

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


class ExportZipRequest(BaseModel):
    title: str = "project"
    files: Dict[str, str]


@router.post("/download-zip")
async def download_dict_zip(payload: ExportZipRequest):
    zip_bytes = ProjectGenerator.generate_zip_from_dict(payload.files)
    clean_title = re.sub(r"[^\w\s-]", "", payload.title).strip().replace(" ", "_").lower() or "project"
    filename = f"{clean_title}_export.zip"

    return Response(
        content=zip_bytes,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )



@router.post("/{project_id}/build-loop")
async def run_project_build_loop(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    from app.services.project.build_loop import BuildLoopEngine
    stmt = select(Project).where(Project.id == project_id, Project.user_id == user.id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    results = await BuildLoopEngine.run_build_loop(project_id)
    return {"project_id": project_id, "steps": [r.__dict__ for r in results]}


class RenameFileRequest(BaseModel):
    old_path: str
    new_path: str


class MoveFileRequest(BaseModel):
    old_path: str
    target_folder: str


class CreateFolderRequest(BaseModel):
    folder_path: str


@router.patch("/{project_id}/files/rename")
async def rename_project_file(
    project_id: int,
    req: RenameFileRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(ProjectFile).join(Project).where(
        ProjectFile.project_id == project_id,
        ProjectFile.path == req.old_path,
        Project.user_id == user.id,
    )
    res = await db.execute(stmt)
    pf = res.scalar_one_or_none()
    if not pf:
        raise HTTPException(status_code=404, detail="File not found")

    pf.path = req.new_path.strip().lstrip("/")
    await db.commit()
    await db.refresh(pf)
    return {"id": pf.id, "old_path": req.old_path, "new_path": pf.path}


@router.patch("/{project_id}/files/move")
async def move_project_file(
    project_id: int,
    req: MoveFileRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(ProjectFile).join(Project).where(
        ProjectFile.project_id == project_id,
        ProjectFile.path == req.old_path,
        Project.user_id == user.id,
    )
    res = await db.execute(stmt)
    pf = res.scalar_one_or_none()
    if not pf:
        raise HTTPException(status_code=404, detail="File not found")

    filename = req.old_path.split("/")[-1]
    target_folder = req.target_folder.strip().strip("/")
    new_path = f"{target_folder}/{filename}" if target_folder else filename
    pf.path = new_path
    await db.commit()
    await db.refresh(pf)
    return {"id": pf.id, "old_path": req.old_path, "new_path": pf.path}


@router.post("/{project_id}/folders")
async def create_project_folder(
    project_id: int,
    req: CreateFolderRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    stmt = select(Project).where(Project.id == project_id, Project.user_id == user.id)
    res = await db.execute(stmt)
    project = res.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    folder = req.folder_path.strip().strip("/")
    keep_file_path = f"{folder}/.gitkeep"
    
    # Create a placeholder .gitkeep file so folder exists in tree
    pf = ProjectFile(
        project_id=project_id,
        path=keep_file_path,
        content="# Folder initialized",
        language="text",
    )
    db.add(pf)
    await db.commit()
    await db.refresh(pf)
    return {"message": "Folder created successfully", "folder_path": folder, "file_id": pf.id}
