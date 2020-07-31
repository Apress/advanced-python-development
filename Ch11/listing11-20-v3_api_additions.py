@version.route("/historical")
@version.route("/historical/<start>")
@version.route("/historical/<start>/<end>")
@require_api_key
def historical_values(
    start: str = None, end: str = None
) -> t.Tuple[t.Dict[str, t.Any], int, t.Dict[str, str]]:
    try:
        import dateutil.parser
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker
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
        query = query.filter(
            sensor_values.c.collected_at <= dateutil.parser.parse(end)
        )

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
    return data, 200, headers

