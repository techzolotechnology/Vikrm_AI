"""add agents table and conversations.agent_id

Revision ID: 202607142000
Revises: 202607141500
Create Date: 2026-07-14 20:00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "202607142000"
down_revision: Union[str, None] = "202607141500"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "agents",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("avatar_color", sa.String(20), nullable=False, server_default="#7C3AED"),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("goal", sa.Text(), nullable=True),
        sa.Column("personality", sa.Text(), nullable=True),
        sa.Column("provider", sa.String(50), nullable=False, server_default="ollama"),
        sa.Column("model", sa.String(100), nullable=False, server_default="llama3.2"),
        sa.Column("temperature", sa.Float(), nullable=False, server_default="0.7"),
        sa.Column("max_tokens", sa.Integer(), nullable=False, server_default="2048"),
        sa.Column(
            "status",
            sa.Enum("ACTIVE", "ARCHIVED", name="agentstatus"),
            nullable=False,
            server_default="ACTIVE",
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
    )
    op.create_index("ix_agents_user_id", "agents", ["user_id"])

    op.add_column("conversations", sa.Column("agent_id", sa.Integer(), nullable=True))
    with op.batch_alter_table("conversations") as batch_op:
        batch_op.create_foreign_key(
            "fk_conversations_agent_id",
            "agents",
            ["agent_id"],
            ["id"],
            ondelete="SET NULL",
        )
    op.create_index("ix_conversations_agent_id", "conversations", ["agent_id"])


def downgrade() -> None:
    op.drop_index("ix_conversations_agent_id", table_name="conversations")
    op.drop_constraint("fk_conversations_agent_id", "conversations", type_="foreignkey")
    op.drop_column("conversations", "agent_id")

    op.drop_index("ix_agents_user_id", table_name="agents")
    op.drop_table("agents")
