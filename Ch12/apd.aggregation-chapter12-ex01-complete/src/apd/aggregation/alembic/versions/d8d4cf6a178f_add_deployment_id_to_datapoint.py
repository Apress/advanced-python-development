"""Add deployment id to DataPoint

Revision ID: d8d4cf6a178f
Revises: 6962f8455a6d
Create Date: 2019-12-03 20:58:11.285509

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "d8d4cf6a178f"
down_revision = "6962f8455a6d"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "datapoints",
        sa.Column("deployment_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        op.f("ix_datapoints_deployment_id"),
        "datapoints",
        ["deployment_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix_datapoints_deployment_id"), table_name="datapoints")
    op.drop_column("datapoints", "deployment_id")
