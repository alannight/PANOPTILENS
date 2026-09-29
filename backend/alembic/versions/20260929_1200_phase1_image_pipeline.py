"""Add validated image properties and extraction statuses.

Revision ID: 7a9d13c2f601
Revises: 45c73ceeec75
Create Date: 2026-09-29 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "7a9d13c2f601"
down_revision = "45c73ceeec75"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("images") as batch_op:
        batch_op.alter_column("owner_id", existing_type=sa.String(), nullable=True)
        batch_op.add_column(sa.Column("image_format", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("image_mode", sa.String(), nullable=True))

    with op.batch_alter_table("image_metadata") as batch_op:
        batch_op.add_column(sa.Column("datetime_digitized", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("gps_direction", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("metadata_status", sa.String(), nullable=False, server_default="UNKNOWN"))
        batch_op.add_column(sa.Column("gps_status", sa.String(), nullable=False, server_default="UNKNOWN"))
        batch_op.alter_column("metadata_status", server_default=None)
        batch_op.alter_column("gps_status", server_default=None)

    with op.batch_alter_table("forensic_analyses") as batch_op:
        batch_op.add_column(sa.Column("image_decoded", sa.Boolean(), nullable=True))

    op.execute("UPDATE forensic_analyses SET metadata_consistent = NULL")


def downgrade() -> None:
    with op.batch_alter_table("forensic_analyses") as batch_op:
        batch_op.drop_column("image_decoded")

    with op.batch_alter_table("image_metadata") as batch_op:
        batch_op.drop_column("gps_status")
        batch_op.drop_column("metadata_status")
        batch_op.drop_column("gps_direction")
        batch_op.drop_column("datetime_digitized")

    with op.batch_alter_table("images") as batch_op:
        batch_op.drop_column("image_mode")
        batch_op.drop_column("image_format")