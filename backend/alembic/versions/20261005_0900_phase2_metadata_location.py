"""Persist reverse-geocoded addresses and time provenance.

Revision ID: d18f77a40b6c
Revises: c4f05a18b907
Create Date: 2026-10-05 09:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


revision = "d18f77a40b6c"
down_revision = "c4f05a18b907"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("image_metadata") as batch_op:
        batch_op.add_column(sa.Column("address_country", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("address_province", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("address_city", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("address_district", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("address_road", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("address_formatted", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("offset_time_original", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("offset_time_digitized", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("offset_time", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("file_upload_timestamp", sa.DateTime(timezone=True), nullable=True))
        for column in ("datetime_original", "datetime_digitized", "create_date", "modify_date"):
            batch_op.alter_column(
                column,
                existing_type=sa.DateTime(),
                type_=sa.DateTime(timezone=True),
                postgresql_using=f"{column} AT TIME ZONE 'UTC'",
            )


def downgrade() -> None:
    with op.batch_alter_table("image_metadata") as batch_op:
        for column in ("datetime_original", "datetime_digitized", "create_date", "modify_date"):
            batch_op.alter_column(
                column,
                existing_type=sa.DateTime(timezone=True),
                type_=sa.DateTime(),
                postgresql_using=f"{column} AT TIME ZONE 'UTC'",
            )
        batch_op.drop_column("file_upload_timestamp")
        batch_op.drop_column("offset_time")
        batch_op.drop_column("offset_time_digitized")
        batch_op.drop_column("offset_time_original")
        batch_op.drop_column("address_formatted")
        batch_op.drop_column("address_road")
        batch_op.drop_column("address_district")
        batch_op.drop_column("address_city")
        batch_op.drop_column("address_province")
        batch_op.drop_column("address_country")