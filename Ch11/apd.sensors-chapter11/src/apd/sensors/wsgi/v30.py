import datetime
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
    errors = []
    for sensor in cli.get_sensors():
        now = datetime.datetime.now()
        if sensor_id and sensor_id != sensor.name:
            continue
        try:
            try:
                value = sensor.value()
            except DataCollectionError as err:
                error = {
                    "id": sensor.name,
                    "title": sensor.title,
                    "collected_at": now.isoformat(),
                    "error": str(err),
                }
                errors.append(error)
                continue
            sensor_data = {
                "id": sensor.name,
                "title": sensor.title,
                "value": sensor.to_json_compatible(value),
                "human_readable": sensor.format(value),
                "collected_at": now.isoformat(),
            }
            sensors.append(sensor_data)
        except NotImplementedError:
            pass
    data = {"sensors": sensors, "errors": errors}
    return data, 200, headers


@version.route("/historical")
@version.route("/historical/<start>")
@version.route("/historical/<start>/<end>")
@require_api_key
def historical_values(
    start: str = None, end: str = None
) -> t.Tuple[t.Dict[str, t.Any], int, t.Dict[str, str]]:
    try:
        import dateutil.parser
        from apd.sensors.database import sensor_values
        from apd.sensors.wsgi import db
    except ImportError:
        return {"error": "Historical data support is not installed"}, 501, {}

    db_session = db.session
    headers = {"Content-Security-Policy": "default-src 'none'"}

    query = db_session.query(sensor_values)
    if start:
        query = query.filter(
            sensor_values.c.collected_at >= dateutil.parser.parse(start)
        )
    if end:
        query = query.filter(sensor_values.c.collected_at <= dateutil.parser.parse(end))

    known_sensors = {sensor.name: sensor for sensor in cli.get_sensors()}
    sensors = []
    for data in query:
        if data.sensor_name not in known_sensors:
            continue
        sensor = known_sensors[data.sensor_name]
        sensor_data = {
            "id": sensor.name,
            "title": sensor.title,
            "value": data.data,
            "human_readable": sensor.format(sensor.from_json_compatible(data.data)),
            "collected_at": data.collected_at.isoformat(),
        }
        sensors.append(sensor_data)
    data = {"sensors": sensors}
    try:
        return data, 200, headers
    finally:
        db_session.close()


@version.route("/deployment_id")
def deployment_id() -> t.Tuple[t.Dict[str, t.Any], int, t.Dict[str, str]]:
    headers = {"Content-Security-Policy": "default-src 'none'"}
    data = {"deployment_id": flask.current_app.config["APD_SENSORS_DEPLOYMENT_ID"]}
    return data, 200, headers
