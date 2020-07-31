import typing as t

import flask

from apd.sensors import cli
from apd.sensors.exceptions import DataCollectionError
from .base import require_api_key

version = flask.Blueprint(__name__, __name__)


@version.route("/sensors/")
@version.route("/sensors/<sensor_id>")
@require_api_key
def sensor_values(sensor_id=None) -> t.Tuple[t.Dict[str, t.Any], int, t.Dict[str, str]]:
    headers = {"Content-Security-Policy": "default-src 'none'"}
    sensors = []
    for sensor in cli.get_sensors():
        if sensor_id and sensor_id != sensor.name:
            continue
        try:
            try:
                value = sensor.value()
            except DataCollectionError:
                human_readable = "Unknown"
                json_value = None
            else:
                json_value = sensor.to_json_compatible(value)
                human_readable = sensor.format(value)
            sensor_data = {
                "id": sensor.name,
                "title": sensor.title,
                "value": json_value,
                "human_readable": human_readable,
            }
            sensors.append(sensor_data)
        except NotImplementedError:
            pass
    data = {"sensors": sensors}
    return data, 200, headers
