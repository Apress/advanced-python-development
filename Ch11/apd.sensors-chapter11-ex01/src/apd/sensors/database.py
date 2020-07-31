from __future__ import annotations

import datetime
import typing as t

import sqlalchemy
from sqlalchemy.schema import Table
from sqlalchemy.orm.session import Session

from apd.sensors.base import Sensor


metadata = sqlalchemy.MetaData()

sensor_values = Table(
    "recorded_values",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("sensor_name", sqlalchemy.String, index=True),
    sqlalchemy.Column("collected_at", sqlalchemy.TIMESTAMP, index=True),
    sqlalchemy.Column("data", sqlalchemy.JSON),
)


def store_sensor_data(sensor: Sensor[t.Any], data: t.Any, db_session: Session) -> None:
    now = datetime.datetime.now()
    record = sensor_values.insert().values(
        sensor_name=sensor.name, data=sensor.to_json_compatible(data), collected_at=now
    )
    db_session.execute(record)
