from apd.sensors.base import Sensor, T_value
from apd.sensors.exceptions import IntermittentSensorFailureError


def get_value_with_retries(sensor: Sensor[T_value], retries: int = 3) -> T_value:
    for i in range(retries):
        try:
            return sensor.value()
        except IntermittentSensorFailureError:
            if i == (retries - 1):
                # This is the last retry, reraise
                raise
            else:
                continue
    # It shouldn't be possible to get here, but it's better to
    # fall through with an appropriate exception rather than a
    # None
    raise IntermittentSensorFailureError(
        f"Could not find a value after {retries} retries"
    )
