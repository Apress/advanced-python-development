from dataclasses import dataclass, field
import datetime
import typing as t

import sqlalchemy
from sqlalchemy.dialects.postgresql import JSONB, TIMESTAMP
from sqlalchemy.schema import Table


metadata = sqlalchemy.MetaData()

datapoint_table = Table(
    "sensor_values",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("sensor_name", sqlalchemy.String),
    sqlalchemy.Column("collected_at", TIMESTAMP),
    sqlalchemy.Column("data", JSONB),
)

@dataclass
class DataPoint:
    sensor_name: str
    data: t.Dict[str, t.Any]
    id: int = None
    collected_at: datetime.datetime = field(default_factory=datetime.datetime.now)

