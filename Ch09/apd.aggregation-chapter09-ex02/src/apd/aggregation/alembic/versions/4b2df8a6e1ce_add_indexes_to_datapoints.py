"""Add indexes to datapoints

Revision ID: 4b2df8a6e1ce
Revises: 6d2eacd5da3f
Create Date: 2019-12-02 16:07:41.123116

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "4b2df8a6e1ce"
down_revision = "6d2eacd5da3f"
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(
        op.f("ix_datapoints_collected_at"),
        "datapoints",
        ["collected_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_datapoints_sensor_name"), "datapoints", ["sensor_name"], unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix_datapoints_sensor_name"), table_name="datapoints")
    op.drop_index(op.f("ix_datapoints_collected_at"), table_name="datapoints")
