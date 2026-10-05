"""Persist derived metadata and field provenance separately from raw EXIF.

Revision ID: c4f05a18b907
Revises: 7a9d13c2f601
Create Date: 2026-09-30 10:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "c4f05a18b907"
down_revision = "7a9d13c2f601"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("image_metadata") as batch_op:
        batch_op.add_column(sa.Column("derived_metadata", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("field_sources", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("image_metadata") as batch_op:
        batch_op.drop_column("field_sources")
        batch_op.drop_column("derived_metadata")