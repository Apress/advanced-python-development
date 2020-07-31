import asyncio
import datetime
import typing as t
from uuid import UUID

from apd.aggregation.database import DataPoint


async def get_data(
    sensor_name: t.Optional[str] = None,
    deployment_id: t.Optional[UUID] = None,
    collected_before: t.Optional[datetime.datetime] = None,
    collected_after: t.Optional[datetime.datetime] = None,
) -> t.AsyncIterator[DataPoint]:
    db_session = db_session_var.get()
    loop = asyncio.get_running_loop()
    query = db_session.query(datapoint_table)
    if sensor_name:
        query = query.filter(datapoint_table.c.sensor_name == sensor_name)
    if deployment_id:
        query = query.filter(datapoint_table.c.deployment_id == deployment_id)
    if collected_before:
        query = query.filter(datapoint_table.c.collected_at < collected_before)
    if collected_after:
        query = query.filter(datapoint_table.c.collected_at > collected_after)
    query = query.order_by(
        datapoint_table.c.deployment_id,
        datapoint_table.c.sensor_name,
        datapoint_table.c.collected_at,
    )

    rows = await loop.run_in_executor(None, query.all)
    for row in rows:
        yield DataPoint.from_sql_result(row)

