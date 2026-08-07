"""
Add folders, attachments tables, and enhanced chat columns.

Revision ID: 202607261000
Revises: 202607241400
Create Date: 2026-07-26 10:00:00
"""
import alembic.op as op
import sqlalchemy as sa

revision = "202607261000"
down_revision = "202607241400"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create folders table
    op.create_table(
        "folders",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("color", sa.String(length=30), server_default="#7C3AED", nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )

    # 2. Add columns to conversations table
    with op.batch_alter_table("conversations") as batch_op:
        batch_op.add_column(sa.Column("folder_id", sa.Integer(), sa.ForeignKey("folders.id", ondelete="SET NULL", name="fk_conversations_folder_id"), nullable=True))
        batch_op.add_column(sa.Column("is_pinned", sa.Boolean(), server_default=sa.text("0"), nullable=False))
        batch_op.add_column(sa.Column("is_archived", sa.Boolean(), server_default=sa.text("0"), nullable=False))
        batch_op.add_column(sa.Column("summary", sa.Text(), nullable=True))

    # 3. Add columns to messages table
    op.add_column("messages", sa.Column("is_bookmarked", sa.Boolean(), server_default=sa.text("0"), nullable=False))
    op.add_column("messages", sa.Column("edited_at", sa.DateTime(), nullable=True))

    # 4. Create attachments table
    op.create_table(
        "attachments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("conversation_id", sa.Integer(), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("message_id", sa.Integer(), sa.ForeignKey("messages.id", ondelete="SET NULL"), nullable=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_type", sa.String(length=100), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("extracted_text", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("attachments")
    op.drop_column("messages", "edited_at")
    op.drop_column("messages", "is_bookmarked")
    op.drop_column("conversations", "summary")
    op.drop_column("conversations", "is_archived")
    op.drop_column("conversations", "is_pinned")
    op.drop_column("conversations", "folder_id")
    op.drop_table("folders")
