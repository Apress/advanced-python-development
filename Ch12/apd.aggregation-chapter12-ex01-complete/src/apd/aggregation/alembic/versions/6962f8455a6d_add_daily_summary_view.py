"""Add daily summary view

Revision ID: 6962f8455a6d
Revises: 4b2df8a6e1ce
Create Date: 2019-12-03 11:50:24.403402

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "6962f8455a6d"
down_revision = "4b2df8a6e1ce"
branch_labels = None
depends_on = None


def upgrade():
    create_view = """
    CREATE VIEW daily_summary AS
      SELECT
        datapoints.sensor_name AS sensor_name,
        datapoints.data AS data,
        count(datapoints.id) AS count
    FROM datapoints
    WHERE
        datapoints.collected_at >= CAST(CURRENT_DATE AS DATE)
        AND
        datapoints.collected_at < CAST(CURRENT_DATE AS DATE) + 1
    GROUP BY
        datapoints.sensor_name,
        datapoints.data;
    """
    op.execute(create_view)


def downgrade():
    op.execute("""DROP VIEW daily_summary""")
