"""Create sensor_values table

Revision ID: 6d2eacd5da3f
Revises: 
Create Date: 2019-09-29 13:43:21.242706

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "6d2eacd5da3f"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "sensor_values",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("sensor_name", sa.String(), nullable=True),
        sa.Column("collected_at", postgresql.TIMESTAMP(), nullable=True),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("sensor_values")
