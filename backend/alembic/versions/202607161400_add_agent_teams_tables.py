"""add agent_teams and agent_team_runs tables

Revision ID: 202607161400
Revises: 202607160900
Create Date: 2026-07-16 14:00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "202607161400"
down_revision: Union[str, None] = "202607160900"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agent_teams",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("manager_agent_id", sa.Integer(), nullable=False),
        sa.Column("member_agent_ids", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["manager_agent_id"], ["agents.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_agent_teams_user_id", "agent_teams", ["user_id"])

    op.create_table(
        "agent_team_runs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("task", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("RUNNING", "COMPLETED", "FAILED", name="teamrunstatus"),
            nullable=False,
            server_default="RUNNING",
        ),
        sa.Column("plan", sa.JSON(), nullable=False),
        sa.Column("steps", sa.JSON(), nullable=False),
        sa.Column("final_output", sa.Text(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["team_id"], ["agent_teams.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_agent_team_runs_team_id", "agent_team_runs", ["team_id"])


def downgrade() -> None:
    op.drop_index("ix_agent_team_runs_team_id", table_name="agent_team_runs")
    op.drop_table("agent_team_runs")
    op.drop_index("ix_agent_teams_user_id", table_name="agent_teams")
    op.drop_table("agent_teams")
