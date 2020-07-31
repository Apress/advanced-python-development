import typing as t

import flask

from apd.sensors.cli import get_sensors
from .base import require_api_key

version = flask.Blueprint(__name__, __name__)


@version.route("/sensors/")
@version.route("/sensors/<sensor_id>")
@require_api_key
def sensor_values(sensor_id=None) -> t.Tuple[t.Dict[str, t.Any], int, t.Dict[str, str]]:
    headers = {"Content-Security-Policy": "default-src 'none'"}
    sensors = []
    for sensor in get_sensors():
        if sensor_id and sensor_id != sensor.name:
            continue
        try:
            value = sensor.value()
            sensor_data = {
                "id": sensor.name,
                "title": sensor.title,
                "value": sensor.to_json_compatible(value),
                "human_readable": sensor.format(value),
            }
            sensors.append(sensor_data)
        except NotImplementedError:
            pass
    data = {"sensors": sensors}
    return data, 200, headers
