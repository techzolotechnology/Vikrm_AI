"""Update server_default for model column in conversations and agents tables to qwen3:8b

Revision ID: 202608081200
Revises: 202608041200
Create Date: 2026-08-08 12:00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "202608081200"
down_revision: Union[str, None] = "202608041200"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("conversations") as batch_op:
        batch_op.alter_column("model", server_default="qwen3:8b")
    with op.batch_alter_table("agents") as batch_op:
        batch_op.alter_column("model", server_default="qwen3:8b")


def downgrade() -> None:
    with op.batch_alter_table("conversations") as batch_op:
        batch_op.alter_column("model", server_default="llama3.2")
    with op.batch_alter_table("agents") as batch_op:
        batch_op.alter_column("model", server_default="llama3.2")
