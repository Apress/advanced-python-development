import datetime
import io
import json
import select
import socket
import typing as t
import urllib.parse

import h11
import requests
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session

from .database import DataPoint


def get_http(uri: str, headers: t.Dict[str, str]) -> socket.socket:
    """Given a URI and a set of headers, make a HTTP request and return the
    underlying socket. If there were a production-quality implementation of
    nonblocking HTTP this function would be replaced with the relevant one
    from that library."""
    parsed = urllib.parse.urlparse(uri)
    sock = socket.socket()
    if parsed.port:
        port = parsed.port
    else:
        port = 80
    headers["Host"] = parsed.netloc
    sock.connect((parsed.hostname, port))
    sock.setblocking(False)

    connection = h11.Connection(h11.CLIENT)
    request = h11.Request(method="GET", target=parsed.path, headers=headers.items())

    sock.send(connection.send(request))
    sock.send(connection.send(h11.EndOfMessage()))
    return sock


def read_from_socket(sock: socket.socket) -> str:
    """ If there were a production-quality implementation of nonblocking HTTP
    this function would be replaced with the relevant one to get the body of
    the response if it was a success or error otherwise. """
    data = sock.recv(2048)
    connection = h11.Connection(h11.CLIENT)
    connection.receive_data(data)

    response = connection.next_event()
    headers = dict(response.headers)
    body = connection.next_event()
    eom = connection.next_event()

    try:
        if (
            response.status_code == 200
            and headers.get(b"content-type", None) == b"application/json"
        ):
            return body.data.decode("utf-8")
        else:
            raise ValueError("Bad response")
    finally:
        sock.close()


def connect_to_server(server: str, api_key: t.Optional[str]) -> socket.socket:
    if not server.endswith("/"):
        server += "/"
    url = server + "v/2.0/sensors/"
    headers = {}
    if api_key:
        headers["X-API-KEY"] = api_key

    return get_http(url, headers=headers)


def prepare_datapoints_from_response(response: str) -> t.Iterator[DataPoint]:
    now = datetime.datetime.now()
    json_result = json.loads(response)
    if "sensors" in json_result:
        for value in json_result["sensors"]:
            yield DataPoint(
                sensor_name=value["id"], collected_at=now, data=value["value"]
            )
    else:
        raise ValueError(
            f"Error loading data from stream: " + json_result.get("error", "Unknown")
        )


def add_data_from_sensors(
    session: Session, servers: t.Tuple[str], api_key: t.Optional[str]
) -> t.Iterable[DataPoint]:
    points: t.List[DataPoint] = []
    sockets = [connect_to_server(server, api_key) for server in servers]
    while sockets:
        readable, writable, exceptional = select.select(sockets, [], [])
        for request in readable:
            # In a production quality implementation there would be
            # handling here for responses that have only partially been
            # received.
            value = read_from_socket(request)
            for point in prepare_datapoints_from_response(value):
                session.add(point)
                points.append(point)
            sockets.remove(request)
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
