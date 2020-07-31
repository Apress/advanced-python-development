from __future__ import annotations

from dataclasses import dataclass, field, asdict
import datetime
import typing as t
import uuid

import sqlalchemy
from sqlalchemy.dialects.postgresql import JSONB, DATE, TIMESTAMP, UUID
from sqlalchemy.ext.hybrid import ExprComparator, hybrid_property
from sqlalchemy.orm import sessionmaker
from sqlalchemy.schema import Table


metadata = sqlalchemy.MetaData()

datapoint_table = Table(
    "datapoints",
    metadata,
    sqlalchemy.Column("id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("sensor_name", sqlalchemy.String, index=True),
    sqlalchemy.Column("collected_at", TIMESTAMP, index=True),
    sqlalchemy.Column("deployment_id", UUID(as_uuid=True), index=True),
    sqlalchemy.Column("data", JSONB),
)

daily_summary_view = Table(
    "daily_summary",
    metadata,
    sqlalchemy.Column("sensor_name", sqlalchemy.String),
    sqlalchemy.Column("data", JSONB),
    sqlalchemy.Column("count", sqlalchemy.Integer),
    info={"is_view": True},
)


class DateEqualComparator(ExprComparator):
    def __init__(self, fallback_expression, raw_expression):
        # Do not try and find update expression from parent
        super().__init__(None, fallback_expression, None)
        self.raw_expression = raw_expression

    def __eq__(self, other):
        """ Returns True iff on the same day as other """
        other_date = sqlalchemy.cast(other, DATE)
        return sqlalchemy.and_(
            self.raw_expression >= other_date, self.raw_expression < other_date + 1,
        )

    def operate(self, op, *other, **kwargs):
        other = [sqlalchemy.cast(date, DATE) for date in other]
        return op(self.expression, *other, **kwargs)

    def reverse_operate(self, op, other, **kwargs):
        other = [sqlalchemy.cast(date, DATE) for date in other]
        return op(other, self.expression, **kwargs)


@dataclass
class DataPoint:
    sensor_name: str
    data: t.Any
    deployment_id: uuid.UUID
    id: t.Optional[int] = None
    collected_at: datetime.datetime = field(default_factory=datetime.datetime.now)

    @classmethod
    def from_sql_result(cls, result) -> DataPoint:
        return cls(**result._asdict())

    def _asdict(self) -> t.Dict[str, t.Any]:
        data = asdict(self)
        if data["id"] is None:
            del data["id"]
        return data

    @hybrid_property
    def collected_on_date(self):
        return self.collected_at.date()

    @collected_on_date.comparator  # type: ignore
    def collected_on_date(cls):
        return DateEqualComparator(
            fallback_expression=sqlalchemy.cast(datapoint_table.c.collected_at, DATE),
            raw_expression=datapoint_table.c.collected_at,
        )


def main() -> None:
    engine = sqlalchemy.create_engine(
        "postgresql+psycopg2://apd@localhost/apd", echo=True
    )
    sm = sessionmaker(engine)
    Session = sm()
    if False:
        metadata.create_all(engine)
    print(Session.query(DataPoint).all())
    pass


if __name__ == "__main__":
    main()
