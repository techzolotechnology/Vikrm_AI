"""
Models for Projects, Project Files, Deployments, and GitHub Integrations.
"""
import enum
from sqlalchemy import Enum, ForeignKey, JSON, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin


class ProjectStatus(str, enum.Enum):
    DRAFT = "draft"
    BUILDING = "building"
    READY = "ready"
    ERROR = "error"


class DeploymentTarget(str, enum.Enum):
    VERCEL = "vercel"
    NETLIFY = "netlify"
    RAILWAY = "railway"
    RENDER = "render"
    DOCKER = "docker"
    KUBERNETES = "kubernetes"


class DeploymentStatus(str, enum.Enum):
    PENDING = "pending"
    BUILDING = "building"
    DEPLOYED = "deployed"
    FAILED = "failed"


class Project(Base, TimestampMixin):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    template: Mapped[str] = mapped_column(String(100), default="custom", nullable=False)
    framework: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(Enum(ProjectStatus), default=ProjectStatus.READY, nullable=False)
    
    # Storage settings & metadata
    root_dir: Mapped[str | None] = mapped_column(String(512), nullable=True)
    zip_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    metadata_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Relationships
    files = relationship("ProjectFile", back_populates="project", cascade="all, delete-orphan", lazy="selectin")
    deployments = relationship("Deployment", back_populates="project", cascade="all, delete-orphan", lazy="selectin")

    def __repr__(self) -> str:
        return f"<Project id={self.id} title='{self.title}' template='{self.template}'>"


class ProjectFile(Base, TimestampMixin):
    __tablename__ = "project_files"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    path: Mapped[str] = mapped_column(String(512), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    language: Mapped[str] = mapped_column(String(50), default="text", nullable=False)

    project = relationship("Project", back_populates="files")

    def __repr__(self) -> str:
        return f"<ProjectFile id={self.id} path='{self.path}'>"


class Deployment(Base, TimestampMixin):
    __tablename__ = "deployments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    target: Mapped[DeploymentTarget] = mapped_column(Enum(DeploymentTarget), nullable=False)
    status: Mapped[DeploymentStatus] = mapped_column(Enum(DeploymentStatus), default=DeploymentStatus.PENDING, nullable=False)
    url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    logs: Mapped[str | None] = mapped_column(Text, nullable=True)

    project = relationship("Project", back_populates="deployments")


class GitHubIntegration(Base, TimestampMixin):
    __tablename__ = "github_integrations"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    access_token: Mapped[str] = mapped_column(String(512), nullable=False)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
