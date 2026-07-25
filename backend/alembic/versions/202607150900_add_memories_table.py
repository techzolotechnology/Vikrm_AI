"""add memories table

Revision ID: 202607150900
Revises: 202607142000
Create Date: 2026-07-15 09:00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "202607150900"
down_revision: Union[str, None] = "202607142000"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "memories",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("agent_id", sa.Integer(), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "memory_type",
            sa.Enum("FACT", "PREFERENCE", "CONTEXT", name="memorytype"),
            nullable=False,
            server_default="FACT",
        ),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["agent_id"], ["agents.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_memories_user_id", "memories", ["user_id"])
    op.create_index("ix_memories_agent_id", "memories", ["agent_id"])


def downgrade() -> None:
    op.drop_index("ix_memories_agent_id", table_name="memories")
    op.drop_index("ix_memories_user_id", table_name="memories")
    op.drop_table("memories")
