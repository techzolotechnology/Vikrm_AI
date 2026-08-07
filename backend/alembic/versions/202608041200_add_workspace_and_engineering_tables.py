"""
Add workspace, projects, project_files, deployments, and github_integrations tables.

Revision ID: 202608041200
Revises: 202607261000
Create Date: 2026-08-04 12:00:00
"""
import alembic.op as op
import sqlalchemy as sa

revision = "202608041200"
down_revision = "202607261000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Projects table
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("template", sa.String(length=100), server_default="custom", nullable=False),
        sa.Column("framework", sa.String(length=100), nullable=True),
        sa.Column("status", sa.Enum("DRAFT", "BUILDING", "READY", "ERROR", name="projectstatus"), server_default="READY", nullable=False),
        sa.Column("root_dir", sa.String(length=512), nullable=True),
        sa.Column("zip_path", sa.String(length=512), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # 2. Project files table
    op.create_table(
        "project_files",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("path", sa.String(length=512), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("language", sa.String(length=50), server_default="text", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # 3. Deployments table
    op.create_table(
        "deployments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("project_id", sa.Integer(), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("target", sa.Enum("VERCEL", "NETLIFY", "RAILWAY", "RENDER", "DOCKER", "KUBERNETES", name="deploymenttarget"), nullable=False),
        sa.Column("status", sa.Enum("PENDING", "BUILDING", "DEPLOYED", "FAILED", name="deploymentstatus"), server_default="PENDING", nullable=False),
        sa.Column("url", sa.String(length=512), nullable=True),
        sa.Column("logs", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # 4. GitHub integrations table
    op.create_table(
        "github_integrations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("access_token", sa.String(length=512), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("avatar_url", sa.String(length=512), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("github_integrations")
    op.drop_table("deployments")
    op.drop_table("project_files")
    op.drop_table("projects")
