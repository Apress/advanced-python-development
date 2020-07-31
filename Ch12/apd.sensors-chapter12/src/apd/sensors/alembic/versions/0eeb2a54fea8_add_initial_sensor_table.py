"""Add initial sensor table

Revision ID: 0eeb2a54fea8
Revises: base
Create Date: 2020-01-16 17:43:37.298379

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0eeb2a54fea8"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "recorded_values",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sensor_name", sa.String(), nullable=True),
        sa.Column("collected_at", sa.TIMESTAMP(), nullable=True),
        sa.Column("data", sa.JSON(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_recorded_values_collected_at"),
        "recorded_values",
        ["collected_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_recorded_values_sensor_name"),
        "recorded_values",
        ["sensor_name"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix_recorded_values_sensor_name"), table_name="recorded_values")
    op.drop_index(op.f("ix_recorded_values_collected_at"), table_name="recorded_values")
    op.drop_table("recorded_values")
