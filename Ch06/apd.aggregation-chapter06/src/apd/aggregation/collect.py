import datetime
import typing as t
 
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session
 
from .database import DataPoint
 
 
def get_data_points(server: str, api_key: t.Optional[str]) -> t.Iterable[DataPoint]:
    if not server.endswith("/"):
        server += "/"
    url = server + "v/2.0/sensors/"
    headers = {}
    if api_key:
        headers["X-API-KEY"] = api_key
    try:
        result = requests.get(url, headers=headers)
    except requests.ConnectionError as e:
        raise ValueError(f"Error connecting to {server}")
    now = datetime.datetime.now()
    if result.ok:
        for value in result.json()["sensors"]:
            yield DataPoint(
                sensor_name=value["id"], collected_at=now, data=value["value"]
            )
    else:
        raise ValueError(
            f"Error loading data from {server}: "
            + result.json().get("error", "Unknown")
        )
 
 
def add_data_from_sensors(
    session: Session, servers: t.Tuple[str], api_key: t.Optional[str]
) -> t.Iterable[DataPoint]:
    points: t.List[DataPoint] = []
    for server in servers:
        for point in get_data_points(server, api_key):
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
    