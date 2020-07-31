import typing as t

import flask

from apd.sensors import cli
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


@version.route("/deployment_id")
def deployment_id() -> t.Tuple[t.Dict[str, t.Any], int, t.Dict[str, str]]:
    headers = {"Content-Security-Policy": "default-src 'none'"}
    data = {"deployment_id": flask.current_app.config["APD_SENSORS_DEPLOYMENT_ID"]}
    return data, 200, headers
