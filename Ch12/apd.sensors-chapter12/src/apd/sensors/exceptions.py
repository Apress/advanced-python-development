import dataclasses


class APDSensorsError(Exception):
    """An exception base class for all exceptions raised by the
    sensor data collection system."""


class DataCollectionError(APDSensorsError, RuntimeError):
    """An error that represents the inability of a Sensor instance
    to retrieve a value"""


class IntermittentSensorFailureError(DataCollectionError):
    """A DataCollectionError that is expected to resolve itself
    in short order"""


class PersistentSensorFailureError(DataCollectionError):
    """A DataCollectionError that is unlikely to resolve itself
    if retried."""


@dataclasses.dataclass(frozen=True)
class UserFacingCLIError(APDSensorsError, SystemExit):
    """A fatal error for the CLI"""

    message: str
    return_code: int

    def __str__(self):
        return f"[{self.return_code}] {self.message}"
