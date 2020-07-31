"""Add deployment table

Revision ID: d8cdc709086b
Revises: d8d4cf6a178f
Create Date: 2019-12-17 16:28:58.585616

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "d8cdc709086b"
down_revision = "d8d4cf6a178f"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "deployments",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("uri", sa.String(), nullable=True),
        sa.Column("name", sa.String(), nullable=True),
        sa.Column("colour", sa.String(), nullable=True),
        sa.Column("api_key", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("deployments")
