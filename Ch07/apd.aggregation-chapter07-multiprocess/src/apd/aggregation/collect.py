import datetime
from concurrent.futures import ThreadPoolExecutor, Future
import typing as t

import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session

from .database import DataPoint


def get_data_points(server: str, api_key: t.Optional[str]) -> t.List[DataPoint]:
    if not server.endswith("/"):
        server += "/"
    url = server + "v/2.0/sensors/"
    headers = {}
    if api_key:
        headers["X-API-KEY"] = api_key
    try:
        result = requests.get(url, headers=headers)
    except requests.ConnectionError:
        raise ValueError(f"Error connecting to {server}")
    now = datetime.datetime.now()
    if result.ok:
        points = []
        for value in result.json()["sensors"]:
            points.append(
                DataPoint(
                    sensor_name=value["id"], collected_at=now, data=value["value"]
                )
            )
        return points
    else:
        raise ValueError(
            f"Error loading data from {server}: "
            + result.json().get("error", "Unknown")
        )


def handle_result(execution: Future, session: Session) -> t.List[DataPoint]:
    points: t.List[DataPoint] = []
    result = execution.result()
    for point in result:
        session.add(point)
        points.append(point)
    return points


def add_data_from_sensors(
    session: Session, servers: t.Tuple[str], api_key: t.Optional[str]
) -> t.List[DataPoint]:
    threads: t.List[Future] = []
    points: t.List[DataPoint] = []
    with ThreadPoolExecutor() as pool:
        for server in servers:
            points_future = pool.submit(get_data_points, server, api_key)
            threads.append(points_future)
    for thread in threads:
        points += handle_result(thread, session)
    return points


def standalone(
    db_uri: str, servers: t.Tuple[str], api_key: t.Optional[str], echo: bool = False
) -> None:
    engine = create_engine(db_uri, echo=echo)
    sm = sessionmaker(engine)
    Session = sm()
    add_data_from_sensors(Session, servers, api_key)
    Session.commit()


if __name__ == "__main__":
    standalone(
        db_uri="postgresql+psycopg2://apd@localhost/apd",
        servers=("http://pvoutput:8080/",),
        api_key="h3hdfjksfhwkjehnwekj",
    )
