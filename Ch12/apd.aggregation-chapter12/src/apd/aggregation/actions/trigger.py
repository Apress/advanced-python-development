import dataclasses
import typing as t
import uuid

from ..database import DataPoint
from ..exceptions import IncompatibleTriggerError, NoDataForTrigger
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


@dataclasses.dataclass
class ValueDifferenceTrigger(Trigger[float]):
    name: str
    sensor_name: str
    target_deployment_id: uuid.UUID
    reference_deployment_id: uuid.UUID

    def __post_init__(self):
        self.last_reference = None
        self.last_target = None

    async def match(self, datapoint: DataPoint) -> bool:
        if datapoint.sensor_name != self.sensor_name:
            return False
        elif datapoint.deployment_id in (
            self.target_deployment_id,
            self.reference_deployment_id,
        ):
            return True
        return False

    async def extract(self, datapoint: DataPoint) -> float:
        if datapoint.data is None:
            raise IncompatibleTriggerError("Datapoint does not contain data")
        elif isinstance(datapoint.data, float):
            value = datapoint.data
        elif isinstance(datapoint.data, dict) and "magnitude" in datapoint.data:
            value = datapoint.data["magnitude"]
        else:
            raise IncompatibleTriggerError("Unrecognised data format")

        if datapoint.deployment_id == self.target_deployment_id:
            self.last_target = value
        elif datapoint.deployment_id == self.reference_deployment_id:
            self.last_reference = value

        if self.last_reference is None or self.last_target is None:
            # We need to have seen both items before we can calculate a difference
            raise NoDataForTrigger("Insufficient data processed")

        return self.last_target - self.last_reference
