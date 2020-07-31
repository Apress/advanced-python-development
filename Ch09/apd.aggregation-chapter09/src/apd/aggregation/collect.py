import asyncio
from contextvars import ContextVar
import datetime
import typing as t
import uuid

import aiohttp
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session

from .database import DataPoint, datapoint_table, Deployment, deployment_table

http_session_var: ContextVar[aiohttp.ClientSession] = ContextVar("http_session")


async def get_deployment_id(server):
    http = http_session_var.get()
    if not server.endswith("/"):
        server += "/"
    url = server + "v/2.1/deployment_id"
    async with http.get(url) as request:
        if request.status != 200:
            raise ValueError(f"Error loading deployment id from {server}")
        result = await request.json()
        return uuid.UUID(result["deployment_id"])


async def get_data_points(server: str, api_key: t.Optional[str],) -> t.List[DataPoint]:
    if not server.endswith("/"):
        server += "/"
    url = server + "v/2.1/sensors/"
    headers = {}
    if api_key:
        headers["X-API-KEY"] = api_key
    http = http_session_var.get()

    # Get the deployment ID in parallel to the sensor data
    deployment_id = asyncio.create_task(get_deployment_id(server))

    async with http.get(url, headers=headers) as request:
        result = await request.json()
        ok = request.status == 200
    now = datetime.datetime.now()
    if ok:
        points = []
        for value in result["sensors"]:
            points.append(
                DataPoint(
                    sensor_name=value["id"],
                    collected_at=now,
                    data=value["value"],
                    deployment_id=await deployment_id,
                )
            )
        return points
    else:
        raise ValueError(
            f"Error loading data from {server}: " + result.get("error", "Unknown")
        )


def handle_result(result: t.List[DataPoint], session: Session) -> t.List[DataPoint]:
    for point in result:
        insert = datapoint_table.insert().values(**point._asdict())
        sql_result = session.execute(insert)
        point.id = sql_result.inserted_primary_key[0]
    return result


async def add_data_from_sensors(
    session: Session, servers: t.Iterable[Deployment]
) -> t.List[DataPoint]:
    tasks: t.List[t.Awaitable[t.List[DataPoint]]] = []
    points: t.List[DataPoint] = []
    async with aiohttp.ClientSession() as http:
        http_session_var.set(http)
        tasks = [get_data_points(server.uri, server.api_key) for server in servers]
        for results in await asyncio.gather(*tasks):
            points += results
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, handle_result, points, session)
    return points


def standalone(
    db_uri: str, servers: t.Tuple[str], api_key: t.Optional[str], echo: bool = False
) -> None:
    engine = create_engine(db_uri, echo=echo)
    sm = sessionmaker(engine)
    Session = sm()
    deployments: t.Iterable[Deployment]
    if servers:
        deployments = tuple(
            Deployment(id=None, name=None, colour=None, api_key=api_key, uri=server)
            for server in servers
        )
    else:
        deployment_data = Session.query(deployment_table).all()
        deployments = tuple(
            Deployment.from_sql_result(deployment) for deployment in deployment_data
        )
    asyncio.run(add_data_from_sensors(Session, deployments))
    Session.commit()


if __name__ == "__main__":
    standalone(
        db_uri="postgresql+psycopg2://apd@localhost/apd",
        servers=("http://pvoutput:8080/",),
        api_key="h3hdfjksfhwkjehnwekj",
    )
