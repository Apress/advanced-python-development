async def get_deployment_ids():
    db_session = db_session_var.get()
    loop = asyncio.get_running_loop()
    query = db_session.query(datapoint_table.c.deployment_id).distinct()
    return [row.deployment_id for row in await loop.run_in_executor(None, query.all)]

async def get_data(
    sensor_name: t.Optional[str] = None,
    deployment_id: t.Optional[UUID] = None,
) -> t.AsyncIterator[DataPoint]:
    db_session = db_session_var.get()
    loop = asyncio.get_running_loop()
    query = db_session.query(datapoint_table)
    if sensor_name:
        query = query.filter(datapoint_table.c.sensor_name == sensor_name)
    if deployment_id:
        query = query.filter(datapoint_table.c.deployment_id == deployment_id)
    query = query.order_by(
        datapoint_table.c.collected_at,
    )

