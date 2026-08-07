"""
Project Generator & Workspace Manager.

Generates complete multi-file projects from templates or custom AI specifications,
manages files, exports ZIP archives, and synchronizes project state.
"""
import io
import json
import os
import zipfile
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.project import Project, ProjectFile, ProjectStatus
from app.services.project.templates import TEMPLATES, ProjectTemplate


class ProjectGenerator:
    @staticmethod
    async def create_project(
        db: AsyncSession,
        *,
        user_id: int,
        title: str,
        description: Optional[str] = None,
        template_id: str = "react",
        custom_prompt: Optional[str] = None,
    ) -> Project:
        tmpl: Optional[ProjectTemplate] = TEMPLATES.get(template_id)
        # Dynamic Architecture Generation
        if custom_prompt or not tmpl:
            prompt = custom_prompt or f"Build a production {title} application with framework {template_id}"
            try:
                from app.services.project.dynamic_generator import DynamicProjectGenerator
                gen_res = DynamicProjectGenerator.generate_project(prompt)
                files_dict = gen_res.get("files", {})
                template_name = "dynamic_ai"
                framework = gen_res.get("agent_plan", {}).framework if hasattr(gen_res.get("agent_plan"), "framework") else "React"
            except Exception as e:
                # Fallback to dynamic scaffold if LLM call fails
                files_dict = tmpl.files if tmpl else {
                    "README.md": f"# {title}\n{description or ''}",
                    "package.json": '{\n  "name": "app",\n  "version": "1.0.0"\n}',
                    "src/App.tsx": 'export function App() {\n  return <div>Vikrm Generated App</div>;\n}',
                }
                template_name = tmpl.id if tmpl else "custom"
                framework = tmpl.framework if tmpl else "React"
        else:
            template_name = tmpl.id
            framework = tmpl.framework
            files_dict = tmpl.files

        # Create database record for project
        project = Project(
            user_id=user_id,
            title=title,
            description=description or f"Project generated dynamically from {template_name}.",
            template=template_name,
            framework=framework,
            status=ProjectStatus.READY,
            metadata_json={"custom_prompt": custom_prompt} if custom_prompt else {},
        )
        db.add(project)
        await db.flush()

        # Insert project files
        for path, content in files_dict.items():
            ext = path.split(".")[-1].lower() if "." in path else ""
            lang_map = {
                "ts": "typescript", "tsx": "typescript",
                "js": "javascript", "jsx": "javascript",
                "py": "python", "json": "json", "html": "html",
                "css": "css", "md": "markdown", "yml": "yaml", "yaml": "yaml",
                "sql": "sql", "sh": "shell", "dart": "dart"
            }
            language = lang_map.get(ext, "text")

            project_file = ProjectFile(
                project_id=project.id,
                path=path,
                content=content,
                language=language,
            )
            db.add(project_file)

        await db.commit()
        await db.refresh(project)
        return project

    @staticmethod
    def generate_zip_archive(files: List[ProjectFile]) -> bytes:
        """Packages all project files into an in-memory ZIP file."""
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for f in files:
                zip_file.writestr(f.path, f.content)
        return zip_buffer.getvalue()

    @staticmethod
    def generate_zip_from_dict(files_dict: Dict[str, str]) -> bytes:
        """Packages a dictionary of file path -> content into an in-memory ZIP archive."""
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for path, content in files_dict.items():
                zip_file.writestr(path, content)
        return zip_buffer.getvalue()

