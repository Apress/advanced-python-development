import dataclasses
import typing as t
import uuid

from ..database import DataPoint
from ..exceptions import IncompatibleTriggerError
from .base import Trigger


@dataclasses.dataclass(frozen=True)
class ValueThresholdTrigger(Trigger[bool]):
    name: str
    threshold: float
    comparator: t.Callable[[float, float], bool]
    sensor_name: str
    deployment_id: t.Optional[uuid.UUID] = dataclasses.field(default=None)

    async def match(self, datapoint: DataPoint) -> bool:
        if datapoint.sensor_name != self.sensor_name:
            return False
        elif self.deployment_id and datapoint.deployment_id != self.deployment_id:
            return False
        return True

    async def extract(self, datapoint: DataPoint) -> bool:
        if datapoint.data is None:
            raise IncompatibleTriggerError("Datapoint does not contain data")
        elif isinstance(datapoint.data, float):
            value = datapoint.data
        elif isinstance(datapoint.data, dict) and "magnitude" in datapoint.data:
            value = datapoint.data["magnitude"]
        else:
            raise IncompatibleTriggerError("Unrecognised data format")
        return self.comparator(value, self.threshold)  # type: ignore
