from dataclasses import dataclass, field, asdict
import datetime
import typing as t


@dataclass
class DataPoint:
    sensor_name: str
    data: t.Dict[str, t.Any]
    id: int = None
    collected_at: datetime.datetime = field(default_factory=datetime.datetime.now)

    @classmethod
    def from_sql_result(cls, result):
        return cls(**result._asdict())

    def _asdict(self):
        data = asdict(self)
        if data["id"] is None:
            del data["id"]
        return data

