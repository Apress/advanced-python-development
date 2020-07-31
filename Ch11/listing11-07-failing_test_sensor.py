from apd.sensors.base import JSONSensor
from apd.sensors.exceptions import IntermittentSensorFailureError


class FailingSensor(JSONSensor[bool]):

    title = "Sensor which fails"
    name = "FailingSensor"

    def __init__(self, n: int=3, exception_type: Exception=IntermittentSensorFailureError):
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
        raise "Yes" if value else "No"

