import json
import typing as t

import flask

from apd.sensors.cli import get_sensors
from .base import require_api_key

version = flask.Blueprint(__name__, __name__)


@version.route("/sensors/")
@require_api_key
def sensor_values() -> t.Tuple[t.Dict[str, t.Any], int, t.Dict[str, str]]:
    headers = {"Content-Security-Policy": "default-src 'none'"}
    data = {}
    for sensor in get_sensors():
        value = sensor.value()
        try:
            json.dumps(value)
        except TypeError:
            # This value isn't JSON serializable, skip it
            continue
        else:
            data[sensor.title] = sensor.value()
    return data, 200, headers
