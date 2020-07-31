import typing as t

import pytest

from apd.sensors.base import JSONSensor
from apd.sensors.exceptions import (
    IntermittentSensorFailureError,
    PersistentSensorFailureError,
)
from apd.sensors.utils import get_value_with_retries


class FailingSensor(JSONSensor[bool]):

    title = "Sensor which fails"
    name = "FailingSensor"

    def __init__(
        self,
        n: int = 3,
        exception_type: t.Type[Exception] = IntermittentSensorFailureError,
    ):
        self.n = n
        self.exception_type = exception_type

    def value(self) -> bool:
        self.n -= 1
        if self.n:
            raise self.exception_type(f"Failing {self.n} more times")
        else:
            return True

    @classmethod
    def format(cls, value: bool) -> str:
        return "Yes" if value else "No"


class TestRetry:
    def test_default_retries(self):
        sensor = FailingSensor(3)
        value = get_value_with_retries(sensor)
        assert value is True

    def test_n_retries(self):
        sensor = FailingSensor(5)
        value = get_value_with_retries(sensor, retries=5)
        assert value is True

    def test_insufficient_retries(self):
        sensor = FailingSensor(5)
        with pytest.raises(IntermittentSensorFailureError):
            get_value_with_retries(sensor, retries=4)

    def test_permanent_failures_not_retried(self):
        sensor = FailingSensor(3, PersistentSensorFailureError)
        with pytest.raises(PersistentSensorFailureError):
            get_value_with_retries(sensor)
