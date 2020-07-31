from __future__ import annotations

import datetime
import functools
import threading
import typing as t
import queue

import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session

from .database import DataPoint


T_Val = t.TypeVar("T_Val")


class return_via_queue(t.Generic[T_Val]):
    def __init__(self, return_queue: queue.Queue[T_Val]) -> None:
        self.return_queue = return_queue

    def __call__(self, func: t.Callable[..., T_Val]) -> t.Callable[..., T_Val]:
        @functools.wraps(func)
        def inner(*args, **kwargs):
            value = func(*args, **kwargs)
            self.return_queue.put(value)
            return

        return inner


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
    dps: t.List[DataPoint] = []
    if result.ok:
        for value in result.json()["sensors"]:
            dps.append(
                DataPoint(
                    sensor_name=value["id"], collected_at=now, data=value["value"]
                )
            )
    else:
        raise ValueError(
            f"Error loading data from {server}: "
            + result.json().get("error", "Unknown")
        )
    return dps


def add_data_from_sensors(
    session: Session, servers: t.Tuple[str], api_key: t.Optional[str]
) -> t.Iterable[DataPoint]:
    points: t.List[DataPoint] = []
    q: queue.Queue[t.List[DataPoint]] = queue.Queue()
    wrap = return_via_queue(q)
    threads = [
        threading.Thread(target=wrap(get_data_points), args=(server, api_key))
        for server in servers
    ]
    for thread in threads:
        # Start all threads
        thread.start()
    for thread in threads:
        # Wait for all threads to finish
        thread.join()
    while not q.empty():
        # So long as there's a return value in the queue, process one thread's results
        found = q.get_nowait()
        for point in found:
            session.add(point)
            points.append(point)
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
