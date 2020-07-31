import json
import typing as t

from apd.sensors.cli import get_sensors

if t.TYPE_CHECKING:
    from wsgiref.types import StartResponse
else:
    StartResponse = t.Callable


def sensor_values(
    environ: t.Dict[str, str], start_response: StartResponse
) -> t.List[bytes]:
    headers = [
        ("Content-type", "application/json; charset=utf-8"),
        ("Content-Security-Policy", "default-src 'none';"),
    ]
    start_response("200 OK", headers)
    data = {}
    for sensor in get_sensors():
        data[sensor.title] = sensor.value()
    encoded = json.dumps(data).encode("utf-8")
    return [encoded]


if __name__ == "__main__":
    import wsgiref.simple_server

    with wsgiref.simple_server.make_server("", 8000, sensor_values) as server:
        server.serve_forever()
