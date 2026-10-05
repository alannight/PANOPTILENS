"""Add image lifecycle state, deletion audit, and analyst annotations.

Revision ID: 06d41c79a3bb
Revises: d18f77a40b6c
Create Date: 2026-10-05 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "06d41c79a3bb"
down_revision = "d18f77a40b6c"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("images") as batch_op:
        batch_op.add_column(sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.false()))
        batch_op.add_column(sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("tags", sa.Text(), nullable=False, server_default=sa.text("'[]'")))
        batch_op.add_column(sa.Column("analyst_notes", sa.Text(), nullable=True))

    with op.batch_alter_table("cases") as batch_op:
        batch_op.alter_column(
            "owner_id",
            existing_type=sa.String(),
            nullable=True,
        )

    op.create_table(
        "image_deletion_audits",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("image_id", sa.String(), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("storage_key", sa.String(), nullable=True),
        sa.Column("sha256", sa.String(length=64), nullable=True),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_image_deletion_audits_image_id", "image_deletion_audits", ["image_id"])


def downgrade() -> None:
    op.drop_index("ix_image_deletion_audits_image_id", table_name="image_deletion_audits")
    op.drop_table("image_deletion_audits")

    with op.batch_alter_table("cases") as batch_op:
        batch_op.alter_column(
            "owner_id",
            existing_type=sa.String(),
            nullable=False,
        )

    with op.batch_alter_table("images") as batch_op:
        batch_op.drop_column("analyst_notes")
        batch_op.drop_column("tags")
        batch_op.drop_column("deleted_at")
        batch_op.drop_column("is_deleted")