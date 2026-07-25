"""add tool_executions table

Revision ID: 202607160900
Revises: 202607152000
Create Date: 2026-07-16 09:00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "202607160900"
down_revision: Union[str, None] = "202607152000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tool_executions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("tool_name", sa.String(100), nullable=False),
        sa.Column("input_text", sa.Text(), nullable=False),
        sa.Column("output_text", sa.Text(), nullable=True),
        sa.Column(
            "status", sa.Enum("SUCCESS", "FAILED", name="toolexecutionstatus"), nullable=False
        ),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_tool_executions_user_id", "tool_executions", ["user_id"])
    op.create_index("ix_tool_executions_tool_name", "tool_executions", ["tool_name"])


def downgrade() -> None:
    op.drop_index("ix_tool_executions_tool_name", table_name="tool_executions")
    op.drop_index("ix_tool_executions_user_id", table_name="tool_executions")
    op.drop_table("tool_executions")
